"""
Run the Conto synchronization directly, without a task queue.

Same work as the Celery tasks, invoked as a command. This is what lets the
integration run on a plain cron job instead of requiring a worker, a beat
process and a Redis broker to be deployed.

    python manage.py sincronizar_conto                 # ventas
    python manage.py sincronizar_conto --que todo
    python manage.py sincronizar_conto --que stock --full

Exits non-zero when something failed, so a scheduler surfaces it instead of
reporting a successful run that imported nothing.
"""
from django.core.management.base import BaseCommand, CommandError

from apps.integraciones.models import ContoIntegration
from apps.integraciones.services import (
    ContoAccountInactive,
    ContoAccountMismatch,
    ContoAuthError,
    ContoError,
    ContoNotLinked,
    ContoUnavailable,
)
from apps.integraciones.sync import SalesImporter, StockSynchronizer


class Command(BaseCommand):
    help = 'Sincroniza ventas y stock desde Conto (sin Celery)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--que',
            choices=['ventas', 'stock', 'todo'],
            default='ventas',
            help='Qué sincronizar (default: ventas)'
        )
        parser.add_argument(
            '--integration-id',
            type=int,
            help='Sincronizar solo esta integración'
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Para stock: traer el catálogo completo, ignorando el cursor'
        )

    def handle(self, *args, **options):
        integrations = ContoIntegration.objects.filter(
            is_active=True,
            conto_account_id__isnull=False,
            link_verified_at__isnull=False,
        ).select_related('branch', 'center')

        if options.get('integration_id'):
            integrations = integrations.filter(pk=options['integration_id'])

        if not integrations.exists():
            self.stdout.write(self.style.WARNING(
                'No hay integraciones activas y verificadas. Nada que hacer.'
            ))
            return

        what = options['que']
        failed = []

        for integration in integrations:
            self.stdout.write(self.style.MIGRATE_HEADING(
                f'Conto — {integration.center.nombre}'
            ))

            problem = self._verify_link(integration)
            if problem:
                failed.append(problem)
                continue

            if what in ('stock', 'todo'):
                failed += self._run(
                    'Stock',
                    lambda: StockSynchronizer(integration).run(full=options['full']),
                    integration,
                )

            if what in ('ventas', 'todo'):
                failed += self._run(
                    'Ventas',
                    lambda: SalesImporter(integration).run(),
                    integration,
                )

        if failed:
            raise CommandError(
                f"{len(failed)} sincronización(es) fallaron:\n  " +
                "\n  ".join(failed)
            )

    def _verify_link(self, integration):
        """
        Confirm the token still resolves to the linked account, before syncing.

        The client already checks `cuenta_id` on every listing page, but only
        when there is data to return. An integration with no recent sales could
        stay pointed at the wrong account indefinitely. One extra request per
        run closes that gap and removes the need for a separate daily job.

        Returns a problem description, or None when everything is fine.
        """
        from apps.integraciones.services import ContoClient

        try:
            account = ContoClient(integration).get_account()
        except ContoUnavailable as exc:
            self.stdout.write(self.style.WARNING(
                f'  Vínculo: Conto no disponible ({exc})'
            ))
            return f'{integration.center.nombre}: {exc}'
        except ContoError as exc:
            self.stdout.write(self.style.ERROR(f'  Vínculo: {exc}'))
            return f'{integration.center.nombre}: {exc}'

        received = account.get('cuenta_id')
        if received != integration.conto_account_id:
            # Fail closed and stop syncing: importing here would write another
            # business's sales into this tenant.
            integration.is_active = False
            integration.save(update_fields=['is_active', 'updated_at'])
            message = (
                f'el token resuelve a la cuenta {received!r} y la integración '
                f'está vinculada a {integration.conto_account_id!r}. '
                f'Se desactivó la integración.'
            )
            self.stdout.write(self.style.ERROR(f'  Vínculo: {message}'))
            return f'{integration.center.nombre}: {message}'

        if not account.get('activa', True):
            self.stdout.write(self.style.WARNING(
                '  Vínculo: la cuenta de Conto está desactivada'
            ))
            return f'{integration.center.nombre}: cuenta de Conto desactivada'

        self.stdout.write(f'  Vínculo: OK ({account.get("nombre") or received})')
        return None

    def _run(self, label, work, integration):
        """
        Run one synchronization, reporting the outcome.

        Auth and isolation errors are reported but do not stop the other
        integrations: one revoked token should not silence everybody else.
        """
        try:
            result = work()
        except (ContoAuthError, ContoAccountMismatch,
                ContoAccountInactive, ContoNotLinked) as exc:
            self.stdout.write(self.style.ERROR(f'  {label}: {exc}'))
            return [f'{integration.center.nombre} / {label}: {exc}']
        except ContoUnavailable as exc:
            self.stdout.write(self.style.WARNING(
                f'  {label}: Conto no disponible ({exc}). '
                f'La próxima corrida recupera lo que falte.'
            ))
            return [f'{integration.center.nombre} / {label}: {exc}']
        except ContoError as exc:
            self.stdout.write(self.style.ERROR(f'  {label}: {exc}'))
            return [f'{integration.center.nombre} / {label}: {exc}']

        style = self.style.ERROR if result.errors else self.style.SUCCESS
        self.stdout.write(style(f'  {label}: {result.summary}'))

        for error in result.errors[:10]:
            self.stdout.write(self.style.ERROR(f'    - {error}'))

        # Per-voucher errors are recorded on the voucher and reprocessable, so
        # they do not make the whole run fail.
        return []

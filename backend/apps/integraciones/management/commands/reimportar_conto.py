"""
Wipe what was imported from Conto and let it be pulled again.

Needed when the imported data itself was wrong — a bug on either side, a mapping
fixed after the fact — because a plain re-run does nothing: vouchers already
marked PROCESSED are skipped by design, which is what makes the sync idempotent.

Only touches records that came from Conto. Transactions loaded by hand, Mi Caja
sales and everything else are never in scope.

    python manage.py reimportar_conto              # muestra qué haría
    python manage.py reimportar_conto --confirmar   # lo hace
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction
from django.db.models import Count, Sum

from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoIntegration, ContoSale


class Command(BaseCommand):
    help = 'Borra las ventas importadas de Conto para poder reimportarlas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--integration-id', type=int,
            help='Integración a limpiar. Por defecto, la única que exista'
        )
        parser.add_argument(
            '--confirmar', action='store_true',
            help='Ejecutar el borrado. Sin esto solo informa'
        )

    def handle(self, *args, **options):
        integration = self._get_integration(options)

        sales = ContoSale.objects.filter(integration=integration)
        transactions = Transaction.objects.filter(conto_sales__in=sales).distinct()

        total = transactions.aggregate(t=Sum('amount'))['t'] or 0
        por_estado = {
            row['status']: row['n']
            for row in sales.values('status').annotate(n=Count('id'))
        }

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'Conto — {integration.center.nombre}'
        ))
        self.stdout.write(f'  Vouchers de Conto:        {sales.count()}')
        for estado, n in sorted(por_estado.items()):
            self.stdout.write(f'    {estado:<12} {n}')
        self.stdout.write(f'  Transacciones a borrar:   {transactions.count()}')
        self.stdout.write(f'  Monto involucrado:        ${total:,.2f}')
        self.stdout.write(
            f'  Cursor de ventas:         {integration.last_sales_sync}'
        )

        # Anything financial that did NOT come from Conto must stay untouched.
        ajenas = Transaction.objects.filter(
            branch=integration.branch
        ).exclude(pk__in=transactions.values('pk')).count()
        self.stdout.write(
            f'  Transacciones que NO se tocan: {ajenas}'
        )

        if not options['confirmar']:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'Modo informativo: no se borró nada. '
                'Volvé a correr con --confirmar para ejecutarlo.'
            ))
            return

        if not sales.exists():
            self.stdout.write('')
            self.stdout.write('No hay nada importado de Conto. Nada que borrar.')
            return

        with db_transaction.atomic():
            borradas = transactions.count()
            vouchers = sales.count()
            # The M2M does not cascade, so the transactions go first and by hand.
            transactions.delete()
            sales.delete()
            integration.last_sales_sync = None
            integration.save(update_fields=['last_sales_sync', 'updated_at'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Borradas {borradas} transacciones y {vouchers} vouchers. '
            f'Cursor de ventas reseteado.'
        ))
        self.stdout.write(
            'Ahora corré "Importar ventas desde Conto" o '
            '"python manage.py sincronizar_conto --que ventas".'
        )

    def _get_integration(self, options):
        queryset = ContoIntegration.objects.select_related('branch', 'center')
        if options.get('integration_id'):
            queryset = queryset.filter(pk=options['integration_id'])

        integration = queryset.first()
        if not integration:
            raise CommandError('No hay ninguna integración cargada.')
        if queryset.count() > 1:
            raise CommandError('Hay más de una integración. Usá --integration-id.')
        return integration

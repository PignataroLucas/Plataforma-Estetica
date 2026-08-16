"""
Trade a Tienda Nube installation code for a token and store the link.

    python manage.py vincular_tiendanube --centro 1 --code abc123...

Exists because the code that Tienda Nube hands back after an install **lives
five minutes**, and doing that exchange by hand from a terminal means fighting
shell quoting against a clock. Here the environment is ours.

It is also the manual fallback for the automatic flow: the OAuth callback does
the same exchange when the merchant installs the app. If the callback is down
or the redirect URL still points at the partner panel, this command finishes
the job with the code copied from the browser.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.empleados.models import CentroEstetica
from apps.integraciones.models import TiendanubeIntegration
from apps.integraciones.tiendanube import (
    TiendanubeClient,
    TiendanubeError,
    exchange_code_for_token,
)


class Command(BaseCommand):
    help = 'Vincula un centro con su tienda de Tienda Nube a partir del código de instalación'

    def add_arguments(self, parser):
        parser.add_argument(
            '--centro',
            type=int,
            required=True,
            help='ID del centro de estética a vincular',
        )
        parser.add_argument(
            '--code',
            help='Código que devuelve Tienda Nube al instalar la app (dura 5 minutos)',
        )
        # El panel de partners ofrece un curl que hace el intercambio en el
        # navegador. Quien lo usó ya tiene el token y el código está quemado:
        # obligarlo a reinstalar para conseguir uno nuevo no aporta nada.
        parser.add_argument(
            '--token',
            help='Token ya obtenido. Alternativa a --code; requiere --store-id',
        )
        parser.add_argument(
            '--store-id',
            help='ID de la tienda (`user_id`), obligatorio junto con --token',
        )

    def handle(self, *args, **options):
        try:
            centro = CentroEstetica.objects.get(pk=options['centro'])
        except CentroEstetica.DoesNotExist:
            raise CommandError(f"No existe el centro {options['centro']}")

        self.stdout.write(f"Centro: {centro.nombre}")
        datos = self._obtener_token(options)
        store_id = str(datos['user_id'])

        # A store already linked to another center is a misconfiguration that
        # would let one tenant issue coupons on another's store. The unique
        # constraint would catch it, but not with an explanation.
        ocupada = (
            TiendanubeIntegration.objects
            .filter(store_id=store_id)
            .exclude(center=centro)
            .select_related('center')
            .first()
        )
        if ocupada:
            raise CommandError(
                f"La tienda {store_id} ya está vinculada al centro "
                f"«{ocupada.center.nombre}». Desvinculala antes de reasignarla."
            )

        integration, creada = TiendanubeIntegration.objects.update_or_create(
            center=centro,
            defaults={
                'store_id': store_id,
                'token': datos['access_token'],
                'scope': datos.get('scope', ''),
                'is_active': True,
                'installed_at': timezone.now(),
                'uninstalled_at': None,
            },
        )

        # Reading the store back is the only proof that the token actually
        # works. Without it the command reports success on a token that could
        # fail on the first coupon.
        try:
            tienda = TiendanubeClient(integration).get_store() or {}
        except TiendanubeError as exc:
            self.stdout.write(self.style.WARNING(
                f"Token guardado, pero no se pudo leer la tienda: {exc}"
            ))
        else:
            nombre = tienda.get('name')
            if isinstance(nombre, dict):
                # Tienda Nube devuelve los textos por idioma: {'es': 'Ame Demo'}
                nombre = nombre.get('es') or next(iter(nombre.values()), '')
            integration.store_name = (nombre or '')[:200]
            integration.store_url = (tienda.get('url_with_protocol') or '').rstrip('/')
            integration.save(update_fields=['store_name', 'store_url', 'updated_at'])
            self.stdout.write(f"Tienda: {integration.store_name or 's/n'}")
            self.stdout.write(f"URL: {integration.store_url or 's/d'}")

        self.stdout.write(f"Store ID: {store_id}")
        self.stdout.write(f"Permisos: {integration.scope or 's/d'}")
        self.stdout.write(self.style.SUCCESS(
            'Integración creada' if creada else 'Integración actualizada'
        ))

    def _obtener_token(self, options):
        """Del código de instalación, o directamente el token si ya se cambió."""
        code, token, store_id = options.get('code'), options.get('token'), options.get('store_id')

        if token:
            if not store_id:
                raise CommandError('Con --token hay que pasar también --store-id')
            return {'access_token': token.strip(), 'user_id': store_id.strip(), 'scope': ''}

        if not code:
            raise CommandError('Pasá --code, o --token junto con --store-id')

        try:
            return exchange_code_for_token(code.strip())
        except TiendanubeError as exc:
            raise CommandError(str(exc))

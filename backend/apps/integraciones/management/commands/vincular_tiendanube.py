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

The linking itself lives in `instalacion.py`, shared with the callback.
"""
from django.core.management.base import BaseCommand, CommandError

from apps.empleados.models import CentroEstetica
from apps.integraciones.instalacion import (
    TiendaDeOtroCentro,
    completar_datos_tienda,
    vincular,
)
from apps.integraciones.tiendanube import TiendanubeError, exchange_code_for_token


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

        try:
            integracion, creada = vincular(centro, datos)
        except TiendaDeOtroCentro as exc:
            raise CommandError(str(exc))

        error = completar_datos_tienda(integracion)
        if error:
            self.stdout.write(self.style.WARNING(
                f"Token guardado, pero no se pudo leer la tienda: {error}"
            ))
        else:
            self.stdout.write(f"Tienda: {integracion.store_name or 's/n'}")
            self.stdout.write(f"URL: {integracion.store_url or 's/d'}")

        self.stdout.write(f"Store ID: {integracion.store_id}")
        self.stdout.write(f"Permisos: {integracion.scope or 's/d'}")
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

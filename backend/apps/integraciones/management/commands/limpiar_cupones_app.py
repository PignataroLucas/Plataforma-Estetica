"""
Borrar de Tienda Nube los cupones de la app que vencieron sin usarse.

    python manage.py limpiar_cupones_app

Cada "Comprar" que no termina en compra deja un cupón vivo en la tienda del
centro. Sin esta limpieza, en unos meses hay miles (COMPRA_EN_APP_SPEC.md §6.5).

Pensado para correr por cron, con el mismo patrón que el sync de Conto. La fila
local no se borra: es la que después dice cuántas compras se empezaron y no se
terminaron.
"""
from django.core.management.base import BaseCommand

from apps.integraciones.cupones import limpiar_vencidos


class Command(BaseCommand):
    help = 'Borra de Tienda Nube los cupones de la app vencidos sin usar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limite',
            type=int,
            help='Máximo de cupones a borrar en esta corrida',
        )

    def handle(self, *args, **options):
        borrados, errores = limpiar_vencidos(limite=options.get('limite'))

        self.stdout.write(f"Cupones borrados: {borrados}")
        for error in errores:
            self.stdout.write(self.style.WARNING(error))

        if errores:
            # Salida distinta de cero para que el cron lo muestre en vez de
            # reportar una corrida exitosa que no borró nada.
            self.stderr.write(f"{len(errores)} cupones no se pudieron borrar")
            raise SystemExit(1)

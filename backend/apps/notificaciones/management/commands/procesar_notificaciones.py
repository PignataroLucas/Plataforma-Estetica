"""
Motor de las notificaciones, como comando.

**Este es el camino real en producción.** El despliegue de Railway levanta solo
Gunicorn: no hay worker ni beat de Celery corriendo, así que un ``.delay()`` se
encolaría en Redis y no lo tomaría nadie. Un servicio de cron que corre este
comando cada pocos minutos hace el mismo trabajo sin sumar dos procesos más.

Las tres etapas son independientes y se pueden correr por separado:

    python manage.py procesar_notificaciones                 # las tres
    python manage.py procesar_notificaciones --disparadores  # solo encolar
    python manage.py procesar_notificaciones --cola          # solo enviar
    python manage.py procesar_notificaciones --recibos       # solo confirmar
"""
import json

from django.core.management.base import BaseCommand

from apps.notificaciones import cola, disparadores


class Command(BaseCommand):
    help = 'Encola, envía y confirma las notificaciones push pendientes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--disparadores', action='store_true',
            help='Solo evaluar los disparadores programados (encolar).',
        )
        parser.add_argument(
            '--cola', action='store_true',
            help='Solo enviar los avisos vencidos.',
        )
        parser.add_argument(
            '--recibos', action='store_true',
            help='Solo consultar los recibos de Expo.',
        )
        parser.add_argument(
            '--limite', type=int, default=cola.LOTE_POR_CORRIDA,
            help='Máximo de avisos a enviar en esta corrida.',
        )

    def handle(self, *args, **opciones):
        # Sin flags se corren las tres etapas, que es lo que hace el cron.
        etapas = {
            'disparadores': opciones['disparadores'],
            'cola': opciones['cola'],
            'recibos': opciones['recibos'],
        }
        if not any(etapas.values()):
            etapas = dict.fromkeys(etapas, True)

        resumen = {}

        if etapas['disparadores']:
            resumen['disparadores'] = disparadores.correr_todos()

        if etapas['cola']:
            resumen['cola'] = cola.procesar_pendientes(limite=opciones['limite'])

        if etapas['recibos']:
            resumen['recibos'] = cola.procesar_recibos()

        # JSON en una línea: los logs de Railway se leen mejor así.
        self.stdout.write(json.dumps(resumen, ensure_ascii=False))

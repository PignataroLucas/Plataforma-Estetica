"""
Repara las transacciones que quedaron guardadas con la fecha del día siguiente.

Hasta este fix, el backend calculaba "hoy" con `timezone.now().date()`. `now()`
devuelve UTC, así que a partir de las 21:00 de Argentina (-03) el `.date()` ya
había pasado al día siguiente: un cobro registrado el viernes a las 21:16 se
guardaba con `date` del sábado. Lo mismo pasaba en el dashboard y en Mi Caja al
leer, por eso el error no se notaba desde adentro — la plata aparecía, pero
contada en el día equivocado.

Cómo se reconoce una fila afectada, sin tocar las fechas que el usuario eligió
a mano: en las filas rotas el `date` coincide **exactamente** con la fecha UTC
de `created_at` y **no** con la fecha local. Una transacción cargada a mano con
fecha futura no cumple las dos condiciones a la vez salvo que se haya cargado
justo en la ventana 21:00-24:00 apuntando al día siguiente, por eso el comando
lista todo antes de escribir y sólo escribe con `--aplicar`.

Sólo lectura por defecto:

    docker-compose exec backend python manage.py corregir_fechas_utc

Para escribir:

    docker-compose exec backend python manage.py corregir_fechas_utc --aplicar
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.utils import timezone

from apps.finanzas.models import Transaction


class Command(BaseCommand):
    help = 'Corrige transacciones guardadas con la fecha UTC en vez de la fecha de Argentina'

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Escribe los cambios. Sin este flag sólo muestra qué se corregiría.',
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=400,
            help='Cuántos días hacia atrás revisar (default: 400).',
        )

    def handle(self, *args, **options):
        aplicar = options['aplicar']
        desde = timezone.now() - timedelta(days=options['dias'])

        candidatas = (
            Transaction.objects
            .filter(created_at__gte=desde)
            .select_related('branch', 'registered_by')
            .order_by('created_at')
        )

        afectadas = []
        for tx in candidatas.iterator(chunk_size=500):
            if not tx.created_at:
                continue
            fecha_utc = tx.created_at.date()  # created_at es aware y se guarda en UTC
            fecha_local = timezone.localtime(tx.created_at).date()
            if fecha_utc == fecha_local:
                continue  # fuera de la ventana 21:00-24:00, imposible que sea este bug
            if tx.date == fecha_utc and tx.date != fecha_local:
                afectadas.append((tx, fecha_local))

        if not afectadas:
            self.stdout.write(self.style.SUCCESS('No hay transacciones con la fecha corrida.'))
            return

        self.stdout.write(
            self.style.WARNING(f'{len(afectadas)} transacción(es) con la fecha corrida un día:\n')
        )
        self.stdout.write(
            f"{'ID':>6}  {'GUARDADA':<11} {'CORRECTA':<11} {'CREADA (AR)':<17} "
            f"{'MONTO':>12}  DESCRIPCIÓN"
        )
        for tx, fecha_local in afectadas:
            creada = timezone.localtime(tx.created_at).strftime('%d/%m/%Y %H:%M')
            self.stdout.write(
                f'{tx.id:>6}  {tx.date.isoformat():<11} {fecha_local.isoformat():<11} '
                f'{creada:<17} {tx.amount:>12}  {tx.description[:50]}'
            )

        if not aplicar:
            self.stdout.write(
                '\n'
                + self.style.NOTICE(
                    'Modo lectura. Revisá la lista y volvé a correr con --aplicar para corregirlas.'
                )
            )
            return

        with db_transaction.atomic():
            for tx, fecha_local in afectadas:
                Transaction.objects.filter(pk=tx.pk).update(date=fecha_local)

        self.stdout.write(
            '\n' + self.style.SUCCESS(f'{len(afectadas)} transacción(es) corregidas.')
        )

"""
Tests de la lógica compartida de disponibilidad y reserva (apps.turnos.services).

La usan tanto el CRM del staff (``horarios_disponibles``) como la app del cliente,
así que se testea acá una sola vez.
"""
from datetime import time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.servicios.models import Servicio
from apps.turnos.models import Turno
from apps.turnos.services import (
    TurnoNoDisponible,
    calcular_slots,
    puede_cancelar,
    reservar_turno,
    slots_agregados,
)


class ServiciosDeTurnosTests(TestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(
            nombre='Centro', telefono='1111', email='c@centro.com'
        )
        self.sucursal = Sucursal.objects.create(
            centro_estetica=self.centro, nombre='Suc', direccion='Calle 1',
            telefono='1111', ciudad='CABA', provincia='BA',
        )
        self.ana = Usuario.objects.create_user(
            username='ana', password='x', first_name='Ana',
            centro_estetica=self.centro, sucursal=self.sucursal, intervalo_minutos=30,
        )
        self.servicio = Servicio.objects.create(
            sucursal=self.sucursal, nombre='Facial',
            duracion_minutos=60, precio=Decimal('20000'),
        )
        self.cliente = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Flor', apellido='A', telefono='11',
        )
        self.fecha = timezone.localdate() + timedelta(days=3)

    def _hora(self, hh, mm=0, fecha=None):
        return timezone.make_aware(
            timezone.datetime.combine(fecha or self.fecha, time(hh, mm))
        )

    def _turno(self, inicio, estado=Turno.Estado.CONFIRMADO, profesional=None):
        return Turno.objects.create(
            sucursal=self.sucursal, cliente=self.cliente, servicio=self.servicio,
            profesional=profesional or self.ana,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=self.servicio.duracion_minutos),
            estado=estado, monto_total=self.servicio.precio,
        )

    def test_slots_dentro_del_horario_laboral(self):
        self.ana.horario_inicio = time(9, 0)
        self.ana.horario_fin = time(13, 0)
        self.ana.save()

        slots = calcular_slots(self.ana, self.servicio, self.fecha)
        horas = [s['inicio'].strftime('%H:%M') for s in slots]

        # 9 a 13 con servicio de 60' e intervalo de 30' → el último arranca 12:00
        self.assertEqual(horas, ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00'])

    def test_slots_despues_de_un_turno_quedan_en_hora_local(self):
        """
        Regresión: al saltar un turno ocupado el cursor toma ``fecha_hora_fin``, que
        la DB devuelve en UTC. Sin convertir a hora local, todos los slots siguientes
        se formatean 3 horas adelantados en el endpoint del staff.
        """
        self._turno(self._hora(10))  # 10:00-11:00

        slots = calcular_slots(self.ana, self.servicio, self.fecha)
        posteriores = [s for s in slots if s['inicio'] >= self._hora(11)]

        self.assertTrue(posteriores)
        self.assertEqual(posteriores[0]['inicio'].strftime('%H:%M'), '11:00')
        for slot in slots:
            self.assertEqual(
                slot['inicio'].strftime('%H:%M'),
                timezone.localtime(slot['inicio']).strftime('%H:%M'),
            )

    def test_turno_cancelado_no_bloquea_el_horario(self):
        self._turno(self._hora(10), estado=Turno.Estado.CANCELADO)

        horas = [s['inicio'].strftime('%H:%M') for s in calcular_slots(self.ana, self.servicio, self.fecha)]
        self.assertIn('10:00', horas)

    def test_no_antes_de_descarta_slots_pasados(self):
        hoy = timezone.localdate()
        corte = timezone.localtime(timezone.now()) + timedelta(hours=2)

        slots = calcular_slots(self.ana, self.servicio, hoy, no_antes_de=corte)
        self.assertTrue(all(s['inicio'] >= corte for s in slots))

    def test_slots_agregados_no_duplica_horarios_entre_profesionales(self):
        beto = Usuario.objects.create_user(
            username='beto', password='x', first_name='Beto',
            centro_estetica=self.centro, sucursal=self.sucursal, intervalo_minutos=30,
        )
        self._turno(self._hora(10))  # Ana ocupada 10:00-11:00

        agregados = slots_agregados(self.servicio, self.fecha)
        por_hora = {s['inicio']: s['profesional'] for s in agregados}

        self.assertEqual(len(por_hora), len(agregados))
        # El horario que Ana tiene ocupado lo cubre Beto
        self.assertEqual(por_hora[self._hora(10)], beto)
        # Ana es la primera por id, así que toma los horarios libres de ambos
        self.assertEqual(por_hora[self._hora(9)], self.ana)

    def test_reservar_asigna_al_primer_profesional_libre(self):
        beto = Usuario.objects.create_user(
            username='beto', password='x', first_name='Beto',
            centro_estetica=self.centro, sucursal=self.sucursal, intervalo_minutos=30,
        )
        self._turno(self._hora(10))  # Ana ocupada

        turno = reservar_turno(
            cliente=self.cliente, servicio=self.servicio, inicio=self._hora(10)
        )
        self.assertEqual(turno.profesional, beto)

    def test_reservar_rechaza_solapamiento(self):
        self._turno(self._hora(10))

        with self.assertRaises(TurnoNoDisponible):
            reservar_turno(
                cliente=self.cliente, servicio=self.servicio,
                inicio=self._hora(10, 30),
            )

    def test_reservar_rechaza_fuera_de_la_jornada(self):
        self.ana.horario_inicio = time(9, 0)
        self.ana.horario_fin = time(13, 0)
        self.ana.save()

        with self.assertRaises(TurnoNoDisponible):
            reservar_turno(
                cliente=self.cliente, servicio=self.servicio, inicio=self._hora(20)
            )

    def test_puede_cancelar_respeta_la_antelacion_minima(self):
        lejano = self._turno(timezone.now() + timedelta(days=2))
        cercano = self._turno(timezone.now() + timedelta(hours=3))
        completado = self._turno(
            timezone.now() + timedelta(days=4), estado=Turno.Estado.COMPLETADO
        )

        self.assertTrue(puede_cancelar(lejano))
        self.assertFalse(puede_cancelar(cercano))
        self.assertFalse(puede_cancelar(completado))

"""
Tests de los disparadores programados y de las señales del turno.

Lo que se prueba acá es que el cron puede correr las veces que quiera sin
duplicar nada, y que un turno que cambia no deja recordatorios viejos apuntando a
una hora que ya no existe.
"""
from datetime import timedelta

from django.test import override_settings
from django.utils import timezone

from apps.clientes.models import Cliente, RutinaCuidado, RutinaItem
from apps.notificaciones import disparadores, eventos
from apps.notificaciones.models import Aviso
from apps.turnos.models import Turno

from .base import NotificacionesTestBase


class RecordatoriosDeTurnoTests(NotificacionesTestBase):

    def test_encola_los_dos_recordatorios_en_su_momento_exacto(self):
        turno = self.crear_turno(dentro_de=timedelta(days=2))

        disparadores.programar_recordatorios_de_turnos()

        de_24 = Aviso.objects.get(evento=eventos.TURNO_RECORDATORIO_24H)
        de_2 = Aviso.objects.get(evento=eventos.TURNO_RECORDATORIO_2H)
        self.assertEqual(de_24.programado_para, turno.fecha_hora_inicio - timedelta(hours=24))
        self.assertEqual(de_2.programado_para, turno.fecha_hora_inicio - timedelta(hours=2))

    def test_correr_el_barrido_muchas_veces_no_duplica(self):
        self.crear_turno(dentro_de=timedelta(days=2))

        for _ in range(5):
            disparadores.programar_recordatorios_de_turnos()

        self.assertEqual(Aviso.objects.count(), 2)

    def test_un_turno_sobre_la_hora_no_dispara_el_de_24h(self):
        """Reservar para dentro de 5 horas no puede mandar un 'mañana tenés turno'."""
        self.crear_turno(dentro_de=timedelta(hours=5))

        disparadores.programar_recordatorios_de_turnos()

        self.assertFalse(Aviso.objects.filter(evento=eventos.TURNO_RECORDATORIO_24H).exists())
        self.assertTrue(Aviso.objects.filter(evento=eventos.TURNO_RECORDATORIO_2H).exists())

    def test_un_turno_cancelado_no_recibe_recordatorios(self):
        self.crear_turno(dentro_de=timedelta(days=2), estado=Turno.Estado.CANCELADO)

        disparadores.programar_recordatorios_de_turnos()

        self.assertFalse(
            Aviso.objects.filter(evento__startswith='turno_recordatorio').exists()
        )

    def test_una_clienta_sin_cuenta_de_app_no_genera_avisos(self):
        sin_cuenta = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Luz', apellido='Vera',
            telefono='1199887766',
        )
        inicio = timezone.now() + timedelta(days=2)
        Turno.objects.create(
            sucursal=self.sucursal, cliente=sin_cuenta, servicio=self.servicio,
            profesional=self.profesional, fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=60),
            estado=Turno.Estado.CONFIRMADO, monto_total=self.servicio.precio,
        )

        disparadores.programar_recordatorios_de_turnos()

        self.assertEqual(Aviso.objects.filter(evento__startswith='turno_record').count(), 0)

    def test_un_turno_muy_lejano_todavia_no_se_programa(self):
        self.crear_turno(dentro_de=timedelta(days=disparadores.DIAS_DE_PROGRAMACION + 2))

        disparadores.programar_recordatorios_de_turnos()

        self.assertEqual(Aviso.objects.count(), 0)


class SenalesDeTurnoTests(NotificacionesTestBase):

    def test_confirmar_el_turno_encola_el_aviso(self):
        turno = self.crear_turno(estado=Turno.Estado.PENDIENTE)
        self.assertFalse(Aviso.objects.filter(evento=eventos.TURNO_CONFIRMADO).exists())

        turno.estado = Turno.Estado.CONFIRMADO
        turno.save()

        aviso = Aviso.objects.get(evento=eventos.TURNO_CONFIRMADO)
        self.assertEqual(aviso.datos['turnoId'], turno.id)

    def test_confirmar_dos_veces_no_avisa_dos_veces(self):
        turno = self.crear_turno(estado=Turno.Estado.PENDIENTE)
        turno.estado = Turno.Estado.CONFIRMADO
        turno.save()
        turno.notas = 'algo más'
        turno.save()

        self.assertEqual(Aviso.objects.filter(evento=eventos.TURNO_CONFIRMADO).count(), 1)

    def test_cancelar_avisa_y_baja_los_recordatorios_pendientes(self):
        turno = self.crear_turno(dentro_de=timedelta(days=2))
        disparadores.programar_recordatorios_de_turnos()
        self.assertEqual(Aviso.objects.filter(evento__startswith='turno_record').count(), 2)

        turno.estado = Turno.Estado.CANCELADO
        turno.save()

        self.assertEqual(Aviso.objects.filter(evento__startswith='turno_record').count(), 0)
        self.assertTrue(Aviso.objects.filter(evento=eventos.TURNO_CANCELADO).exists())

    def test_mover_el_turno_de_hora_rehace_los_recordatorios(self):
        turno = self.crear_turno(dentro_de=timedelta(days=2))
        disparadores.programar_recordatorios_de_turnos()
        original = Aviso.objects.get(evento=eventos.TURNO_RECORDATORIO_24H).programado_para

        turno.fecha_hora_inicio = turno.fecha_hora_inicio + timedelta(hours=3)
        turno.fecha_hora_fin = turno.fecha_hora_fin + timedelta(hours=3)
        turno.save()
        disparadores.programar_recordatorios_de_turnos()

        nuevo = Aviso.objects.get(evento=eventos.TURNO_RECORDATORIO_24H)
        self.assertEqual(nuevo.programado_para, original + timedelta(hours=3))
        # Y el texto también se rehízo con la hora nueva.
        hora_nueva = timezone.localtime(turno.fecha_hora_inicio).strftime('%H:%M')
        self.assertIn(hora_nueva, nuevo.cuerpo)


class CumpleanosTests(NotificacionesTestBase):

    def test_saluda_a_quien_cumple_hoy(self):
        hoy = timezone.localdate()
        self.cliente.fecha_nacimiento = hoy.replace(year=1990)
        self.cliente.save()

        disparadores.saludar_cumpleanos()

        aviso = Aviso.objects.get(evento=eventos.CUMPLEANOS)
        self.assertIn('Sofía', aviso.titulo)

    def test_no_saluda_dos_veces_el_mismo_año(self):
        hoy = timezone.localdate()
        self.cliente.fecha_nacimiento = hoy.replace(year=1990)
        self.cliente.save()

        for _ in range(4):
            disparadores.saludar_cumpleanos()

        self.assertEqual(Aviso.objects.filter(evento=eventos.CUMPLEANOS).count(), 1)

    def test_no_saluda_a_quien_no_cumple_hoy(self):
        self.cliente.fecha_nacimiento = timezone.localdate() - timedelta(days=40)
        self.cliente.save()

        disparadores.saludar_cumpleanos()

        self.assertEqual(Aviso.objects.count(), 0)


class RutinaTests(NotificacionesTestBase):

    def _rutina_con_pasos(self):
        rutina = RutinaCuidado.objects.create(cliente=self.cliente, activa=True)
        RutinaItem.objects.create(
            rutina=rutina, momento=RutinaItem.Momento.NOCTURNA, orden=1, paso='Limpieza'
        )
        return rutina

    def test_apagado_por_defecto(self):
        self._rutina_con_pasos()

        resumen = disparadores.recordar_rutina()

        self.assertTrue(resumen['apagado'])
        self.assertEqual(Aviso.objects.count(), 0)

    @override_settings(NOTIFICACIONES_RUTINA_DIARIA=True)
    def test_encendido_encola_uno_por_dia(self):
        self._rutina_con_pasos()

        disparadores.recordar_rutina()
        disparadores.recordar_rutina()

        self.assertEqual(Aviso.objects.filter(evento=eventos.RUTINA_RECORDATORIO).count(), 1)

    @override_settings(NOTIFICACIONES_RUTINA_DIARIA=True)
    def test_una_rutina_sin_pasos_nocturnos_no_recuerda_nada(self):
        rutina = RutinaCuidado.objects.create(cliente=self.cliente, activa=True)
        RutinaItem.objects.create(
            rutina=rutina, momento=RutinaItem.Momento.DIURNA, orden=1, paso='Protector'
        )

        disparadores.recordar_rutina()

        self.assertEqual(Aviso.objects.count(), 0)


class CorrerTodosTests(NotificacionesTestBase):

    def test_un_disparador_roto_no_frena_a_los_demas(self):
        self.crear_turno(dentro_de=timedelta(days=2))

        def explota(ahora=None):
            raise RuntimeError('boom')

        original = disparadores.DISPARADORES
        disparadores.DISPARADORES = (explota, disparadores.programar_recordatorios_de_turnos)
        self.addCleanup(lambda: setattr(disparadores, 'DISPARADORES', original))

        resumen = disparadores.correr_todos()

        self.assertTrue(resumen['explota_error'])
        self.assertEqual(resumen['recordatorios_encolados'], 2)

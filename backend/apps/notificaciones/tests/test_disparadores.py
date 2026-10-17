"""
Tests de los disparadores programados y de las señales del turno.

Lo que se prueba acá es que el cron puede correr las veces que quiera sin
duplicar nada, y que un turno que cambia no deja recordatorios viejos apuntando a
una hora que ya no existe.
"""
from datetime import datetime, timedelta

from django.test import override_settings
from django.utils import timezone

from apps.clientes import rutina_diaria
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


def _local(*args):
    """Un instante en la hora del centro."""
    return timezone.make_aware(datetime(*args))


# Viernes 16 de octubre de 2026, antes de las 9.
VIERNES_TEMPRANO = _local(2026, 10, 16, 7, 0)
VIERNES = VIERNES_TEMPRANO.date()


class RutinaTests(NotificacionesTestBase):

    def _rutina(self, *pasos):
        rutina = RutinaCuidado.objects.create(cliente=self.cliente, activa=True)
        items = []
        for orden, (momento, paso, dias) in enumerate(pasos, start=1):
            items.append(RutinaItem.objects.create(
                rutina=rutina, momento=momento, orden=orden, paso=paso, dias=dias,
            ))
        return rutina, items

    def _avisos(self):
        return Aviso.objects.filter(evento=eventos.RUTINA_RECORDATORIO).order_by('programado_para')

    @override_settings(NOTIFICACIONES_RUTINA_DIARIA=False)
    def test_el_interruptor_los_apaga(self):
        self._rutina((RutinaItem.Momento.NOCTURNA, 'Limpieza', []))

        resumen = disparadores.recordar_rutina(VIERNES_TEMPRANO)

        self.assertTrue(resumen['apagado'])
        self.assertEqual(Aviso.objects.count(), 0)

    def test_encola_manana_y_noche_a_su_hora_una_sola_vez(self):
        self._rutina(
            (RutinaItem.Momento.DIURNA, 'Protector', []),
            (RutinaItem.Momento.NOCTURNA, 'Limpieza', []),
        )

        disparadores.recordar_rutina(VIERNES_TEMPRANO)
        disparadores.recordar_rutina(VIERNES_TEMPRANO + timedelta(minutes=15))

        manana, noche = self._avisos()
        self.assertEqual(manana.programado_para, _local(2026, 10, 16, 9, 0))
        self.assertEqual(manana.titulo, 'Tu rutina de la mañana')
        self.assertEqual(noche.programado_para, _local(2026, 10, 16, 21, 0))
        self.assertEqual(noche.titulo, 'Tu rutina de la noche')

    def test_un_momento_sin_pasos_no_recuerda_nada(self):
        self._rutina((RutinaItem.Momento.DIURNA, 'Protector', []))

        disparadores.recordar_rutina(VIERNES_TEMPRANO)

        self.assertEqual([a.titulo for a in self._avisos()], ['Tu rutina de la mañana'])

    def test_un_paso_que_no_toca_hoy_no_cuenta(self):
        # Martes (1) y jueves (3): el viernes no hay nada a la noche.
        self._rutina((RutinaItem.Momento.NOCTURNA, 'Exfoliante', [1, 3]))

        disparadores.recordar_rutina(VIERNES_TEMPRANO)

        self.assertEqual(Aviso.objects.count(), 0)

    def test_el_texto_nombra_lo_que_no_va_todos_los_dias(self):
        self._rutina(
            (RutinaItem.Momento.NOCTURNA, 'Doble limpieza', []),
            (RutinaItem.Momento.NOCTURNA, 'Exfoliante enzimático', [1, 4]),
            (RutinaItem.Momento.NOCTURNA, 'Crema reparadora', []),
        )

        disparadores.recordar_rutina(VIERNES_TEMPRANO)

        self.assertEqual(self._avisos().get().cuerpo, 'Hoy toca exfoliante enzimático. Son 3 pasos.')

    def test_con_pocos_pasos_los_lista(self):
        self._rutina(
            (RutinaItem.Momento.DIURNA, 'Limpieza', []),
            (RutinaItem.Momento.DIURNA, 'Sérum', []),
            (RutinaItem.Momento.DIURNA, 'Protector', []),
        )

        disparadores.recordar_rutina(VIERNES_TEMPRANO)

        self.assertEqual(self._avisos().get().cuerpo, 'Limpieza, sérum y protector. Son unos minutos.')

    def test_si_ya_la_cumplio_no_se_encola(self):
        rutina, (paso,) = self._rutina((RutinaItem.Momento.DIURNA, 'Protector', []))
        rutina_diaria.marcar_paso(rutina, paso, True, fecha=VIERNES)

        disparadores.recordar_rutina(VIERNES_TEMPRANO)

        self.assertEqual(Aviso.objects.count(), 0)

    def test_cumplirla_descarta_el_aviso_que_estaba_esperando(self):
        rutina, (paso,) = self._rutina((RutinaItem.Momento.NOCTURNA, 'Limpieza', []))
        disparadores.recordar_rutina(VIERNES_TEMPRANO)
        self.assertEqual(self._avisos().count(), 1)

        rutina_diaria.marcar_paso(rutina, paso, True, fecha=VIERNES)
        self.assertEqual(self._avisos().count(), 0)

        # Si la destilda, el barrido siguiente lo vuelve a encolar.
        rutina_diaria.marcar_paso(rutina, paso, False, fecha=VIERNES)
        disparadores.recordar_rutina(VIERNES_TEMPRANO + timedelta(minutes=15))
        self.assertEqual(self._avisos().count(), 1)

    def test_con_mucho_atraso_el_de_la_manana_se_pierde(self):
        self._rutina(
            (RutinaItem.Momento.DIURNA, 'Protector', []),
            (RutinaItem.Momento.NOCTURNA, 'Limpieza', []),
        )

        disparadores.recordar_rutina(_local(2026, 10, 16, 15, 0))

        self.assertEqual([a.titulo for a in self._avisos()], ['Tu rutina de la noche'])

    def test_con_dos_rutinas_activas_manda_la_mas_nueva(self):
        vieja, _ = self._rutina((RutinaItem.Momento.NOCTURNA, 'Vieja', []))
        nueva, _ = self._rutina((RutinaItem.Momento.NOCTURNA, 'Nueva', []))
        RutinaCuidado.objects.filter(id=vieja.id).update(creado_en=timezone.now() - timedelta(days=30))

        disparadores.recordar_rutina(VIERNES_TEMPRANO)

        aviso = self._avisos().get()
        self.assertEqual(aviso.cuerpo, 'Nueva. Es un solo paso.')
        self.assertIn(f'rutina:{nueva.id}:', aviso.clave)

    def test_la_prueba_sale_aunque_no_sea_la_hora(self):
        rutina, _ = self._rutina((RutinaItem.Momento.NOCTURNA, 'Limpieza', []))

        avisos = disparadores.enviar_recordatorio_de_prueba(rutina, RutinaItem.Momento.NOCTURNA)
        otra = disparadores.enviar_recordatorio_de_prueba(rutina, RutinaItem.Momento.NOCTURNA)

        self.assertEqual(len(avisos) + len(otra), 2)
        self.assertLessEqual(avisos[0].programado_para, timezone.now())


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

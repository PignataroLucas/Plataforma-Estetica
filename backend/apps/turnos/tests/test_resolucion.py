"""
Tests de la resolución de un pedido: aceptarlo, rechazarlo y que venza.

Lo que se cuida acá, en orden de cuánto duele si se rompe:

1. **Que un pedido se resuelva una sola vez.** Dos personas del centro abriendo
   el mismo pedido, o alguien que acepta justo cuando el barrido lo estaba
   venciendo, no pueden dejar dos resoluciones ni dos avisos a la clienta.
2. **Que rechazar libere el horario.** `RECHAZADO` no ocupa agenda; si ocupara,
   un pedido rechazado dejaría el slot muerto para siempre.
3. **Que la clienta se entere**, y con el aviso correcto: el de rechazo lleva a
   elegir otro horario, no a una lista donde su turno ya no está.
4. **Que el vencimiento distinga** "dijimos que no" de "nadie lo miró".
"""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Cliente, UsuarioCliente, VinculacionCliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.notificaciones import eventos
from apps.notificaciones.models import Aviso
from apps.servicios.models import Servicio
from apps.turnos.models import Turno
from apps.turnos.services import (
    ESTADOS_QUE_OCUPAN,
    PedidoYaResuelto,
    confirmar_turno,
    rechazar_turno,
    vencer_pedidos,
)


class ResolucionTestBase(TestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(
            nombre='AME', telefono='1', email='ame@test.local'
        )
        self.sucursal = Sucursal.objects.create(
            centro_estetica=self.centro, nombre='Banfield', direccion='Calle 1',
            telefono='1', ciudad='Banfield', provincia='BA',
        )
        self.duenia = Usuario.objects.create_user(
            username='duenia', password='x', first_name='Ana',
            centro_estetica=self.centro, sucursal=self.sucursal,
        )
        self.servicio = Servicio.objects.create(
            sucursal=self.sucursal, nombre='Limpieza facial',
            duracion_minutos=60, precio=Decimal('20000'),
        )
        self.cliente = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Sofía', apellido='Paz',
            telefono='11', email='sofi@mail.com',
        )
        # Con cuenta de app: sin ella no hay a quién avisarle y los tests de
        # aviso no probarían nada.
        usuario = UsuarioCliente.objects.create_user(
            email='sofi@mail.com', password='Secreta123!'
        )
        VinculacionCliente.objects.create(
            usuario_cliente=usuario, cliente=self.cliente,
            metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
        )

    def pedido(self, *, vence_en=None, dentro_de=timedelta(days=3)):
        inicio = timezone.now() + dentro_de
        return Turno.objects.create(
            sucursal=self.sucursal, cliente=self.cliente, servicio=self.servicio,
            profesional=self.duenia,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=60),
            estado=Turno.Estado.PENDIENTE,
            origen=Turno.Origen.APP,
            vence_en=vence_en if vence_en is not None else timezone.now() + timedelta(hours=3),
            monto_total=self.servicio.precio,
        )


class TestConfirmar(ResolucionTestBase):

    def test_queda_confirmado_y_con_auditoria(self):
        turno = confirmar_turno(self.pedido(), usuario=self.duenia)

        self.assertEqual(turno.estado, Turno.Estado.CONFIRMADO)
        self.assertEqual(turno.resuelto_por, self.duenia)
        self.assertIsNotNone(turno.resuelto_en)

    def test_le_avisa_a_la_clienta(self):
        confirmar_turno(self.pedido(), usuario=self.duenia)

        self.assertTrue(
            Aviso.objects.filter(evento=eventos.TURNO_CONFIRMADO).exists()
        )

    def test_no_se_puede_confirmar_dos_veces(self):
        """
        La carrera real: dos personas del centro con el mismo pedido abierto.
        Sin esto, la segunda dispararía un aviso duplicado a la clienta.
        """
        turno = self.pedido()
        confirmar_turno(turno, usuario=self.duenia)

        with self.assertRaises(PedidoYaResuelto):
            confirmar_turno(turno, usuario=self.duenia)


class TestRechazar(ResolucionTestBase):

    def test_queda_rechazado_con_motivo(self):
        turno = rechazar_turno(
            self.pedido(),
            motivo=Turno.MotivoRechazo.SIN_DISPONIBILIDAD,
            usuario=self.duenia,
            detalle='Ese día tengo la máquina ocupada',
        )

        self.assertEqual(turno.estado, Turno.Estado.RECHAZADO)
        self.assertEqual(turno.motivo_rechazo, Turno.MotivoRechazo.SIN_DISPONIBILIDAD)
        self.assertEqual(turno.detalle_rechazo, 'Ese día tengo la máquina ocupada')
        self.assertEqual(turno.resuelto_por, self.duenia)

    def test_sin_motivo_no_se_puede_rechazar(self):
        """
        El motivo es lo que hace que el reporte de rechazos sirva. Si se pudiera
        rechazar sin él, el campo se llenaría de vacíos y la métrica moriría.
        """
        with self.assertRaises(ValueError):
            rechazar_turno(self.pedido(), motivo='', usuario=self.duenia)

    def test_libera_el_horario(self):
        """Si `RECHAZADO` ocupara agenda, el slot quedaría muerto para siempre."""
        self.assertNotIn(Turno.Estado.RECHAZADO, ESTADOS_QUE_OCUPAN)

        turno = rechazar_turno(
            self.pedido(), motivo=Turno.MotivoRechazo.SIN_DISPONIBILIDAD,
            usuario=self.duenia,
        )
        ocupados = Turno.objects.filter(
            profesional=self.duenia, estado__in=ESTADOS_QUE_OCUPAN,
            fecha_hora_inicio=turno.fecha_hora_inicio,
        )
        self.assertFalse(ocupados.exists())

    def test_le_avisa_a_la_clienta_con_el_evento_propio(self):
        """
        No reusa el de cancelación: el texto y el destino son otros. El de
        rechazo lleva a elegir otro horario.
        """
        rechazar_turno(
            self.pedido(), motivo=Turno.MotivoRechazo.SIN_DISPONIBILIDAD,
            usuario=self.duenia,
        )

        aviso = Aviso.objects.get(evento=eventos.TURNO_RECHAZADO)
        self.assertEqual(aviso.datos.get('ruta'), '/(tabs)/reservar')
        self.assertFalse(
            Aviso.objects.filter(evento=eventos.TURNO_CANCELADO).exists()
        )

    def test_el_motivo_no_viaja_a_la_clienta(self):
        """
        «No hay disponibilidad» es muy distinto de leer «tiene una deuda». El
        motivo queda en el CRM para las métricas.
        """
        rechazar_turno(
            self.pedido(), motivo=Turno.MotivoRechazo.DEUDA_PENDIENTE,
            usuario=self.duenia, detalle='Debe la sesión de marzo',
        )

        aviso = Aviso.objects.get(evento=eventos.TURNO_RECHAZADO)
        texto = f'{aviso.titulo} {aviso.cuerpo} {aviso.datos}'
        self.assertNotIn('deuda', texto.lower())
        self.assertNotIn('marzo', texto.lower())

    def test_el_aviso_es_transaccional(self):
        """Apagar los recordatorios no puede apagar «tu turno no va»."""
        self.assertTrue(eventos.obtener(eventos.TURNO_RECHAZADO).transaccional)


class TestDespachoInmediato(ResolucionTestBase):
    """
    Cuando alguien del centro resuelve un pedido hay una clienta esperando una
    respuesta, así que el push no puede quedarse hasta cinco minutos en la cola.

    El outbox sigue siendo la garantía: esto es un intento que, si falla, no
    cambia nada — el barrido lo levanta igual.
    """

    def test_confirmar_intenta_mandar_en_el_acto(self):
        with patch('apps.notificaciones.cola.despachar_ahora') as despachar:
            with self.captureOnCommitCallbacks(execute=True):
                confirmar_turno(self.pedido(), usuario=self.duenia)

        despachar.assert_called_once()

    def test_rechazar_intenta_mandar_en_el_acto(self):
        with patch('apps.notificaciones.cola.despachar_ahora') as despachar:
            with self.captureOnCommitCallbacks(execute=True):
                rechazar_turno(
                    self.pedido(), motivo=Turno.MotivoRechazo.SIN_DISPONIBILIDAD,
                    usuario=self.duenia,
                )

        despachar.assert_called_once()

    def test_si_el_envio_inmediato_falla_el_turno_queda_confirmado_igual(self):
        """
        Que Expo esté caído no puede hacer fallar el clic de quien confirma. El
        aviso queda pendiente y sale en la corrida siguiente.
        """
        turno = self.pedido()

        with patch('apps.notificaciones.cola.procesar_pendientes',
                   side_effect=RuntimeError('Expo caído')):
            with self.captureOnCommitCallbacks(execute=True):
                confirmar_turno(turno, usuario=self.duenia)

        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.CONFIRMADO)
        # El aviso sigue en la cola, esperando al barrido.
        self.assertTrue(
            Aviso.objects.filter(
                evento=eventos.TURNO_CONFIRMADO, estado=Aviso.Estado.PENDIENTE
            ).exists()
        )

    def test_un_recordatorio_no_dispara_envio_inmediato(self):
        """
        Solo las resoluciones. Un recordatorio de 24 horas está programado para
        su hora: sacarlo antes no sirve de nada y multiplicaría las corridas.
        """
        from apps.notificaciones import despacho

        with patch('apps.notificaciones.cola.despachar_ahora') as despachar:
            with self.captureOnCommitCallbacks(execute=True):
                despacho.crear_aviso_para_cliente(
                    evento=eventos.TURNO_RECORDATORIO_24H,
                    cliente=self.cliente,
                    contexto={'servicio': 'Facial', 'fecha': 'hoy', 'hora': '10:00',
                              'centro': 'AME'},
                )

        despachar.assert_not_called()


class TestVencimiento(ResolucionTestBase):

    def test_vence_los_que_se_pasaron_de_plazo(self):
        turno = self.pedido(vence_en=timezone.now() - timedelta(minutes=1))

        resumen = vencer_pedidos()

        turno.refresh_from_db()
        self.assertEqual(resumen['pedidos_vencidos'], 1)
        self.assertEqual(turno.estado, Turno.Estado.RECHAZADO)
        self.assertEqual(turno.motivo_rechazo, Turno.MotivoRechazo.VENCIDO)

    def test_un_vencido_no_lo_cerro_nadie(self):
        """
        `resuelto_por` nulo es lo que después distingue «dijimos que no» de
        «nadie lo miró», que son dos problemas con dos soluciones distintas.
        """
        turno = self.pedido(vence_en=timezone.now() - timedelta(minutes=1))

        vencer_pedidos()

        turno.refresh_from_db()
        self.assertIsNone(turno.resuelto_por)

    def test_no_toca_los_que_todavia_tienen_plazo(self):
        turno = self.pedido(vence_en=timezone.now() + timedelta(hours=1))

        resumen = vencer_pedidos()

        turno.refresh_from_db()
        self.assertEqual(resumen['pedidos_vencidos'], 0)
        self.assertEqual(turno.estado, Turno.Estado.PENDIENTE)

    def test_no_toca_los_que_no_vencen(self):
        """Los cargados en el CRM no tienen plazo: `vence_en` es nulo."""
        turno = self.pedido(vence_en=None)
        turno.vence_en = None
        turno.save(update_fields=['vence_en'])

        vencer_pedidos()

        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.PENDIENTE)

    def test_le_avisa_a_la_clienta(self):
        self.pedido(vence_en=timezone.now() - timedelta(minutes=1))

        vencer_pedidos()

        self.assertTrue(
            Aviso.objects.filter(evento=eventos.TURNO_RECHAZADO).exists()
        )

    def test_uno_que_ya_fue_resuelto_no_cuenta_como_vencido(self):
        """
        Alguien lo aceptó entre el filtro y el lock. No es un error: es la
        carrera que el lock está ahí para resolver.
        """
        turno = self.pedido(vence_en=timezone.now() - timedelta(minutes=1))
        confirmar_turno(turno, usuario=self.duenia)

        resumen = vencer_pedidos()

        self.assertEqual(resumen['pedidos_vencidos'], 0)
        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.CONFIRMADO)

    def test_esta_enganchado_al_barrido(self):
        """
        Si se cae de `DISPARADORES`, los pedidos no vencen nunca y los horarios
        quedan bloqueados — sin ningún error que lo delate.
        """
        from apps.notificaciones.disparadores import correr_todos

        self.pedido(vence_en=timezone.now() - timedelta(minutes=1))

        resumen = correr_todos()

        self.assertEqual(resumen['pedidos_vencidos'], 1)

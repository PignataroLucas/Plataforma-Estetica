"""Fixtures compartidas por los tests de notificaciones."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Cliente, UsuarioCliente, VinculacionCliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.notificaciones.canales import Resultado
from apps.notificaciones.models import DispositivoPush
from apps.servicios.models import Servicio
from apps.turnos.models import Turno


class CanalFalso:
    """
    Doble del canal de Expo.

    Registra lo que se le pidió mandar y devuelve lo que se le configure. Los
    tests no salen a la red: lo que se prueba acá es la tubería, no la API de
    Expo.
    """

    def __init__(self):
        self.enviados = []
        self.recibos_pedidos = []
        self.respuesta = None      # callable(mensaje, indice) -> Resultado
        self.recibos = {}

    def enviar(self, mensajes):
        self.enviados.extend(mensajes)
        if self.respuesta is None:
            return [
                Resultado(destino=m.destino, ok=True, ticket_id=f'ticket-{i}')
                for i, m in enumerate(mensajes)
            ]
        return [self.respuesta(m, i) for i, m in enumerate(mensajes)]

    def consultar_recibos(self, ticket_ids):
        self.recibos_pedidos.extend(ticket_ids)
        return {t: self.recibos[t] for t in ticket_ids if t in self.recibos}


class NotificacionesTestBase(TestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(
            nombre='Centro AME', telefono='1111', email='centro@ame.com'
        )
        self.sucursal = Sucursal.objects.create(
            centro_estetica=self.centro, nombre='Sucursal',
            direccion='Calle 1', telefono='1111', ciudad='CABA', provincia='BA',
        )
        self.profesional = Usuario.objects.create_user(
            username='ana', password='x', first_name='Ana', last_name='Gómez',
            centro_estetica=self.centro, sucursal=self.sucursal,
            rol=Usuario.Rol.EMPLEADO, intervalo_minutos=30,
        )
        self.servicio = Servicio.objects.create(
            sucursal=self.sucursal, nombre='Limpieza facial',
            duracion_minutos=60, precio=Decimal('20000'),
            reservable_por_cliente=True,
        )
        self.cliente = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Sofía', apellido='Paz',
            telefono='1155667788', email='sofi@mail.com',
        )
        self.usuario = UsuarioCliente.objects.create_user(
            email='sofi@mail.com', password='Secreta123!'
        )
        VinculacionCliente.objects.create(
            usuario_cliente=self.usuario, cliente=self.cliente,
            metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
        )

    def crear_dispositivo(self, usuario=None, token='ExponentPushToken[aaa]'):
        return DispositivoPush.objects.create(
            usuario_cliente=usuario or self.usuario,
            token=token,
            plataforma=DispositivoPush.Plataforma.ANDROID,
        )

    def crear_turno(self, *, dentro_de=timedelta(days=1), estado=Turno.Estado.PENDIENTE):
        inicio = timezone.now() + dentro_de
        return Turno.objects.create(
            sucursal=self.sucursal,
            cliente=self.cliente,
            servicio=self.servicio,
            profesional=self.profesional,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=60),
            estado=estado,
            monto_total=self.servicio.precio,
        )

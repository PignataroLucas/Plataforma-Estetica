"""
Baja de la cuenta de la app desde la propia app (exigencia de Google Play).

Lo que se cuida es la frontera entre dos cosas que conviven en la misma persona:
la **cuenta de la app**, que es de la clienta y se borra entera, y la **ficha
del CRM**, que es del centro y no se toca (ver ``apps/clientes/cuenta_app.py``).

Un error de un lado deja datos que la clienta pidió borrar. Uno del otro le
borra al centro el historial de una clienta que sigue atendiendo. Los dos son
silenciosos.
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.client_api.tokens import tokens_para_usuario_cliente
from apps.clientes.models import (
    Cliente,
    CodigoInvitacion,
    CodigoRecuperacion,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.empleados.models import CentroEstetica
from apps.notificaciones.models import Aviso, DispositivoPush, PreferenciaNotificacion

CLAVE = 'ClaveSegura123'


@pytest.fixture(autouse=True)
def sin_throttle():
    """
    Apaga el límite de la baja, que comparte scope con la recuperación de clave.

    Se toca el atributo de clase y no los settings: DRF fija `THROTTLE_RATES` al
    importar el módulo. Se restaura al terminar para no filtrarles el cambio a
    los tests de otros módulos.
    """
    original = SimpleRateThrottle.THROTTLE_RATES
    SimpleRateThrottle.THROTTLE_RATES = {**original, 'cliente_password': None}
    yield
    SimpleRateThrottle.THROTTLE_RATES = original


@pytest.fixture
def centro(db):
    return CentroEstetica.objects.create(nombre='Centro A', telefono='1111', email='a@centro.com')


@pytest.fixture
def ficha(centro):
    return Cliente.objects.create(
        centro_estetica=centro, nombre='María', apellido='Rivaldo', telefono='1150517958',
    )


@pytest.fixture
def usuaria(ficha):
    """Una cuenta con todo lo que una cuenta real acumula."""
    cuenta = UsuarioCliente.objects.create_user(email='maria@mail.com', password=CLAVE)
    codigo = CodigoInvitacion.objects.create(cliente=ficha)
    codigo.usado_por = cuenta
    codigo.usado_en = timezone.now()
    codigo.save()
    VinculacionCliente.objects.create(usuario_cliente=cuenta, cliente=ficha)
    DispositivoPush.objects.create(usuario_cliente=cuenta, token='ExponentPushToken[abc]')
    PreferenciaNotificacion.objects.create(usuario_cliente=cuenta, categoria='PROMOCIONES',
                                           habilitada=False)
    Aviso.objects.create(
        usuario_cliente=cuenta, cliente=ficha, evento='turno_confirmado', categoria='TURNOS',
        titulo='Tu turno', cuerpo='Confirmado', programado_para=timezone.now(),
    )
    CodigoRecuperacion.emitir(cuenta)
    return cuenta


def con_sesion(cuenta):
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens_para_usuario_cliente(cuenta)['access']}")
    return api


def eliminar(api, password=CLAVE):
    datos = {} if password is None else {'password': password}
    return api.delete(reverse('client-perfil'), datos, format='json')


class TestLoQueSeBorra:
    def test_borra_la_cuenta(self, usuaria):
        resp = eliminar(con_sesion(usuaria))

        assert resp.status_code == 204
        assert not UsuarioCliente.objects.filter(pk=usuaria.pk).exists()

    def test_se_lleva_todo_lo_que_es_de_la_cuenta(self, usuaria):
        pk = usuaria.pk
        eliminar(con_sesion(usuaria))

        assert not VinculacionCliente.objects.filter(usuario_cliente_id=pk).exists()
        assert not DispositivoPush.objects.filter(usuario_cliente_id=pk).exists()
        assert not PreferenciaNotificacion.objects.filter(usuario_cliente_id=pk).exists()
        assert not Aviso.objects.filter(usuario_cliente_id=pk).exists()
        assert not CodigoRecuperacion.objects.filter(usuario_cliente_id=pk).exists()

    def test_el_token_de_la_sesion_deja_de_servir(self, usuaria):
        api = con_sesion(usuaria)
        eliminar(api)

        assert api.get(reverse('client-perfil')).status_code == 401


class TestLoQueQueda:
    def test_la_ficha_del_centro_no_se_toca(self, usuaria, ficha):
        eliminar(con_sesion(usuaria))

        assert Cliente.objects.filter(pk=ficha.pk).exists()

    def test_el_codigo_de_invitacion_queda_sin_dueña(self, usuaria, ficha):
        """El código es del centro: se conserva, sin apuntar a una cuenta que no existe."""
        eliminar(con_sesion(usuaria))

        codigo = CodigoInvitacion.objects.get(cliente=ficha)
        assert codigo.usado_por is None

    def test_no_toca_otra_cuenta_vinculada_a_la_misma_ficha(self, usuaria, ficha):
        otra = UsuarioCliente.objects.create_user(email='hermana@mail.com', password=CLAVE)
        VinculacionCliente.objects.create(usuario_cliente=otra, cliente=ficha)
        DispositivoPush.objects.create(usuario_cliente=otra, token='ExponentPushToken[otro]')

        eliminar(con_sesion(usuaria))

        assert VinculacionCliente.objects.filter(usuario_cliente=otra).exists()
        assert DispositivoPush.objects.filter(usuario_cliente=otra).exists()


class TestLaContraseña:
    def test_con_contraseña_equivocada_no_borra(self, usuaria):
        resp = eliminar(con_sesion(usuaria), password='NoEsEsta999')

        assert resp.status_code == 400
        assert 'password' in resp.data
        assert UsuarioCliente.objects.filter(pk=usuaria.pk).exists()

    def test_sin_contraseña_no_borra(self, usuaria):
        resp = eliminar(con_sesion(usuaria), password=None)

        assert resp.status_code == 400
        assert UsuarioCliente.objects.filter(pk=usuaria.pk).exists()

    def test_sin_sesion_no_se_puede(self, usuaria):
        resp = eliminar(APIClient())

        assert resp.status_code == 401
        assert UsuarioCliente.objects.filter(pk=usuaria.pk).exists()


def test_cada_relacion_de_la_cuenta_tiene_decidido_que_pasa_en_la_baja():
    """
    Si aparece una relación nueva hacia la cuenta, este test falla a propósito.

    Una FK nueva con CASCADE se borraría con la baja sin que nadie lo decida: si
    fuera, por ejemplo, un registro de compras, el centro perdería ventas. Una con
    PROTECT haría fallar la baja en producción. Antes de agregarla acá, decidir
    en ``apps/clientes/cuenta_app.py`` qué le corresponde.
    """
    relaciones = {
        (rel.related_model._meta.label, rel.field.name, rel.on_delete.__name__)
        for rel in UsuarioCliente._meta.related_objects
    }

    assert relaciones == {
        ('clientes.VinculacionCliente', 'usuario_cliente', 'CASCADE'),
        ('clientes.CodigoInvitacion', 'usado_por', 'SET_NULL'),
        ('clientes.CodigoRecuperacion', 'usuario_cliente', 'CASCADE'),
        ('notificaciones.DispositivoPush', 'usuario_cliente', 'CASCADE'),
        ('notificaciones.PreferenciaNotificacion', 'usuario_cliente', 'CASCADE'),
        ('notificaciones.Aviso', 'usuario_cliente', 'CASCADE'),
    }

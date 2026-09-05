"""
Recuperación de contraseña por código de seis dígitos.

Lo que se cuida acá no es el camino feliz —ese es de una línea— sino las tres
propiedades que hacen que el circuito no se convierta en un agujero:

1. **No revela quién tiene cuenta.** Un centro de estética tiene clientela que
   no necesariamente quiere ser identificada. Si el endpoint contestara distinto
   para un email registrado, alcanzaría con probar direcciones.
2. **El código se quema.** De un solo uso, con vencimiento y con tope de
   intentos, para que no quede una puerta abierta ni se pueda tantear por fuerza
   bruta dentro de la ventana.
3. **Pedir uno nuevo invalida el anterior.** Si no, cada pedido deja una llave
   más dando vueltas.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.clientes.models import CodigoRecuperacion, UsuarioCliente


@pytest.fixture(autouse=True)
def sin_throttle():
    """
    Apaga el límite de 5/hora, que estos tests superan a propósito.

    Se toca el atributo de clase y no los settings: DRF fija `THROTTLE_RATES` al
    importar el módulo, así que un `override_settings` no siempre llega. Se
    restaura al terminar para no filtrarle el cambio a los tests de otros
    módulos, que es lo que ya pasó una vez en este proyecto.
    """
    original = SimpleRateThrottle.THROTTLE_RATES
    SimpleRateThrottle.THROTTLE_RATES = {**original, 'cliente_password': None}
    yield
    SimpleRateThrottle.THROTTLE_RATES = original


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def usuaria(db):
    return UsuarioCliente.objects.create_user(
        email='sofia@test.local', password='ClaveVieja123', nombre='Sofía'
    )


def pedir(api, email):
    return api.post(reverse('client-olvide-clave'), {'email': email}, format='json')


def restablecer(api, email, codigo, password='ClaveNueva456'):
    return api.post(
        reverse('client-restablecer-clave'),
        {'email': email, 'codigo': codigo, 'password': password},
        format='json',
    )


@pytest.mark.django_db
class TestPedidoDeCodigo:
    def test_una_cuenta_existente_recibe_un_codigo(self, api, usuaria):
        with patch('apps.client_api.views.enviar_correo') as enviar:
            assert pedir(api, usuaria.email).status_code == 200

        assert CodigoRecuperacion.objects.filter(usuario_cliente=usuaria).count() == 1
        # El código viaja en el cuerpo del mail y en ningún otro lado.
        assert enviar.call_count == 1

    def test_un_email_desconocido_responde_igual_y_no_manda_nada(self, api, usuaria):
        """La respuesta no puede distinguirse; es toda la protección."""
        with patch('apps.client_api.views.enviar_correo') as enviar:
            conocida = pedir(api, usuaria.email)
            desconocida = pedir(api, 'nadie@test.local')

        assert conocida.status_code == desconocida.status_code == 200
        assert conocida.data == desconocida.data
        assert enviar.call_count == 1

    def test_si_el_mail_falla_la_respuesta_es_la_misma(self, api, usuaria):
        from apps.notificaciones.correo import CorreoNoEnviado

        with patch('apps.client_api.views.enviar_correo', side_effect=CorreoNoEnviado('SES caído')):
            assert pedir(api, usuaria.email).status_code == 200

    def test_pedir_otro_invalida_el_anterior(self, api, usuaria):
        with patch('apps.client_api.views.enviar_correo'):
            pedir(api, usuaria.email)
            primero = CodigoRecuperacion.objects.get(usuario_cliente=usuaria)
            pedir(api, usuaria.email)

        assert not CodigoRecuperacion.objects.filter(pk=primero.pk).exists()
        assert CodigoRecuperacion.objects.filter(usuario_cliente=usuaria).count() == 1

    def test_el_codigo_no_se_guarda_en_claro(self, usuaria):
        _, codigo = CodigoRecuperacion.emitir(usuaria)
        guardado = CodigoRecuperacion.objects.get(usuario_cliente=usuaria)
        assert codigo not in guardado.codigo_hash


@pytest.mark.django_db
class TestRestablecer:
    def test_el_camino_feliz_cambia_la_clave(self, api, usuaria):
        _, codigo = CodigoRecuperacion.emitir(usuaria)

        assert restablecer(api, usuaria.email, codigo).status_code == 200

        usuaria.refresh_from_db()
        assert usuaria.check_password('ClaveNueva456')

    def test_el_codigo_no_sirve_dos_veces(self, api, usuaria):
        _, codigo = CodigoRecuperacion.emitir(usuaria)
        restablecer(api, usuaria.email, codigo)

        segunda = restablecer(api, usuaria.email, codigo, password='OtraMas789')
        assert segunda.status_code == 400

        usuaria.refresh_from_db()
        assert usuaria.check_password('ClaveNueva456')

    def test_un_codigo_vencido_no_sirve(self, api, usuaria):
        obj, codigo = CodigoRecuperacion.emitir(usuaria)
        obj.expira_en = timezone.now() - timedelta(minutes=1)
        obj.save(update_fields=['expira_en'])

        assert restablecer(api, usuaria.email, codigo).status_code == 400
        usuaria.refresh_from_db()
        assert usuaria.check_password('ClaveVieja123')

    def test_se_agotan_los_intentos(self, api, usuaria):
        _, codigo = CodigoRecuperacion.emitir(usuaria)

        for _ in range(CodigoRecuperacion.MAX_INTENTOS):
            assert restablecer(api, usuaria.email, '000000').status_code == 400

        # Y a partir de acá ni siquiera el código correcto entra.
        assert restablecer(api, usuaria.email, codigo).status_code == 400
        usuaria.refresh_from_db()
        assert usuaria.check_password('ClaveVieja123')

    def test_el_error_no_distingue_cuenta_inexistente_de_codigo_malo(self, api, usuaria):
        CodigoRecuperacion.emitir(usuaria)

        malo = restablecer(api, usuaria.email, '000000')
        inexistente = restablecer(api, 'nadie@test.local', '000000')

        assert malo.status_code == inexistente.status_code == 400
        assert malo.data == inexistente.data

    def test_rechaza_una_clave_debil(self, api, usuaria):
        _, codigo = CodigoRecuperacion.emitir(usuaria)

        assert restablecer(api, usuaria.email, codigo, password='123').status_code == 400
        usuaria.refresh_from_db()
        assert usuaria.check_password('ClaveVieja123')

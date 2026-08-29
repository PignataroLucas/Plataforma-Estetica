"""
Tests del intercambio OAuth con Tienda Nube y del comando que vincula.

Lo que se cuida acá no es el happy path —ese lo verifica una instalación real—
sino los dos modos de fallar que cuestan una vuelta entera por el navegador:

1. Que un error de Tienda Nube se lea. El código de instalación **dura cinco
   minutos**, así que "invalid_grant" y "invalid_client" se parecen desde la
   terminal y tienen arreglos opuestos: uno es reinstalar, el otro es revisar
   las credenciales de la app.
2. Que un token que no sirve no se guarde como si sirviera.

Y una regla de aislamiento: una tienda vinculada a un centro no se le puede
robar a otro, porque emitir cupones en la tienda equivocada es plata de alguien.
"""
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.empleados.models import CentroEstetica
from apps.integraciones.models import TiendanubeIntegration
from apps.integraciones.tiendanube import (
    TiendanubeAuthError,
    TiendanubeError,
    TiendanubeNotConfigured,
    exchange_code_for_token,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)
        self.content = b'x'

    def json(self):
        return self._payload


def hacer_centro(nombre='Ame'):
    return CentroEstetica.objects.create(
        nombre=nombre, telefono='1', email=f'{nombre}@test.local'
    )


@pytest.fixture
def credenciales(settings):
    settings.TIENDANUBE_CLIENT_ID = '39429'
    settings.TIENDANUBE_CLIENT_SECRET = 'secreto'


class TestIntercambioDelCodigo:

    def test_sin_credenciales_no_se_intenta_el_intercambio(self, settings):
        """
        Falla antes de salir a la red y nombra las dos variables. El error de
        Tienda Nube sería `invalid_client`, que manda a buscar el problema al
        lugar equivocado.
        """
        settings.TIENDANUBE_CLIENT_ID = ''
        settings.TIENDANUBE_CLIENT_SECRET = ''

        with pytest.raises(TiendanubeNotConfigured) as exc:
            exchange_code_for_token('abc')

        assert 'TIENDANUBE_CLIENT_ID' in str(exc.value)

    def test_devuelve_el_token_y_la_tienda(self, credenciales):
        payload = {
            'access_token': 'tok_123',
            'user_id': 4321,
            'scope': 'read_products,write_coupons',
        }
        with patch('apps.integraciones.tiendanube.requests.post',
                   return_value=FakeResponse(payload)) as post:
            datos = exchange_code_for_token('abc')

        assert datos['access_token'] == 'tok_123'
        assert datos['user_id'] == 4321
        # El grant_type va siempre: sin él, Tienda Nube contesta que falta.
        assert post.call_args.kwargs['json']['grant_type'] == 'authorization_code'

    def test_un_codigo_vencido_dice_que_hay_que_reinstalar(self, credenciales):
        """Es el error más frecuente, porque el código dura 5 minutos."""
        payload = {'error': 'invalid_grant', 'error_description': 'The code is invalid'}
        with patch('apps.integraciones.tiendanube.requests.post',
                   return_value=FakeResponse(payload, status_code=400)):
            with pytest.raises(TiendanubeAuthError) as exc:
                exchange_code_for_token('vencido')

        assert 'volvé a instalar' in str(exc.value).lower()

    def test_credenciales_malas_mandan_a_claves_de_acceso(self, credenciales):
        payload = {'error': 'invalid_client', 'error_description': 'Invalid credentials'}
        with patch('apps.integraciones.tiendanube.requests.post',
                   return_value=FakeResponse(payload, status_code=401)):
            with pytest.raises(TiendanubeAuthError) as exc:
                exchange_code_for_token('abc')

        assert 'TIENDANUBE_CLIENT_SECRET' in str(exc.value)

    def test_un_error_devuelto_con_200_tambien_es_error(self, credenciales):
        """
        Tienda Nube contesta el error con 200 y una clave `error` tan seguido
        como con 4xx. Mirar solo el status guardaría un token vacío.
        """
        payload = {'error': 'invalid_grant', 'error_description': 'expired'}
        with patch('apps.integraciones.tiendanube.requests.post',
                   return_value=FakeResponse(payload, status_code=200)):
            with pytest.raises(TiendanubeAuthError):
                exchange_code_for_token('abc')

    def test_una_respuesta_sin_token_no_pasa_por_buena(self, credenciales):
        with patch('apps.integraciones.tiendanube.requests.post',
                   return_value=FakeResponse({'user_id': 1})):
            with pytest.raises(TiendanubeError):
                exchange_code_for_token('abc')


@pytest.mark.django_db
class TestComandoVincular:

    def _exchange(self, store_id=4321):
        return {
            'access_token': 'tok_123',
            'user_id': store_id,
            'scope': 'read_products,write_coupons',
        }

    def test_vincula_el_centro_con_su_tienda(self, credenciales):
        centro = hacer_centro()

        with patch('apps.integraciones.management.commands.vincular_tiendanube'
                   '.exchange_code_for_token', return_value=self._exchange()), \
             patch('apps.integraciones.tiendanube.TiendanubeClient.get_store',
                   return_value={'name': {'es': 'Ame Demo'}}):
            call_command('vincular_tiendanube', centro=centro.id, code='abc')

        integracion = TiendanubeIntegration.objects.get(center=centro)
        assert integracion.store_id == '4321'
        assert integracion.token == 'tok_123'
        assert integracion.store_name == 'Ame Demo'
        assert integracion.can_issue_coupons

    def test_reinstalar_actualiza_en_vez_de_duplicar(self, credenciales):
        """
        Desinstalar y volver a instalar emite un token nuevo. El viejo ya no
        sirve, así que la fila se pisa: dos filas para un centro dejarían la
        emisión de cupones dependiendo de cuál se lea primero.
        """
        centro = hacer_centro()
        TiendanubeIntegration.objects.create(
            center=centro, store_id='4321', token='viejo', is_active=False,
        )

        with patch('apps.integraciones.management.commands.vincular_tiendanube'
                   '.exchange_code_for_token', return_value=self._exchange()), \
             patch('apps.integraciones.tiendanube.TiendanubeClient.get_store',
                   return_value={'name': 'Ame Demo'}):
            call_command('vincular_tiendanube', centro=centro.id, code='abc')

        assert TiendanubeIntegration.objects.filter(center=centro).count() == 1
        integracion = TiendanubeIntegration.objects.get(center=centro)
        assert integracion.token == 'tok_123'
        assert integracion.is_active

    def test_una_tienda_de_otro_centro_se_rechaza_con_nombre_y_apellido(self, credenciales):
        """
        Emitir cupones en la tienda de otro centro es plata ajena. La unique
        constraint lo impediría igual, pero con un IntegrityError que no dice
        de quién es la tienda.
        """
        centro_a, centro_b = hacer_centro('A'), hacer_centro('B')
        TiendanubeIntegration.objects.create(
            center=centro_a, store_id='4321', token='tok_a',
        )

        with patch('apps.integraciones.management.commands.vincular_tiendanube'
                   '.exchange_code_for_token', return_value=self._exchange()):
            with pytest.raises(CommandError) as exc:
                call_command('vincular_tiendanube', centro=centro_b.id, code='abc')

        assert 'A' in str(exc.value)
        assert not TiendanubeIntegration.objects.filter(center=centro_b).exists()

    def test_si_la_tienda_no_responde_igual_guarda_el_token_pero_avisa(self, credenciales):
        """
        El token ya es válido —el intercambio lo devolvió—, así que tirarlo
        obligaría a reinstalar por una lectura que puede fallar por red. Se
        guarda y se avisa.
        """
        centro = hacer_centro()

        with patch('apps.integraciones.management.commands.vincular_tiendanube'
                   '.exchange_code_for_token', return_value=self._exchange()), \
             patch('apps.integraciones.tiendanube.TiendanubeClient.get_store',
                   side_effect=TiendanubeError('sin red')):
            call_command('vincular_tiendanube', centro=centro.id, code='abc')

        integracion = TiendanubeIntegration.objects.get(center=centro)
        assert integracion.token == 'tok_123'
        assert integracion.store_name == ''

    def test_un_centro_que_no_existe_es_un_error_claro(self, credenciales):
        with pytest.raises(CommandError):
            call_command('vincular_tiendanube', centro=9999, code='abc')

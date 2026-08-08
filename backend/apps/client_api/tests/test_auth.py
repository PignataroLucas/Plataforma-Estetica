from datetime import timedelta

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.clientes.models import (
    Cliente,
    CodigoInvitacion,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.client_api.tokens import tokens_para_usuario_cliente
from apps.empleados.models import CentroEstetica, Usuario
from apps.notificaciones.models import DispositivoPush, PreferenciaNotificacion

# Cache local + throttle desactivado para tests hermeticos
TEST_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    # Se parte del diccionario real y solo se anulan los scopes bajo prueba.
    # Reemplazarlo entero borraba los otros scopes, y como DRF cachea las tasas
    # en la clase del throttle, la pérdida se filtraba a los tests de otros
    # módulos que corrían después (KeyError: 'public_api').
    'DEFAULT_THROTTLE_RATES': {
        **settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'],
        'cliente_auth': None,
        'cliente_registro': None,
    },
}


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    REST_FRAMEWORK=TEST_REST_FRAMEWORK,
)
class ClientAuthTests(APITestCase):
    def setUp(self):
        self.centro_a = CentroEstetica.objects.create(
            nombre='Centro A', telefono='1111', email='a@centro.com'
        )
        self.centro_b = CentroEstetica.objects.create(
            nombre='Centro B', telefono='2222', email='b@centro.com'
        )
        self.cliente_a = Cliente.objects.create(
            centro_estetica=self.centro_a,
            nombre='Maria', apellido='Rivaldo', telefono='1150517958',
        )
        self.staff = Usuario.objects.create_user(
            username='staff_a', password='staffpass123',
            centro_estetica=self.centro_a, rol=Usuario.Rol.ADMIN,
        )

    # ---------- Registro con código ----------

    def test_registro_con_codigo_valido(self):
        codigo = CodigoInvitacion.objects.create(cliente=self.cliente_a)
        resp = self.client.post(reverse('client-registro'), {
            'email': 'maria@mail.com', 'password': 'ClaveSegura123', 'codigo': codigo.codigo,
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

        usuario = UsuarioCliente.objects.get(email='maria@mail.com')
        vinc = VinculacionCliente.objects.get(usuario_cliente=usuario)
        self.assertEqual(vinc.cliente, self.cliente_a)
        self.assertEqual(vinc.metodo_vinculacion, VinculacionCliente.Metodo.CODIGO_INVITACION)

        codigo.refresh_from_db()
        self.assertEqual(codigo.estado, 'USADO')
        self.assertEqual(codigo.usado_por, usuario)

    def test_registro_codigo_ya_usado(self):
        otro = UsuarioCliente.objects.create_user(email='otro@mail.com', password='x123ABCdef')
        codigo = CodigoInvitacion.objects.create(cliente=self.cliente_a)
        codigo.marcar_usado(otro)

        resp = self.client.post(reverse('client-registro'), {
            'email': 'nueva@mail.com', 'password': 'ClaveSegura123', 'codigo': codigo.codigo,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(UsuarioCliente.objects.filter(email='nueva@mail.com').exists())

    def test_registro_codigo_expirado(self):
        codigo = CodigoInvitacion.objects.create(
            cliente=self.cliente_a, expira_en=timezone.now() - timedelta(hours=1)
        )
        resp = self.client.post(reverse('client-registro'), {
            'email': 'nueva@mail.com', 'password': 'ClaveSegura123', 'codigo': codigo.codigo,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_codigo_inexistente(self):
        resp = self.client.post(reverse('client-registro'), {
            'email': 'nueva@mail.com', 'password': 'ClaveSegura123', 'codigo': 'XXX-YYYY-ZZZZ',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- Registro nuevo (auto-registro) ----------

    def test_registro_nuevo_con_centro(self):
        resp = self.client.post(reverse('client-registro'), {
            'email': 'nuevo@mail.com', 'password': 'ClaveSegura123',
            'nombre': 'Ana', 'apellido': 'Gomez', 'centro': self.centro_a.id,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        usuario = UsuarioCliente.objects.get(email='nuevo@mail.com')
        vinc = VinculacionCliente.objects.get(usuario_cliente=usuario)
        self.assertEqual(vinc.metodo_vinculacion, VinculacionCliente.Metodo.REGISTRO_NUEVO)
        self.assertEqual(vinc.cliente.centro_estetica, self.centro_a)
        self.assertEqual(vinc.cliente.nombre, 'Ana')

    def test_registro_nuevo_sin_centro_falla(self):
        resp = self.client.post(reverse('client-registro'), {
            'email': 'nuevo@mail.com', 'password': 'ClaveSegura123',
            'nombre': 'Ana', 'apellido': 'Gomez',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_duplicado_case_insensitive(self):
        UsuarioCliente.objects.create_user(email='dup@mail.com', password='x123ABCdef')
        resp = self.client.post(reverse('client-registro'), {
            'email': 'DUP@mail.com', 'password': 'ClaveSegura123',
            'nombre': 'A', 'apellido': 'B', 'centro': self.centro_a.id,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_nuevo_no_expone_otro_centro(self):
        """El auto-registro crea ficha SOLO en el centro indicado."""
        resp = self.client.post(reverse('client-registro'), {
            'email': 'multi@mail.com', 'password': 'ClaveSegura123',
            'nombre': 'Ana', 'apellido': 'Gomez', 'centro': self.centro_a.id,
        }, format='json')
        usuario = UsuarioCliente.objects.get(email='multi@mail.com')
        centros = list(usuario.centros.values_list('id', flat=True))
        self.assertEqual(centros, [self.centro_a.id])
        self.assertNotIn(self.centro_b.id, centros)

    # ---------- Login ----------

    def test_login_ok(self):
        UsuarioCliente.objects.create_user(email='log@mail.com', password='ClaveSegura123')
        resp = self.client.post(reverse('client-login'), {
            'email': 'LOG@mail.com', 'password': 'ClaveSegura123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_login_password_incorrecto(self):
        UsuarioCliente.objects.create_user(email='log@mail.com', password='ClaveSegura123')
        resp = self.client.post(reverse('client-login'), {
            'email': 'log@mail.com', 'password': 'incorrecta',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_email_inexistente(self):
        resp = self.client.post(reverse('client-login'), {
            'email': 'noexiste@mail.com', 'password': 'ClaveSegura123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------- Perfil ----------

    def _crear_usuario_vinculado(self, email='perfil@mail.com'):
        usuario = UsuarioCliente.objects.create_user(
            email=email, password='ClaveSegura123', nombre='Maria', apellido='R',
        )
        VinculacionCliente.objects.create(
            usuario_cliente=usuario, cliente=self.cliente_a,
            metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
        )
        return usuario

    def test_perfil_con_token_cliente(self):
        usuario = self._crear_usuario_vinculado()
        token = tokens_para_usuario_cliente(usuario)['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('client-perfil'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['email'], 'perfil@mail.com')
        self.assertEqual(len(resp.data['vinculaciones']), 1)
        self.assertEqual(resp.data['vinculaciones'][0]['centro_id'], self.centro_a.id)

    def test_perfil_sin_token(self):
        resp = self.client.get(reverse('client-perfil'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------- Cross-auth (CRÍTICO) ----------

    def test_token_staff_rechazado_en_endpoint_cliente(self):
        """Un token de staff NO debe autenticar en la app."""
        staff_token = str(RefreshToken.for_user(self.staff).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {staff_token}')
        resp = self.client.get(reverse('client-perfil'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_cliente_rechazado_en_endpoint_staff(self):
        """Un token de cliente NO debe autenticar en endpoints de staff."""
        usuario = self._crear_usuario_vinculado()
        token = tokens_para_usuario_cliente(usuario)['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # Endpoint de staff existente (lista de clientes del CRM)
        resp = self.client.get('/api/clientes/clientes/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------- Refresh ----------

    def test_refresh_token_cliente(self):
        usuario = self._crear_usuario_vinculado()
        refresh = tokens_para_usuario_cliente(usuario)['refresh']
        resp = self.client.post(reverse('client-refresh'), {'refresh': refresh}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        nuevo_access = resp.data['access']
        # El nuevo access sigue siendo válido en la app
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {nuevo_access}')
        perfil = self.client.get(reverse('client-perfil'))
        self.assertEqual(perfil.status_code, status.HTTP_200_OK)

    def test_refresh_token_staff_rechazado(self):
        staff_refresh = str(RefreshToken.for_user(self.staff))
        resp = self.client.post(reverse('client-refresh'), {'refresh': staff_refresh}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------- Push ----------

    def _autenticar(self, usuario):
        token = tokens_para_usuario_cliente(usuario)['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_push_register(self):
        usuario = self._crear_usuario_vinculado()
        self._autenticar(usuario)
        resp = self.client.post(reverse('client-push-register'),
                                {'push_token': 'ExponentPushToken[abc123]',
                                 'plataforma': 'ANDROID'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        dispositivo = DispositivoPush.objects.get(token='ExponentPushToken[abc123]')
        self.assertEqual(dispositivo.usuario_cliente, usuario)
        self.assertTrue(dispositivo.activo)

    def test_push_register_es_idempotente(self):
        usuario = self._crear_usuario_vinculado()
        self._autenticar(usuario)
        for _ in range(3):
            self.client.post(reverse('client-push-register'),
                             {'push_token': 'ExponentPushToken[abc123]'}, format='json')
        self.assertEqual(DispositivoPush.objects.count(), 1)

    def test_una_cuenta_puede_registrar_dos_telefonos(self):
        usuario = self._crear_usuario_vinculado()
        self._autenticar(usuario)
        for token in ('ExponentPushToken[uno]', 'ExponentPushToken[dos]'):
            self.client.post(reverse('client-push-register'),
                             {'push_token': token}, format='json')
        self.assertEqual(DispositivoPush.objects.filter(usuario_cliente=usuario).count(), 2)

    def test_el_telefono_prestado_se_reasigna_a_la_cuenta_nueva(self):
        """
        Si otra cuenta inicia sesión en el mismo aparato, el token pasa a ser
        suyo: si no, el teléfono seguiría recibiendo los turnos de la anterior.
        """
        primera = self._crear_usuario_vinculado()
        self._autenticar(primera)
        self.client.post(reverse('client-push-register'),
                         {'push_token': 'ExponentPushToken[compartido]'}, format='json')

        segunda = self._crear_usuario_vinculado(email='otra@mail.com')
        self._autenticar(segunda)
        self.client.post(reverse('client-push-register'),
                         {'push_token': 'ExponentPushToken[compartido]'}, format='json')

        self.assertEqual(DispositivoPush.objects.count(), 1)
        self.assertEqual(DispositivoPush.objects.get().usuario_cliente, segunda)

    def test_push_register_rechaza_un_token_que_no_es_de_expo(self):
        usuario = self._crear_usuario_vinculado()
        self._autenticar(usuario)
        resp = self.client.post(reverse('client-push-register'),
                                {'push_token': 'cualquier-cosa'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(DispositivoPush.objects.exists())

    def test_push_unregister_da_de_baja_el_dispositivo(self):
        usuario = self._crear_usuario_vinculado()
        self._autenticar(usuario)
        self.client.post(reverse('client-push-register'),
                         {'push_token': 'ExponentPushToken[abc123]'}, format='json')

        resp = self.client.delete(reverse('client-push-register'),
                                  {'push_token': 'ExponentPushToken[abc123]'}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dispositivo = DispositivoPush.objects.get()
        self.assertFalse(dispositivo.activo)
        self.assertEqual(dispositivo.motivo_baja, DispositivoPush.MotivoBaja.SESION_CERRADA)

    def test_no_se_puede_dar_de_baja_el_dispositivo_de_otra_cuenta(self):
        primera = self._crear_usuario_vinculado()
        self._autenticar(primera)
        self.client.post(reverse('client-push-register'),
                         {'push_token': 'ExponentPushToken[ajeno]'}, format='json')

        segunda = self._crear_usuario_vinculado(email='otra@mail.com')
        self._autenticar(segunda)
        resp = self.client.delete(reverse('client-push-register'),
                                  {'push_token': 'ExponentPushToken[ajeno]'}, format='json')

        self.assertFalse(resp.data['dado_de_baja'])
        self.assertTrue(DispositivoPush.objects.get().activo)

    def test_push_register_sin_auth(self):
        resp = self.client.post(reverse('client-push-register'),
                                {'push_token': 'ExponentPushToken[abc123]'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------- Preferencias ----------

    def test_preferencias_arrancan_todas_encendidas(self):
        usuario = self._crear_usuario_vinculado()
        self._autenticar(usuario)
        resp = self.client.get(reverse('client-preferencias-notificacion'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(all(resp.data.values()))
        self.assertIn('TURNOS', resp.data)

    def test_apagar_y_volver_a_encender_una_categoria(self):
        usuario = self._crear_usuario_vinculado()
        self._autenticar(usuario)
        url = reverse('client-preferencias-notificacion')

        resp = self.client.patch(url, {'PROMOCIONES': False}, format='json')
        self.assertFalse(resp.data['PROMOCIONES'])
        self.assertTrue(resp.data['TURNOS'])
        self.assertEqual(
            PreferenciaNotificacion.objects.filter(usuario_cliente=usuario).count(), 1
        )

        resp = self.client.patch(url, {'PROMOCIONES': True}, format='json')
        self.assertTrue(resp.data['PROMOCIONES'])
        # Encender borra la excepción en lugar de guardar un True.
        self.assertEqual(
            PreferenciaNotificacion.objects.filter(usuario_cliente=usuario).count(), 0
        )

    def test_preferencias_rechaza_una_categoria_inventada(self):
        usuario = self._crear_usuario_vinculado()
        self._autenticar(usuario)
        resp = self.client.patch(reverse('client-preferencias-notificacion'),
                                 {'LO_QUE_SEA': False}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_preferencias_sin_auth(self):
        resp = self.client.get(reverse('client-preferencias-notificacion'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

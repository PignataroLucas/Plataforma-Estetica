from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.clientes.models import Cliente, UsuarioCliente, VinculacionCliente
from apps.empleados.models import CentroEstetica

TEST_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {'cliente_auth': None, 'cliente_registro': None},
}

TELEFONO = '+5491151234567'  # AR mobile válido (normaliza a E.164)


@override_settings(
    # LOCATION propia: aísla la cache de throttle de otras clases (LocMemCache
    # default es global al proceso y contaminaría el conteo de rate limit).
    CACHES={'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'registro-guard-tests',
    }},
    REST_FRAMEWORK=TEST_REST_FRAMEWORK,
)
class RegistroGuardTests(APITestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(
            nombre='Centro', telefono='1', email='c@c.com'
        )

    def _post(self, email, telefono):
        return self.client.post(reverse('client-registro'), {
            'email': email, 'password': 'ClaveSegura123',
            'nombre': 'Maria', 'apellido': 'Lopez',
            'telefono': telefono, 'centro': self.centro.id,
        }, format='json')

    def test_match_telefono_y_email_vincula_a_ficha_existente(self):
        ficha = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Maria', apellido='Lopez',
            telefono=TELEFONO, email='maria@x.com',
        )
        # Sanity: el teléfono es válido y normalizó
        self.assertTrue(ficha.telefono_normalizado)

        resp = self._post(email='maria@x.com', telefono=TELEFONO)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # NO se creó una ficha nueva
        self.assertEqual(Cliente.objects.filter(centro_estetica=self.centro).count(), 1)

        # La cuenta quedó vinculada a la ficha existente, por AUTO_MATCH
        vinc = VinculacionCliente.objects.get(cliente=ficha)
        self.assertEqual(vinc.metodo_vinculacion, VinculacionCliente.Metodo.AUTO_MATCH)
        self.assertEqual(resp.data['usuario']['vinculaciones'][0]['cliente_id'], ficha.id)

    def test_match_solo_telefono_crea_ficha_nueva(self):
        Cliente.objects.create(
            centro_estetica=self.centro, nombre='Maria', apellido='Lopez',
            telefono=TELEFONO, email='maria@x.com',
        )
        # Mismo teléfono, distinto email → NO auto-vincula (requiere ambos)
        resp = self._post(email='otra@x.com', telefono=TELEFONO)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Cliente.objects.filter(centro_estetica=self.centro).count(), 2)
        usuario = UsuarioCliente.objects.get(email='otra@x.com')
        vinc = VinculacionCliente.objects.get(usuario_cliente=usuario)
        self.assertEqual(vinc.metodo_vinculacion, VinculacionCliente.Metodo.REGISTRO_NUEVO)

    def test_sin_match_crea_ficha_nueva(self):
        resp = self._post(email='nueva@x.com', telefono='+5491159998877')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cliente.objects.filter(centro_estetica=self.centro).count(), 1)
        usuario = UsuarioCliente.objects.get(email='nueva@x.com')
        vinc = VinculacionCliente.objects.get(usuario_cliente=usuario)
        self.assertEqual(vinc.metodo_vinculacion, VinculacionCliente.Metodo.REGISTRO_NUEVO)

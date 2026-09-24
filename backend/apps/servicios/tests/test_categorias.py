from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.servicios.models import CategoriaServicio, Servicio

TEST_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {**settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], 'public_api': None},
}

CATEGORIAS_URL = '/api/servicios/categorias/'
SERVICIOS_URL = '/api/servicios/servicios/'


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    REST_FRAMEWORK=TEST_REST_FRAMEWORK,
)
class CategoriasServicioTests(APITestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(nombre='Centro A', telefono='1', email='a@c.com')
        self.otro_centro = CentroEstetica.objects.create(nombre='Centro B', telefono='2', email='b@c.com')
        self.sucursal = Sucursal.objects.create(
            centro_estetica=self.centro, nombre='Suc A', direccion='Dir A',
            telefono='1', ciudad='CABA', provincia='BsAs',
        )
        self.otra_sucursal = Sucursal.objects.create(
            centro_estetica=self.otro_centro, nombre='Suc B', direccion='Dir B',
            telefono='2', ciudad='CABA', provincia='BsAs',
        )
        self.staff = Usuario.objects.create_user(
            username='staff', password='staffpass123',
            centro_estetica=self.centro, sucursal=self.sucursal, rol=Usuario.Rol.ADMIN,
        )
        self.client.force_authenticate(self.staff)

        self.facial = CategoriaServicio.objects.create(sucursal=self.sucursal, nombre='Facial')
        self.ajena = CategoriaServicio.objects.create(sucursal=self.otra_sucursal, nombre='Corporal')
        self.servicio = Servicio.objects.create(
            sucursal=self.sucursal, nombre='HIFU', duracion_minutos=60, precio=65000
        )

    def test_asigna_categoria_propia(self):
        resp = self.client.patch(f'{SERVICIOS_URL}{self.servicio.id}/', {'categoria': self.facial.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.categoria, self.facial)

    def test_rechaza_categoria_de_otra_sucursal(self):
        resp = self.client.patch(f'{SERVICIOS_URL}{self.servicio.id}/', {'categoria': self.ajena.id})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.servicio.refresh_from_db()
        self.assertIsNone(self.servicio.categoria)

    def test_null_le_saca_la_categoria(self):
        self.servicio.categoria = self.facial
        self.servicio.save()
        resp = self.client.patch(
            f'{SERVICIOS_URL}{self.servicio.id}/', {'categoria': None}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.servicio.refresh_from_db()
        self.assertIsNone(self.servicio.categoria)

    def test_crea_categoria_en_la_sucursal_del_usuario(self):
        resp = self.client.post(CATEGORIAS_URL, {'nombre': '  Corporal  '})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        creada = CategoriaServicio.objects.get(id=resp.data['id'])
        self.assertEqual(creada.sucursal, self.sucursal)
        self.assertEqual(creada.nombre, 'Corporal')

    def test_nombre_repetido_da_400_y_no_500(self):
        resp = self.client.post(CATEGORIAS_URL, {'nombre': 'facial'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', resp.data)

    def test_renombrar_a_si_misma_no_choca(self):
        resp = self.client.patch(f'{CATEGORIAS_URL}{self.facial.id}/', {'nombre': 'Facial'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_app_muestra_categoria_activa_y_oculta_inactiva(self):
        self.servicio.categoria = self.facial
        self.servicio.save()
        url = reverse('public-centro-servicio-detalle', args=[self.centro.id, self.servicio.id])

        resp = self.client.get(url)
        self.assertEqual(resp.data['categoria_nombre'], 'Facial')

        self.facial.activa = False
        self.facial.save()
        resp = self.client.get(url)
        self.assertIsNone(resp.data['categoria_nombre'])

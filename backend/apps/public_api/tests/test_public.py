from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.empleados.models import CentroEstetica, Sucursal
from apps.inventario.models import Producto
from apps.servicios.models import Servicio

TEST_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {**settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], 'public_api': None},
}


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    REST_FRAMEWORK=TEST_REST_FRAMEWORK,
)
class PublicApiTests(APITestCase):
    def setUp(self):
        self.centro_a = CentroEstetica.objects.create(
            nombre='Centro A', telefono='111', email='a@c.com', direccion='Calle 1'
        )
        self.centro_b = CentroEstetica.objects.create(
            nombre='Centro B', telefono='222', email='b@c.com'
        )
        self.suc_a = Sucursal.objects.create(
            centro_estetica=self.centro_a, nombre='Suc A', direccion='Dir A',
            telefono='111', ciudad='CABA', provincia='BsAs',
        )
        self.suc_b = Sucursal.objects.create(
            centro_estetica=self.centro_b, nombre='Suc B', direccion='Dir B',
            telefono='222', ciudad='CABA', provincia='BsAs',
        )
        # Servicios
        self.serv_activo = Servicio.objects.create(
            sucursal=self.suc_a, nombre='Limpieza facial', duracion_minutos=60, precio=5000
        )
        self.serv_inactivo = Servicio.objects.create(
            sucursal=self.suc_a, nombre='Servicio viejo', duracion_minutos=30, precio=3000, activo=False
        )
        self.serv_centro_b = Servicio.objects.create(
            sucursal=self.suc_b, nombre='Masaje B', duracion_minutos=45, precio=4000
        )
        # Productos
        self.prod_reventa = Producto.objects.create(
            sucursal=self.suc_a, nombre='Serum Vitamina C', tipo=Producto.TipoProducto.REVENTA,
            precio_costo=1000, precio_venta=3000, stock_actual=5,
        )
        self.prod_reventa_inactivo = Producto.objects.create(
            sucursal=self.suc_a, nombre='Producto discontinuado', tipo=Producto.TipoProducto.REVENTA,
            precio_costo=1000, precio_venta=3000, stock_actual=0, activo=False,
        )
        self.prod_uso_interno = Producto.objects.create(
            sucursal=self.suc_a, nombre='Algodón', tipo=Producto.TipoProducto.USO_INTERNO,
            precio_costo=100, precio_venta=200, stock_actual=100,
        )

    # ---------- Info ----------

    def test_info_sin_auth(self):
        resp = self.client.get(reverse('public-centro-info', args=[self.centro_a.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nombre'], 'Centro A')
        self.assertEqual(len(resp.data['sucursales']), 1)

    def test_info_centro_inexistente_404(self):
        resp = self.client.get(reverse('public-centro-info', args=[99999]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_info_centro_inactivo_404(self):
        self.centro_a.activo = False
        self.centro_a.save()
        resp = self.client.get(reverse('public-centro-info', args=[self.centro_a.id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # ---------- Servicios ----------

    def test_servicios_solo_activos_del_centro(self):
        resp = self.client.get(reverse('public-centro-servicios', args=[self.centro_a.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        nombres = [s['nombre'] for s in resp.data['results']]
        self.assertIn('Limpieza facial', nombres)
        self.assertNotIn('Servicio viejo', nombres)   # inactivo excluido
        self.assertNotIn('Masaje B', nombres)          # otro centro excluido

    # ---------- Productos ----------

    def test_productos_solo_reventa_activos(self):
        resp = self.client.get(reverse('public-centro-productos', args=[self.centro_a.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        nombres = [p['nombre'] for p in resp.data['results']]
        self.assertIn('Serum Vitamina C', nombres)
        self.assertNotIn('Producto discontinuado', nombres)  # inactivo
        self.assertNotIn('Algodón', nombres)                 # uso interno

    def test_productos_no_filtran_datos_internos(self):
        resp = self.client.get(reverse('public-centro-productos', args=[self.centro_a.id]))
        prod = resp.data['results'][0]
        # Datos internos NO deben aparecer
        for campo in ['precio_costo', 'margen_ganancia', 'stock_actual', 'stock_minimo', 'proveedor']:
            self.assertNotIn(campo, prod)
        # Disponibilidad como booleano, no el stock exacto
        self.assertIn('disponible', prod)
        self.assertTrue(prod['disponible'])

    def test_productos_centro_b_no_leak(self):
        # Centro B no tiene productos; debe devolver lista vacía, no los de A
        resp = self.client.get(reverse('public-centro-productos', args=[self.centro_b.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'], [])

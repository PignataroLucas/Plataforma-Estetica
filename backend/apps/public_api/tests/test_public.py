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

    def test_servicios_no_filtran_datos_internos(self):
        resp = self.client.get(reverse('public-centro-servicios', args=[self.centro_a.id]))
        serv = resp.data['results'][0]
        for campo in ['comision_porcentaje', 'costo_maquina_diario', 'ganancia_por_servicio',
                      'profit_porcentaje', 'maquina_alquilada', 'codigo']:
            self.assertNotIn(campo, serv)

    # ---------- Ficha del servicio ----------

    def test_ficha_devuelve_contenido_cargado_por_el_centro(self):
        self.serv_activo.descripcion = 'Limpieza profunda en cabina.'
        self.serv_activo.beneficios = 'Piel luminosa\nMenos poros visibles'
        self.serv_activo.video_url = 'https://www.instagram.com/reel/abc/'
        self.serv_activo.reservable_por_cliente = True
        self.serv_activo.save()

        resp = self.client.get(
            reverse('public-centro-servicio-detalle', args=[self.centro_a.id, self.serv_activo.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nombre'], 'Limpieza facial')
        self.assertEqual(resp.data['descripcion'], 'Limpieza profunda en cabina.')
        self.assertEqual(resp.data['beneficios'], 'Piel luminosa\nMenos poros visibles')
        self.assertEqual(resp.data['video_url'], 'https://www.instagram.com/reel/abc/')
        # La app decide con esto si muestra "Reservar" o "Consultar con el centro"
        self.assertTrue(resp.data['reservable_por_cliente'])

    def test_ficha_de_servicio_inactivo_404(self):
        resp = self.client.get(
            reverse('public-centro-servicio-detalle', args=[self.centro_a.id, self.serv_inactivo.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_ficha_de_otro_centro_404(self):
        # El id existe, pero no en el centro pedido: no se puede espiar el catálogo ajeno
        resp = self.client.get(
            reverse('public-centro-servicio-detalle', args=[self.centro_a.id, self.serv_centro_b.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

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

    def test_productos_no_exponen_disponibilidad(self):
        """
        `disponible` se sacó a propósito: devolvía `stock_actual > 0`, y desde el
        sync con Conto ese stock es el del depósito, no el del mostrador. La app
        le habría dicho a una clienta que no está disponible algo que está en la
        vitrina. Mientras los dos stocks no estén separados, no decir nada es
        más honesto que mentir.
        """
        resp = self.client.get(reverse('public-centro-productos', args=[self.centro_a.id]))
        self.assertNotIn('disponible', resp.data['results'][0])

    def test_productos_centro_b_no_leak(self):
        # Centro B no tiene productos; debe devolver lista vacía, no los de A
        resp = self.client.get(reverse('public-centro-productos', args=[self.centro_b.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'], [])

    # ---------- Ficha de producto ----------

    def test_producto_detalle_devuelve_la_ficha(self):
        resp = self.client.get(reverse(
            'public-centro-producto-detalle', args=[self.centro_a.id, self.prod_reventa.id]
        ))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nombre'], 'Serum Vitamina C')

    def test_producto_detalle_de_otro_centro_da_404(self):
        """
        El id es adivinable, así que el scope de la ficha tiene que ser el mismo
        que el del listado: si no, pedir ids al azar recorre el catálogo de
        cualquier centro.
        """
        resp = self.client.get(reverse(
            'public-centro-producto-detalle', args=[self.centro_b.id, self.prod_reventa.id]
        ))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_producto_detalle_no_expone_los_que_el_listado_oculta(self):
        """Un producto inactivo o de uso interno no puede abrirse por id."""
        for producto in (self.prod_reventa_inactivo, self.prod_uso_interno):
            resp = self.client.get(reverse(
                'public-centro-producto-detalle', args=[self.centro_a.id, producto.id]
            ))
            self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND, producto.nombre)

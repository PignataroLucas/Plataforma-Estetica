"""
Tests de POST /api/client/comprar/.

Es el endpoint que la app llama al tocar "Comprar": emite el cupón y devuelve
qué mandarle al checkout de Tienda Nube.

Lo que se cuida acá es plata y aislamiento:

1. **El cupón lleva el descuento que la app mostró.** Sale de
   `Cliente.descuento_app`, el mismo número del catálogo (§5.8). Si acá se
   recalculara, la clienta vería un precio y pagaría otro (§6.1).
2. **Un carrito no puede tocar productos de otro centro.** El id llega del
   dispositivo, así que es entrada no confiable.
3. **Un producto sin emparejar con Tienda Nube no se puede comprar**, y el
   pedido falla entero en vez de abrir un checkout al que le falta un artículo.
"""
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.client_api.tokens import tokens_para_usuario_cliente
from apps.clientes.models import (
    Cliente,
    SegmentoApp,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.empleados.models import CentroEstetica, Sucursal
from apps.integraciones.models import CuponApp, TiendanubeIntegration
from apps.inventario.models import Producto


class PrepararCompraTests(APITestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(
            nombre='Ame', telefono='1', email='ame@test.local'
        )
        self.sucursal = Sucursal.objects.create(
            centro_estetica=self.centro, nombre='Suc', direccion='x',
            telefono='1', ciudad='CABA', provincia='CABA',
        )
        self.integracion = TiendanubeIntegration.objects.create(
            center=self.centro, store_id='8100688', token='tok',
            store_name='Ame Demo', store_url='https://amedemo.mitiendanube.com',
        )
        SegmentoApp.objects.create(
            centro_estetica=self.centro, nombre='General de la app',
            porcentaje_descuento=Decimal('15.00'), es_predeterminado=True,
        )

        self.producto = Producto.objects.create(
            sucursal=self.sucursal, nombre='Serum', precio_costo=Decimal('50'),
            precio_venta=Decimal('100'), tiendanube_product_id='361410527',
            tiendanube_variant_id='1578078539',
        )

        self.cliente = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Ana', apellido='Gómez', telefono='11',
        )
        self.usuario = UsuarioCliente.objects.create_user(
            email='ana@test.com', password='x', nombre='Ana',
        )
        VinculacionCliente.objects.create(
            usuario_cliente=self.usuario, cliente=self.cliente,
            metodo_vinculacion=VinculacionCliente.Metodo.REGISTRO_NUEVO,
        )

        self.url = reverse('client-comprar')
        tokens = tokens_para_usuario_cliente(self.usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def comprar(self, items=None):
        cuerpo = {'items': items or [{'producto': self.producto.id, 'cantidad': 2}]}
        with patch('apps.integraciones.cupones.TiendanubeClient.create_coupon',
                   return_value={'id': 67713598}):
            return self.client.post(self.url, cuerpo, format='json')

    def test_devuelve_el_carrito_y_el_cupon(self):
        respuesta = self.comprar()

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.data
        self.assertEqual(datos['checkout']['url'], 'https://amedemo.mitiendanube.com/comprar/')
        # Una línea por producto: Tienda Nube agrega de a uno por POST.
        self.assertEqual(datos['checkout']['items'], [{
            'producto_tiendanube': '361410527', 'cantidad': 2, 'nombre': 'Serum',
        }])
        self.assertEqual(datos['cupon']['porcentaje'], '15.00')
        self.assertTrue(datos['cupon']['codigo'].startswith('APP-'))

    def test_el_total_es_el_que_vio_la_clienta(self):
        """2 × $100 con 15% = $170. El mismo número que la app mostró en el carrito."""
        respuesta = self.comprar()

        self.assertEqual(respuesta.data['subtotal'], '200.00')
        self.assertEqual(respuesta.data['total'], '170.00')

    def test_el_cupon_queda_atado_a_la_clienta(self):
        """Es lo que hace atribuible la venta cuando vuelve por Conto (§5.6)."""
        respuesta = self.comprar()

        cupon = CuponApp.objects.get(code=respuesta.data['cupon']['codigo'])
        self.assertEqual(cupon.cliente, self.cliente)
        self.assertEqual(cupon.percentage, self.cliente.descuento_app)

    def test_sin_descuento_la_compra_sigue_en_pie(self):
        """
        Que no le toque descuento no puede impedirle comprar: el catálogo le
        mostró precio de lista y eso es lo que va a pagar.
        """
        SegmentoApp.objects.update(porcentaje_descuento=Decimal('0.00'))

        respuesta = self.comprar()

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIsNone(respuesta.data['cupon'])
        self.assertEqual(respuesta.data['total'], '200.00')
        self.assertFalse(CuponApp.objects.exists())

    def test_un_producto_sin_emparejar_no_se_puede_comprar(self):
        """
        Sin el id de Tienda Nube no hay carrito que armar. Falla el pedido
        entero: abrir un checkout al que le falta un artículo es peor.
        """
        self.producto.tiendanube_product_id = ''
        self.producto.save()

        respuesta = self.comprar()

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Serum', respuesta.data['detail'])
        self.assertFalse(CuponApp.objects.exists())

    def test_un_producto_de_otro_centro_no_entra_al_carrito(self):
        """El id lo manda el dispositivo: es entrada no confiable."""
        otro_centro = CentroEstetica.objects.create(
            nombre='Otro', telefono='2', email='otro@test.local'
        )
        otra_sucursal = Sucursal.objects.create(
            centro_estetica=otro_centro, nombre='Suc', direccion='x',
            telefono='1', ciudad='CABA', provincia='CABA',
        )
        ajeno = Producto.objects.create(
            sucursal=otra_sucursal, nombre='Ajeno', precio_costo=Decimal('1'),
            precio_venta=Decimal('999'), tiendanube_product_id='999',
        )

        respuesta = self.comprar([{'producto': ajeno.id, 'cantidad': 1}])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CuponApp.objects.exists())

    def test_un_producto_inactivo_no_se_vende(self):
        self.producto.activo = False
        self.producto.save()

        respuesta = self.comprar()

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_tienda_vinculada_avisa_en_castellano(self):
        self.integracion.delete()

        respuesta = self.comprar()

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tienda', respuesta.data['detail'].lower())

    def test_el_carrito_vacio_se_rechaza(self):
        respuesta = self.client.post(self.url, {'items': []}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_sesion_no_se_puede_comprar(self):
        self.client.credentials()
        respuesta = self.client.post(
            self.url, {'items': [{'producto': self.producto.id, 'cantidad': 1}]},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

"""
Tests de GET /api/client/descuento/.

El endpoint existe porque el catálogo es público y devuelve precio de lista: el
descuento no es del producto sino de la clienta, así que solo se puede resolver
con la sesión iniciada (COMPRA_EN_APP_SPEC.md §5.8).

Lo que se cuida acá es que el número que la app usa para pintar los precios sea
el mismo que el backend tiene para esa clienta. En cuanto se separen, la app
muestra un precio y el checkout cobra otro (§6.1).
"""
from decimal import Decimal

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
from apps.empleados.models import CentroEstetica


class DescuentoAppTests(APITestCase):
    def setUp(self):
        self.centro_a = CentroEstetica.objects.create(
            nombre='Centro A', telefono='1111', email='a@centro.com'
        )
        self.centro_b = CentroEstetica.objects.create(
            nombre='Centro B', telefono='2222', email='b@centro.com'
        )

        self.general_a = SegmentoApp.objects.create(
            centro_estetica=self.centro_a, nombre='General de la app',
            porcentaje_descuento=Decimal('10.00'), es_predeterminado=True,
        )
        SegmentoApp.objects.create(
            centro_estetica=self.centro_b, nombre='General de la app',
            porcentaje_descuento=Decimal('5.00'), es_predeterminado=True,
        )

        self.cliente_a = Cliente.objects.create(
            centro_estetica=self.centro_a, nombre='Maria', apellido='Rivaldo', telefono='11',
        )
        self.cliente_b = Cliente.objects.create(
            centro_estetica=self.centro_b, nombre='Maria', apellido='Rivaldo', telefono='11',
        )

        self.usuario = UsuarioCliente.objects.create_user(
            email='maria@test.com', password='x', nombre='Maria',
        )
        VinculacionCliente.objects.create(
            usuario_cliente=self.usuario, cliente=self.cliente_a,
            metodo_vinculacion=VinculacionCliente.Metodo.REGISTRO_NUEVO,
        )

        self.url = reverse('client-descuento-app')

    def autenticar(self, usuario=None):
        tokens = tokens_para_usuario_cliente(usuario or self.usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_sin_sesion_no_devuelve_nada(self):
        """El precio segmentado es de la clienta: sin sesión no hay a quién resolverle."""
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_devuelve_el_general_cuando_no_tiene_segmento_propio(self):
        self.autenticar()
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['porcentaje'], '10.00')
        self.assertEqual(respuesta.data['segmento'], 'General de la app')
        self.assertEqual(respuesta.data['centro'], self.centro_a.id)

    def test_devuelve_el_segmento_propio(self):
        vip = SegmentoApp.objects.create(
            centro_estetica=self.centro_a, nombre='VIP',
            porcentaje_descuento=Decimal('20.00'),
        )
        self.cliente_a.segmento_app = vip
        self.cliente_a.save()

        self.autenticar()
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.data['porcentaje'], '20.00')
        self.assertEqual(respuesta.data['segmento'], 'VIP')

    def test_es_el_mismo_numero_que_tiene_el_backend(self):
        """
        Un solo origen: este es el porcentaje que después se va a emitir como
        cupón. Si el endpoint redondeara o resolviera distinto que
        `Cliente.descuento_app`, la app mostraría un precio que nadie va a cobrar.
        """
        self.general_a.porcentaje_descuento = Decimal('12.50')
        self.general_a.save()

        self.autenticar()
        respuesta = self.client.get(self.url)

        self.cliente_a.refresh_from_db()
        self.assertEqual(
            Decimal(respuesta.data['porcentaje']), self.cliente_a.descuento_app
        )

    def test_cada_centro_tiene_su_descuento(self):
        """
        Una cuenta puede estar vinculada a varios centros y el descuento es de
        cada uno: sin el filtro, la app le mostraría a la clienta el porcentaje
        del centro equivocado.
        """
        VinculacionCliente.objects.create(
            usuario_cliente=self.usuario, cliente=self.cliente_b,
            metodo_vinculacion=VinculacionCliente.Metodo.REGISTRO_NUEVO,
        )

        self.autenticar()
        respuesta_a = self.client.get(self.url, {'centro': self.centro_a.id})
        respuesta_b = self.client.get(self.url, {'centro': self.centro_b.id})

        self.assertEqual(respuesta_a.data['porcentaje'], '10.00')
        self.assertEqual(respuesta_b.data['porcentaje'], '5.00')

    def test_sin_vinculacion_en_ese_centro_no_inventa_un_descuento(self):
        self.autenticar()
        respuesta = self.client.get(self.url, {'centro': self.centro_b.id})

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_sin_segmentos_cargados_devuelve_cero(self):
        """
        El centro que todavía no configuró nada tiene que devolver 0, no fallar:
        la app pide esto en cada arranque y un error acá dejaría la tienda sin
        precios.
        """
        self.general_a.delete()

        self.autenticar()
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['porcentaje'], '0.00')
        self.assertIsNone(respuesta.data['segmento'])

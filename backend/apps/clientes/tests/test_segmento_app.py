"""
Tests del segmento de la app y del descuento que resuelve.

Lo que se cuida acá es que `Cliente.descuento_app` devuelva UN número y siempre
el mismo. Ese número es el que la app usa para mostrar precios y el que después
se va a emitir como cupón en Tienda Nube (COMPRA_EN_APP_SPEC.md §5.8): si la
resolución cambia según por dónde se la mire, la clienta ve un precio y paga
otro, que es exactamente la trampa del §6.1.
"""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.clientes.models import Cliente, SegmentoApp
from apps.empleados.models import CentroEstetica, Usuario


def hacer_centro(nombre):
    return CentroEstetica.objects.create(
        nombre=nombre, telefono='1', email=f'{nombre}@test.local'
    )


def hacer_cliente(centro, **extra):
    datos = {'nombre': 'Ana', 'apellido': 'Gómez', 'telefono': '11'}
    datos.update(extra)
    return Cliente.objects.create(centro_estetica=centro, **datos)


class ResolucionDelDescuentoTests(APITestCase):
    """
    Qué porcentaje le toca a cada clienta, según lo que tenga cargado el centro.
    """

    def setUp(self):
        self.centro = hacer_centro('A')
        self.general = SegmentoApp.objects.create(
            centro_estetica=self.centro, nombre='General de la app',
            porcentaje_descuento=Decimal('10.00'), es_predeterminado=True,
        )
        self.vip = SegmentoApp.objects.create(
            centro_estetica=self.centro, nombre='VIP',
            porcentaje_descuento=Decimal('20.00'),
        )

    def test_sin_segmento_propio_le_toca_el_general(self):
        cliente = hacer_cliente(self.centro)
        self.assertEqual(cliente.descuento_app, Decimal('10.00'))

    def test_con_segmento_propio_le_toca_el_suyo(self):
        cliente = hacer_cliente(self.centro, segmento_app=self.vip)
        self.assertEqual(cliente.descuento_app, Decimal('20.00'))

    def test_un_segmento_desactivado_cae_al_general_y_no_a_cero(self):
        """
        Apagar "VIP" es dejar de tratarlas distinto, no dejarlas sin el descuento
        que tiene cualquiera por usar la app. A cero, además, el centro apagaría
        el incentivo sin haberlo decidido.
        """
        cliente = hacer_cliente(self.centro, segmento_app=self.vip)
        self.vip.activo = False
        self.vip.save()

        self.assertEqual(cliente.descuento_app, Decimal('10.00'))

    def test_sin_general_activo_no_hay_descuento(self):
        """
        Cero es el default correcto: el precio de lista es el que Tienda Nube va
        a cobrar igual, así que sin segmento cargado la app no promete nada.
        """
        self.general.activo = False
        self.general.save()
        cliente = hacer_cliente(self.centro)

        self.assertEqual(cliente.descuento_app, Decimal('0.00'))

    def test_el_general_de_otro_centro_no_se_aplica(self):
        """Aislamiento entre inquilinos: el descuento lo pone cada centro."""
        otro = hacer_centro('B')
        SegmentoApp.objects.create(
            centro_estetica=otro, nombre='General de la app',
            porcentaje_descuento=Decimal('50.00'), es_predeterminado=True,
        )
        # El centro A se queda sin general activo: si la resolución no filtrara
        # por centro, la clienta de A se llevaría el 50% del centro B.
        self.general.activo = False
        self.general.save()

        self.assertEqual(hacer_cliente(self.centro).descuento_app, Decimal('0.00'))

    def test_borrar_el_segmento_deja_a_la_clienta_en_el_general(self):
        """
        `SET_NULL` y no cascade: borrar un segmento no puede borrar fichas de
        clientas. Vuelven al general, que es lo que les tocaba antes.
        """
        cliente = hacer_cliente(self.centro, segmento_app=self.vip)
        self.vip.delete()

        cliente.refresh_from_db()
        self.assertIsNone(cliente.segmento_app)
        self.assertEqual(cliente.descuento_app, Decimal('10.00'))


class UnicidadDelGeneralTests(APITestCase):
    """
    Con dos generales en el mismo centro, cuál gana lo decidiría el orden de la
    tabla — y el precio que ve la clienta dependería de eso.
    """

    def test_no_puede_haber_dos_generales_en_un_centro(self):
        centro = hacer_centro('A')
        SegmentoApp.objects.create(
            centro_estetica=centro, nombre='General', es_predeterminado=True
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SegmentoApp.objects.create(
                    centro_estetica=centro, nombre='Otro general', es_predeterminado=True
                )

    def test_cada_centro_tiene_el_suyo(self):
        a, b = hacer_centro('A'), hacer_centro('B')
        SegmentoApp.objects.create(centro_estetica=a, nombre='General', es_predeterminado=True)
        SegmentoApp.objects.create(centro_estetica=b, nombre='General', es_predeterminado=True)

        self.assertEqual(SegmentoApp.objects.filter(es_predeterminado=True).count(), 2)


class SegmentosApiTests(APITestCase):
    """El ABM de segmentos del CRM."""

    def setUp(self):
        self.centro = hacer_centro('A')
        self.admin = Usuario.objects.create_user(
            username='admin', password='x', centro_estetica=self.centro,
            rol=Usuario.Rol.ADMIN,
        )
        self.empleada = Usuario.objects.create_user(
            username='empleada', password='x', centro_estetica=self.centro,
            rol=Usuario.Rol.EMPLEADO,
        )
        self.general = SegmentoApp.objects.create(
            centro_estetica=self.centro, nombre='General de la app',
            porcentaje_descuento=Decimal('10.00'), es_predeterminado=True,
        )
        self.url = reverse('segmento-app-list')

    def test_admin_puede_crear(self):
        self.client.force_authenticate(self.admin)
        respuesta = self.client.post(
            self.url, {'nombre': 'VIP', 'porcentaje_descuento': '20.00'}, format='json'
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        creado = SegmentoApp.objects.get(nombre='VIP')
        # El centro sale del usuario, nunca del body.
        self.assertEqual(creado.centro_estetica, self.centro)

    def test_una_empleada_no_toca_los_descuentos(self):
        """El porcentaje es margen del centro, no dato de operación diaria."""
        self.client.force_authenticate(self.empleada)
        respuesta = self.client.post(
            self.url, {'nombre': 'VIP', 'porcentaje_descuento': '20.00'}, format='json'
        )

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_se_ven_los_segmentos_de_otro_centro(self):
        otro = hacer_centro('B')
        SegmentoApp.objects.create(centro_estetica=otro, nombre='Ajeno')

        self.client.force_authenticate(self.admin)
        respuesta = self.client.get(self.url)

        nombres = {s['nombre'] for s in respuesta.data['results']}
        self.assertEqual(nombres, {'General de la app'})

    def test_el_general_no_se_puede_borrar(self):
        """
        Borrarlo pondría a todas las clientas sin segmento propio en 0% de un
        saque, sin nada en pantalla que explique por qué.
        """
        self.client.force_authenticate(self.admin)
        respuesta = self.client.delete(f'{self.url}{self.general.id}/')

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(SegmentoApp.objects.filter(pk=self.general.pk).exists())

    def test_un_segmento_normal_si_se_borra(self):
        vip = SegmentoApp.objects.create(centro_estetica=self.centro, nombre='VIP')

        self.client.force_authenticate(self.admin)
        respuesta = self.client.delete(f'{self.url}{vip.id}/')

        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)


class AsignacionDesdeLaFichaTests(APITestCase):
    """La asignación arranca a mano, desde la pantalla de la clienta (§5.8)."""

    def setUp(self):
        self.centro = hacer_centro('A')
        self.admin = Usuario.objects.create_user(
            username='admin', password='x', centro_estetica=self.centro,
            rol=Usuario.Rol.ADMIN,
        )
        self.client.force_authenticate(self.admin)
        self.cliente = hacer_cliente(self.centro)
        self.vip = SegmentoApp.objects.create(
            centro_estetica=self.centro, nombre='VIP',
            porcentaje_descuento=Decimal('20.00'),
        )

    def test_asignar_segmento_a_una_clienta(self):
        respuesta = self.client.patch(
            reverse('cliente-detail', args=[self.cliente.id]),
            {'segmento_app': self.vip.id}, format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['segmento_app_nombre'], 'VIP')
        # La ficha del CRM muestra el mismo número que va a ver la app.
        self.assertEqual(respuesta.data['descuento_app'], '20.00')

    def test_no_se_puede_asignar_un_segmento_de_otro_centro(self):
        ajeno = SegmentoApp.objects.create(
            centro_estetica=hacer_centro('B'), nombre='Ajeno',
            porcentaje_descuento=Decimal('99.00'),
        )

        respuesta = self.client.patch(
            reverse('cliente-detail', args=[self.cliente.id]),
            {'segmento_app': ajeno.id}, format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.cliente.refresh_from_db()
        self.assertIsNone(self.cliente.segmento_app)

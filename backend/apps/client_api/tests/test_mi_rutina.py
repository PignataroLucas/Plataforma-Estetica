from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.client_api.tokens import tokens_para_usuario_cliente
from apps.clientes.models import (
    Cliente,
    PlanTratamiento,
    RutinaCuidado,
    RutinaItem,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.empleados.models import CentroEstetica, Sucursal
from apps.inventario.models import Producto


class MiRutinaTests(APITestCase):
    def setUp(self):
        self.centro_a = CentroEstetica.objects.create(
            nombre='Centro A', telefono='1111', email='a@centro.com'
        )
        self.centro_b = CentroEstetica.objects.create(
            nombre='Centro B', telefono='2222', email='b@centro.com'
        )
        self.sucursal_a = Sucursal.objects.create(
            centro_estetica=self.centro_a, nombre='Suc A',
            direccion='Calle 1', telefono='1111', ciudad='CABA', provincia='BA',
        )

        self.cliente_a = Cliente.objects.create(
            centro_estetica=self.centro_a, nombre='Maria', apellido='Rivaldo', telefono='11',
        )
        self.cliente_b = Cliente.objects.create(
            centro_estetica=self.centro_b, nombre='Otra', apellido='Persona', telefono='22',
        )

        self.producto = Producto.objects.create(
            sucursal=self.sucursal_a, nombre='Serum Vitamina C', marca='The Ordinary',
            precio_costo=Decimal('1000'), precio_venta=Decimal('2500'),
            stock_actual=Decimal('5'), duracion_estimada_dias=60,
        )

        # Rutina activa de cliente_a con un item linkeado y otro de solo texto
        self.rutina_a = RutinaCuidado.objects.create(cliente=self.cliente_a, activa=True)
        RutinaItem.objects.create(
            rutina=self.rutina_a, momento=RutinaItem.Momento.DIURNA, orden=1,
            paso='Serum antioxidante', producto=self.producto,
        )
        RutinaItem.objects.create(
            rutina=self.rutina_a, momento=RutinaItem.Momento.NOCTURNA, orden=1,
            paso='Crema de noche', producto_texto='Crema Genérica',
        )
        self.plan_a = PlanTratamiento.objects.create(
            cliente=self.cliente_a, tratamiento_sugerido='Limpieza facial mensual',
            frecuencia='mensual', sesiones_estimadas=6,
        )

        # cliente_b tiene su propia rutina (para probar aislamiento)
        rutina_b = RutinaCuidado.objects.create(cliente=self.cliente_b, activa=True)
        RutinaItem.objects.create(
            rutina=rutina_b, momento=RutinaItem.Momento.DIURNA, orden=1, paso='SECRETO B',
        )

        self.user_a = UsuarioCliente.objects.create_user(
            email='a@mail.com', password='ClaveSegura123', nombre='Maria',
        )
        VinculacionCliente.objects.create(
            usuario_cliente=self.user_a, cliente=self.cliente_a,
            metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
        )
        self.user_b = UsuarioCliente.objects.create_user(
            email='b@mail.com', password='ClaveSegura123',
        )
        VinculacionCliente.objects.create(
            usuario_cliente=self.user_b, cliente=self.cliente_b,
            metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
        )

    def _auth(self, usuario):
        token = tokens_para_usuario_cliente(usuario)['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_devuelve_rutina_plan_y_centro(self):
        self._auth(self.user_a)
        resp = self.client.get(reverse('client-mi-rutina'))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['centro']['id'], self.centro_a.id)
        self.assertEqual(resp.data['cliente']['id'], self.cliente_a.id)

        self.assertIsNotNone(resp.data['rutina'])
        items = resp.data['rutina']['items']
        self.assertEqual(len(items), 2)

        # El item diurno trae el producto del catálogo anidado y curado
        diurno = next(i for i in items if i['momento'] == 'DIURNA')
        self.assertEqual(diurno['producto']['nombre'], 'Serum Vitamina C')
        self.assertIn('precio', diurno['producto'])
        # No debe filtrar datos internos del producto
        self.assertNotIn('precio_costo', diurno['producto'])

        # El item nocturno es solo texto (sin producto del catálogo)
        nocturno = next(i for i in items if i['momento'] == 'NOCTURNA')
        self.assertIsNone(nocturno['producto'])
        self.assertEqual(nocturno['producto_texto'], 'Crema Genérica')

        self.assertEqual(resp.data['plan']['tratamiento_sugerido'], 'Limpieza facial mensual')

    def test_aislamiento_entre_usuarios(self):
        """Cada usuario ve SOLO la rutina de su propia ficha vinculada."""
        self._auth(self.user_a)
        resp_a = self.client.get(reverse('client-mi-rutina'))
        self.assertEqual(resp_a.data['cliente']['id'], self.cliente_a.id)
        self.assertNotEqual(resp_a.data['cliente']['id'], self.cliente_b.id)

        self._auth(self.user_b)
        resp_b = self.client.get(reverse('client-mi-rutina'))
        self.assertEqual(resp_b.data['centro']['id'], self.centro_b.id)
        pasos_b = [i['paso'] for i in resp_b.data['rutina']['items']]
        self.assertIn('SECRETO B', pasos_b)

    def test_centro_param_inexistente_da_404(self):
        """Pedir un centro con el que el usuario no está vinculado no expone nada."""
        self._auth(self.user_a)
        resp = self.client.get(reverse('client-mi-rutina'), {'centro': self.centro_b.id})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_solo_rutina_activa(self):
        """Si hay varias rutinas, devuelve la activa."""
        RutinaCuidado.objects.create(cliente=self.cliente_a, activa=False)
        self._auth(self.user_a)
        resp = self.client.get(reverse('client-mi-rutina'))
        self.assertEqual(resp.data['rutina']['id'], self.rutina_a.id)
        self.assertTrue(resp.data['rutina']['activa'])

    def test_sin_rutina_devuelve_null(self):
        cliente = Cliente.objects.create(
            centro_estetica=self.centro_a, nombre='Sin', apellido='Rutina', telefono='33',
        )
        user = UsuarioCliente.objects.create_user(email='c@mail.com', password='ClaveSegura123')
        VinculacionCliente.objects.create(
            usuario_cliente=user, cliente=cliente,
            metodo_vinculacion=VinculacionCliente.Metodo.REGISTRO_NUEVO,
        )
        self._auth(user)
        resp = self.client.get(reverse('client-mi-rutina'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data['rutina'])
        self.assertIsNone(resp.data['plan'])

    def test_sin_auth_401(self):
        resp = self.client.get(reverse('client-mi-rutina'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

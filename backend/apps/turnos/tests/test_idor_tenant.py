"""
Aislamiento multi-tenant en la creación de turnos (POST /api/turnos/turnos/).

Lo que se cuida acá es un IDOR cross-tenant. El serializer aceptaba
`cliente`/`servicio`/`profesional` por id sin validar que pertenecieran al
centro/sucursal del usuario, así que un usuario del centro A podía crear un turno
apuntando a la ficha de un cliente del centro B (escritura cross-tenant + fuga
del nombre/teléfono del cliente ajeno en su propio calendario). El fix acota el
queryset de validación de cada FK al tenant del usuario; estos tests fijan que
un id ajeno se rechace con 400 y que el alta legítima siga funcionando.
"""
from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.clientes.models import Cliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.servicios.models import Servicio
from apps.turnos.models import Turno


def hacer_centro(nombre):
    centro = CentroEstetica.objects.create(
        nombre=nombre, telefono='1', email=f'{nombre}@test.local',
    )
    sucursal = Sucursal.objects.create(
        centro_estetica=centro, nombre=f'Suc {nombre}', direccion='x',
        telefono='1', ciudad='CABA', provincia='CABA',
    )
    return centro, sucursal


def hacer_servicio(sucursal):
    return Servicio.objects.create(
        sucursal=sucursal, nombre='Limpieza facial',
        duracion_minutos=60, precio=Decimal('20000'),
    )


def hacer_cliente(centro):
    return Cliente.objects.create(
        centro_estetica=centro, nombre='Ana', apellido='Gómez', telefono='11',
    )


class TurnoIDORTenantTests(APITestCase):
    """Un centro no puede referenciar objetos (cliente/servicio/profesional) de otro."""

    def setUp(self):
        # Centro A: el atacante autenticado y sus objetos propios.
        self.centro_a, self.suc_a = hacer_centro('A')
        self.admin_a = Usuario.objects.create_user(
            username='admin-a', password='x', rol='ADMIN',
            centro_estetica=self.centro_a, sucursal=self.suc_a,
        )
        self.servicio_a = hacer_servicio(self.suc_a)
        self.cliente_a = hacer_cliente(self.centro_a)

        # Centro B: los objetos ajenos que no deberían ser referenciables.
        self.centro_b, self.suc_b = hacer_centro('B')
        self.servicio_b = hacer_servicio(self.suc_b)
        self.cliente_b = hacer_cliente(self.centro_b)
        self.profesional_b = Usuario.objects.create_user(
            username='prof-b', password='x', rol='EMPLEADO',
            centro_estetica=self.centro_b, sucursal=self.suc_b,
        )

        self.url = reverse('turno-list')
        self.client.force_authenticate(user=self.admin_a)

    def _body(self, **override):
        inicio = timezone.now() + timedelta(days=2)
        body = {
            'cliente': self.cliente_a.id,
            'servicio': self.servicio_a.id,
            'fecha_hora_inicio': inicio.isoformat(),
        }
        body.update(override)
        return body

    def test_no_se_puede_crear_turno_con_cliente_de_otro_centro(self):
        resp = self.client.post(self.url, self._body(cliente=self.cliente_b.id), format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cliente', resp.data)
        # No debe haberse persistido nada apuntando a la ficha ajena.
        self.assertFalse(Turno.objects.filter(cliente=self.cliente_b).exists())

    def test_no_se_puede_crear_turno_con_servicio_de_otro_centro(self):
        resp = self.client.post(self.url, self._body(servicio=self.servicio_b.id), format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('servicio', resp.data)
        self.assertFalse(Turno.objects.filter(servicio=self.servicio_b).exists())

    def test_no_se_puede_crear_turno_con_profesional_de_otro_centro(self):
        resp = self.client.post(
            self.url, self._body(profesional=self.profesional_b.id), format='json'
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profesional', resp.data)
        self.assertFalse(Turno.objects.filter(profesional=self.profesional_b).exists())

    def test_un_id_ajeno_y_uno_inexistente_dan_el_mismo_error(self):
        """Sin diferencia de respuesta no queda oráculo para enumerar entre centros.

        DRF responde con el mismo código `does_not_exist` para un id de otro
        centro que para uno inexistente. Lo único que cambia en el texto es el pk
        que el propio atacante mandó, así que no aprende nada sobre el otro centro.
        """
        ajeno = self.client.post(self.url, self._body(cliente=self.cliente_b.id), format='json')
        inexistente = self.client.post(self.url, self._body(cliente=999999), format='json')

        self.assertEqual(ajeno.status_code, inexistente.status_code)
        self.assertEqual(ajeno.data['cliente'][0].code, 'does_not_exist')
        self.assertEqual(inexistente.data['cliente'][0].code, 'does_not_exist')

    def test_el_alta_legitima_del_propio_centro_sigue_funcionando(self):
        resp = self.client.post(
            self.url, self._body(profesional=self.admin_a.id), format='json'
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertTrue(
            Turno.objects.filter(
                cliente=self.cliente_a, servicio=self.servicio_a,
                sucursal=self.suc_a,
            ).exists()
        )

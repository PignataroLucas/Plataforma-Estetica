"""
Tests de los endpoints con los que el CRM resuelve los pedidos de la app.

Lo que se cuida acá es lo que el frontend no puede garantizar solo:

1. **Que nadie resuelva un pedido de otra sucursal.** El filtro por sucursal ya
   existe en el viewset; estos tests lo fijan para las acciones nuevas, que son
   las que cambian estado.
2. **Que el motivo sea obligatorio y de la lista.** Si el endpoint aceptara
   texto libre, el reporte de rechazos moriría por más que el formulario tenga
   un selector.
3. **Que `VENCIDO` no se pueda elegir a mano.** Es lo que separa "dijimos que
   no" de "nadie lo miró".
4. **Que una segunda resolución devuelva 409** y no pise a la primera.
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


class AprobacionAPITestBase(APITestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(
            nombre='AME', telefono='1', email='ame@test.local'
        )
        self.sucursal = Sucursal.objects.create(
            centro_estetica=self.centro, nombre='Banfield', direccion='Calle 1',
            telefono='1', ciudad='Banfield', provincia='BA',
        )
        self.duenia = Usuario.objects.create_user(
            username='duenia', password='x', first_name='Ana', last_name='Gómez',
            centro_estetica=self.centro, sucursal=self.sucursal,
        )
        self.servicio = Servicio.objects.create(
            sucursal=self.sucursal, nombre='Limpieza facial',
            duracion_minutos=60, precio=Decimal('20000'),
        )
        self.cliente = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Sofía', apellido='Paz', telefono='11',
        )
        self.client.force_authenticate(user=self.duenia)

    def pedido(self, sucursal=None, cliente=None, servicio=None, profesional=...):
        inicio = timezone.now() + timedelta(days=3)
        return Turno.objects.create(
            sucursal=sucursal or self.sucursal,
            cliente=cliente or self.cliente,
            servicio=servicio or self.servicio,
            # El modelo valida que el profesional sea de la misma sucursal, así
            # que el pedido de otro centro va sin profesional asignado.
            profesional=self.duenia if profesional is ... else profesional,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=60),
            estado=Turno.Estado.PENDIENTE,
            origen=Turno.Origen.APP,
            vence_en=timezone.now() + timedelta(hours=3),
            monto_total=self.servicio.precio,
        )


class TestPendientes(AprobacionAPITestBase):

    def test_lista_los_pedidos_sin_resolver(self):
        self.pedido()

        resp = self.client.get(reverse('turno-pendientes-de-aprobacion'))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['origen'], Turno.Origen.APP)

    def test_no_cuenta_los_turnos_del_crm(self):
        """El staff los cargó ya decididos: no hay nada que aprobar."""
        turno = self.pedido()
        turno.origen = Turno.Origen.CRM
        turno.save(update_fields=['origen'])

        resp = self.client.get(reverse('turno-pendientes-de-aprobacion'))

        self.assertEqual(resp.data['count'], 0)

    def test_no_cuenta_los_ya_resueltos(self):
        turno = self.pedido()
        turno.estado = Turno.Estado.CONFIRMADO
        turno.save(update_fields=['estado'])

        resp = self.client.get(reverse('turno-pendientes-de-aprobacion'))

        self.assertEqual(resp.data['count'], 0)

    def test_manda_el_vencimiento_para_mostrar_cuanto_falta(self):
        self.pedido()

        resp = self.client.get(reverse('turno-pendientes-de-aprobacion'))

        self.assertIsNotNone(resp.data['results'][0]['vence_en'])


class TestAprobar(AprobacionAPITestBase):

    def test_aprueba_y_deja_quien_fue(self):
        turno = self.pedido()

        resp = self.client.post(reverse('turno-aprobar', args=[turno.pk]))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.CONFIRMADO)
        self.assertEqual(turno.resuelto_por, self.duenia)

    def test_aprobarlo_dos_veces_da_409(self):
        """
        Dos personas del centro con el mismo pedido abierto. La segunda tiene que
        ver que alguien se le adelantó, no creer que lo aprobó ella.
        """
        turno = self.pedido()
        self.client.post(reverse('turno-aprobar', args=[turno.pk]))

        resp = self.client.post(reverse('turno-aprobar', args=[turno.pk]))

        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_no_se_puede_aprobar_el_de_otra_sucursal(self):
        otro_centro = CentroEstetica.objects.create(
            nombre='Otro', telefono='2', email='otro@test.local'
        )
        otra_sucursal = Sucursal.objects.create(
            centro_estetica=otro_centro, nombre='Otra', direccion='Calle 2',
            telefono='2', ciudad='CABA', provincia='BA',
        )
        ajeno = self.pedido(
            sucursal=otra_sucursal,
            profesional=None,
            cliente=Cliente.objects.create(
                centro_estetica=otro_centro, nombre='X', apellido='Y', telefono='2',
            ),
            servicio=Servicio.objects.create(
                sucursal=otra_sucursal, nombre='Otro', duracion_minutos=30,
                precio=Decimal('1000'),
            ),
        )

        resp = self.client.post(reverse('turno-aprobar', args=[ajeno.pk]))

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        ajeno.refresh_from_db()
        self.assertEqual(ajeno.estado, Turno.Estado.PENDIENTE)


class TestRechazar(AprobacionAPITestBase):

    def test_rechaza_con_motivo(self):
        turno = self.pedido()

        resp = self.client.post(
            reverse('turno-rechazar', args=[turno.pk]),
            {'motivo': Turno.MotivoRechazo.SIN_DISPONIBILIDAD,
             'detalle': 'Tengo la máquina ocupada'},
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.RECHAZADO)
        self.assertEqual(turno.detalle_rechazo, 'Tengo la máquina ocupada')

    def test_sin_motivo_no_pasa(self):
        turno = self.pedido()

        resp = self.client.post(reverse('turno-rechazar', args=[turno.pk]))

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.PENDIENTE)

    def test_un_motivo_inventado_no_pasa(self):
        """
        Si aceptara texto libre, el reporte de rechazos no se podría agrupar por
        más que el formulario tenga un selector.
        """
        turno = self.pedido()

        resp = self.client.post(
            reverse('turno-rechazar', args=[turno.pk]), {'motivo': 'porque si'}
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_se_puede_elegir_vencido_a_mano(self):
        """
        Ese motivo lo pone el sistema. Si alguien lo pudiera elegir, se perdería
        la distinción entre «dijimos que no» y «nadie lo miró».
        """
        turno = self.pedido()

        resp = self.client.post(
            reverse('turno-rechazar', args=[turno.pk]),
            {'motivo': Turno.MotivoRechazo.VENCIDO},
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rechazarlo_dos_veces_da_409(self):
        turno = self.pedido()
        self.client.post(
            reverse('turno-rechazar', args=[turno.pk]),
            {'motivo': Turno.MotivoRechazo.SIN_DISPONIBILIDAD},
        )

        resp = self.client.post(
            reverse('turno-rechazar', args=[turno.pk]),
            {'motivo': Turno.MotivoRechazo.SIN_DISPONIBILIDAD},
        )

        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)


class TestMotivos(AprobacionAPITestBase):

    def test_devuelve_las_opciones_del_selector(self):
        resp = self.client.get(reverse('turno-motivos-de-rechazo'))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        valores = [m['valor'] for m in resp.data]
        self.assertIn(Turno.MotivoRechazo.SIN_DISPONIBILIDAD, valores)

    def test_no_ofrece_el_de_vencimiento(self):
        resp = self.client.get(reverse('turno-motivos-de-rechazo'))

        valores = [m['valor'] for m in resp.data]
        self.assertNotIn(Turno.MotivoRechazo.VENCIDO, valores)

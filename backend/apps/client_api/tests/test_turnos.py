"""
Tests de los endpoints de turnos de la app (client_api).

Cubren el invariante central: el scope sale SIEMPRE de las vinculaciones del
usuario autenticado, nunca de un id del request. Y la reserva no puede pisar un
turno existente ni salirse de la agenda del profesional.
"""
from datetime import time, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.client_api.tokens import tokens_para_usuario_cliente
from apps.clientes.models import Cliente, UsuarioCliente, VinculacionCliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.servicios.models import Servicio
from apps.turnos.models import Turno
from apps.turnos.services import DIAS_MAXIMOS_A_FUTURO


def _proximo_dia_habil(dias=3):
    """Una fecha futura a las 10:00 hora local (dentro del horario por defecto 08-22)."""
    fecha = timezone.localdate() + timedelta(days=dias)
    return timezone.make_aware(
        timezone.datetime.combine(fecha, time(10, 0))
    )


# Cada clase con su propio cache: el LocMemCache por defecto es global al proceso
# y contamina el conteo del throttle de reservas entre clases de test.
@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'turnos-app-tests',
    }
})
class TurnosAppTestBase(APITestCase):
    def setUp(self):
        cache.clear()

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
        self.sucursal_b = Sucursal.objects.create(
            centro_estetica=self.centro_b, nombre='Suc B',
            direccion='Calle 2', telefono='2222', ciudad='CABA', provincia='BA',
        )

        self.profesional = Usuario.objects.create_user(
            username='ana', password='x', first_name='Ana', last_name='Gómez',
            centro_estetica=self.centro_a, sucursal=self.sucursal_a,
            rol=Usuario.Rol.EMPLEADO, intervalo_minutos=30,
        )
        self.profesional_b = Usuario.objects.create_user(
            username='beto', password='x', first_name='Beto', last_name='Ruiz',
            centro_estetica=self.centro_b, sucursal=self.sucursal_b,
            rol=Usuario.Rol.EMPLEADO, intervalo_minutos=30,
        )

        self.servicio = Servicio.objects.create(
            sucursal=self.sucursal_a, nombre='Limpieza facial',
            duracion_minutos=60, precio=Decimal('20000'),
        )
        self.servicio_b = Servicio.objects.create(
            sucursal=self.sucursal_b, nombre='Servicio de otro centro',
            duracion_minutos=60, precio=Decimal('30000'),
        )

        self.cliente_a = Cliente.objects.create(
            centro_estetica=self.centro_a, nombre='Flor', apellido='Audisio', telefono='11',
        )
        self.cliente_b = Cliente.objects.create(
            centro_estetica=self.centro_b, nombre='Otra', apellido='Persona', telefono='22',
        )

        self.user_a = UsuarioCliente.objects.create_user(
            email='a@mail.com', password='ClaveSegura123', nombre='Flor',
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

    def _crear_turno(self, cliente=None, inicio=None, estado=Turno.Estado.CONFIRMADO,
                     servicio=None, profesional=None, sucursal=None):
        servicio = servicio or self.servicio
        inicio = inicio or _proximo_dia_habil()
        return Turno.objects.create(
            sucursal=sucursal or servicio.sucursal,
            cliente=cliente or self.cliente_a,
            servicio=servicio,
            profesional=profesional or self.profesional,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=servicio.duracion_minutos),
            estado=estado,
            monto_total=servicio.precio,
        )


class ListadoTurnosTests(TurnosAppTestBase):
    def test_separa_proximos_de_historicos(self):
        futuro = self._crear_turno(inicio=_proximo_dia_habil(5))
        pasado = self._crear_turno(
            inicio=timezone.now() - timedelta(days=10), estado=Turno.Estado.COMPLETADO
        )

        self._auth(self.user_a)
        resp = self.client.get(reverse('client-turnos'))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([t['id'] for t in resp.data['proximos']], [futuro.id])
        self.assertEqual([t['id'] for t in resp.data['historicos']], [pasado.id])

    def test_turno_cancelado_a_futuro_va_al_historial(self):
        cancelado = self._crear_turno(
            inicio=_proximo_dia_habil(5), estado=Turno.Estado.CANCELADO
        )

        self._auth(self.user_a)
        resp = self.client.get(reverse('client-turnos'))

        self.assertEqual(resp.data['proximos'], [])
        self.assertEqual([t['id'] for t in resp.data['historicos']], [cancelado.id])

    def test_aislamiento_entre_usuarios(self):
        """Un usuario nunca ve los turnos de la ficha de otro."""
        mio = self._crear_turno(cliente=self.cliente_a)
        ajeno = self._crear_turno(
            cliente=self.cliente_b, servicio=self.servicio_b, profesional=self.profesional_b,
        )

        self._auth(self.user_a)
        resp = self.client.get(reverse('client-turnos'))
        ids = [t['id'] for t in resp.data['proximos']]

        self.assertIn(mio.id, ids)
        self.assertNotIn(ajeno.id, ids)

    def test_serializer_curado_no_expone_datos_internos(self):
        self._crear_turno()
        self._auth(self.user_a)
        resp = self.client.get(reverse('client-turnos'))

        turno = resp.data['proximos'][0]
        self.assertEqual(turno['servicio_nombre'], 'Limpieza facial')
        self.assertEqual(turno['profesional_nombre'], 'Ana Gómez')
        self.assertEqual(turno['centro_nombre'], 'Centro A')
        for campo_interno in ['creado_por', 'cliente', 'cliente_data', 'servicio_data']:
            self.assertNotIn(campo_interno, turno)

    def test_sin_auth_401(self):
        resp = self.client.get(reverse('client-turnos'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class DisponibilidadTests(TurnosAppTestBase):
    def _get_slots(self, fecha=None, servicio=None):
        fecha = fecha or (timezone.localdate() + timedelta(days=3))
        servicio = servicio or self.servicio
        return self.client.get(reverse('client-disponibilidad'), {
            'servicio': servicio.id,
            'fecha': fecha.isoformat(),
        })

    def test_devuelve_slots_del_horario_por_defecto(self):
        """Sin agenda cargada el profesional se asume 08:00-22:00 todos los días."""
        self._auth(self.user_a)
        resp = self._get_slots()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        horas = [s['hora'] for s in resp.data['slots']]
        self.assertEqual(horas[0], '08:00')
        self.assertIn('10:00', horas)
        # Servicio de 60 min con intervalo de 30 → el último arranca 21:00
        self.assertEqual(horas[-1], '21:00')

    def test_excluye_horarios_ocupados(self):
        inicio = _proximo_dia_habil()
        self._crear_turno(inicio=inicio)

        self._auth(self.user_a)
        resp = self._get_slots(fecha=timezone.localtime(inicio).date())
        horas = [s['hora'] for s in resp.data['slots']]

        # Turno 10:00-11:00 → se caen los solapados y se ofrece recién desde 11:00
        self.assertNotIn('09:30', horas)
        self.assertNotIn('10:00', horas)
        self.assertNotIn('10:30', horas)
        self.assertIn('11:00', horas)

    def test_respeta_dias_no_laborales(self):
        fecha = timezone.localdate() + timedelta(days=3)
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        self.profesional.dias_laborales = [d for d in dias if d != dias[fecha.weekday()]]
        self.profesional.save()

        self._auth(self.user_a)
        resp = self._get_slots(fecha=fecha)
        self.assertEqual(resp.data['slots'], [])

    def test_servicio_de_otro_centro_da_404(self):
        self._auth(self.user_a)
        resp = self._get_slots(servicio=self.servicio_b)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_fecha_pasada_sin_slots(self):
        self._auth(self.user_a)
        resp = self._get_slots(fecha=timezone.localdate() - timedelta(days=1))
        self.assertEqual(resp.data['slots'], [])

    def test_sin_auth_401(self):
        resp = self._get_slots()
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class ReservaTests(TurnosAppTestBase):
    def _reservar(self, inicio=None, servicio=None, **extra):
        return self.client.post(reverse('client-turnos'), {
            'servicio': (servicio or self.servicio).id,
            'fecha_hora_inicio': (inicio or _proximo_dia_habil()).isoformat(),
            **extra,
        }, format='json')

    def test_reserva_crea_turno_pendiente_con_profesional_asignado(self):
        inicio = _proximo_dia_habil()
        self._auth(self.user_a)
        resp = self._reservar(inicio=inicio, notas='Primera vez')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        turno = Turno.objects.get(pk=resp.data['id'])
        self.assertEqual(turno.cliente, self.cliente_a)
        self.assertEqual(turno.estado, Turno.Estado.PENDIENTE)
        self.assertEqual(turno.profesional, self.profesional)
        self.assertEqual(turno.sucursal, self.sucursal_a)
        self.assertEqual(turno.monto_total, self.servicio.precio)
        self.assertEqual(turno.fecha_hora_fin, inicio + timedelta(minutes=60))
        # Reservado por el cliente: no hay empleado que lo haya cargado
        self.assertIsNone(turno.creado_por)

    def test_no_permite_doble_reserva_del_mismo_horario(self):
        inicio = _proximo_dia_habil()
        self._crear_turno(inicio=inicio)

        self._auth(self.user_a)
        resp = self._reservar(inicio=inicio)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Turno.objects.filter(fecha_hora_inicio=inicio).count(), 1)

    def test_reserva_solapada_parcialmente_tambien_se_rechaza(self):
        inicio = _proximo_dia_habil()
        self._crear_turno(inicio=inicio)  # 10:00-11:00

        self._auth(self.user_a)
        resp = self._reservar(inicio=inicio + timedelta(minutes=30))  # 10:30-11:30

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_horario_fuera_de_la_jornada_se_rechaza(self):
        fecha = timezone.localdate() + timedelta(days=3)
        madrugada = timezone.make_aware(timezone.datetime.combine(fecha, time(3, 0)))

        self._auth(self.user_a)
        resp = self._reservar(inicio=madrugada)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_permite_reservar_en_el_pasado(self):
        self._auth(self.user_a)
        resp = self._reservar(inicio=timezone.now() - timedelta(days=1))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_permite_reservar_demasiado_a_futuro(self):
        self._auth(self.user_a)
        resp = self._reservar(inicio=_proximo_dia_habil(DIAS_MAXIMOS_A_FUTURO + 5))

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Turno.objects.exists())

    def test_no_permite_reservar_servicio_de_otro_centro(self):
        self._auth(self.user_a)
        resp = self._reservar(servicio=self.servicio_b)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Turno.objects.filter(servicio=self.servicio_b).exists())

    def test_sin_auth_401(self):
        resp = self._reservar()
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class CancelacionTests(TurnosAppTestBase):
    def _cancelar(self, turno):
        return self.client.post(reverse('client-cancelar-turno', args=[turno.id]))

    def test_cancela_turno_propio_con_antelacion(self):
        turno = self._crear_turno(inicio=_proximo_dia_habil(5))

        self._auth(self.user_a)
        resp = self._cancelar(turno)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.CANCELADO)

    def test_libera_el_horario_para_otra_reserva(self):
        inicio = _proximo_dia_habil(5)
        turno = self._crear_turno(inicio=inicio)

        self._auth(self.user_a)
        self._cancelar(turno)
        resp = self.client.post(reverse('client-turnos'), {
            'servicio': self.servicio.id,
            'fecha_hora_inicio': inicio.isoformat(),
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_no_cancela_con_menos_de_24_horas(self):
        turno = self._crear_turno(inicio=timezone.now() + timedelta(hours=5))

        self._auth(self.user_a)
        resp = self._cancelar(turno)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.CONFIRMADO)

    def test_no_cancela_turno_ajeno(self):
        ajeno = self._crear_turno(
            cliente=self.cliente_b, servicio=self.servicio_b,
            profesional=self.profesional_b, inicio=_proximo_dia_habil(5),
        )

        self._auth(self.user_a)
        resp = self._cancelar(ajeno)

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        ajeno.refresh_from_db()
        self.assertEqual(ajeno.estado, Turno.Estado.CONFIRMADO)

    def test_no_cancela_turno_ya_completado(self):
        turno = self._crear_turno(
            inicio=timezone.now() - timedelta(days=2), estado=Turno.Estado.COMPLETADO
        )

        self._auth(self.user_a)
        resp = self._cancelar(turno)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_auth_401(self):
        turno = self._crear_turno(inicio=_proximo_dia_habil(5))
        resp = self._cancelar(turno)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

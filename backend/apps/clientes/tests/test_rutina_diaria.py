"""
Tests de la rutina diaria: qué toca hoy, el check-in, la racha y la edición desde el CRM.

Lo que se cuida acá es que la historia de la clienta no se mueva sola: ni cuando
el staff edita la rutina, ni cuando pasan los días.
"""
from datetime import date, timedelta
from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.clientes import rutina_diaria
from apps.clientes.models import (
    Cliente,
    RutinaCuidado,
    RutinaDiaCumplido,
    RutinaItem,
    RutinaPasoHecho,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.empleados.models import CentroEstetica, Usuario
from apps.notificaciones.models import Aviso, PreferenciaNotificacion

# Viernes 16 de octubre de 2026.
VIERNES = date(2026, 10, 16)
DIURNA = RutinaItem.Momento.DIURNA
NOCTURNA = RutinaItem.Momento.NOCTURNA


class RutinaBase(APITestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(nombre='AME', telefono='1', email='ame@test.local')
        self.cliente = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Martina', apellido='Paz', telefono='11',
        )
        self.rutina = RutinaCuidado.objects.create(cliente=self.cliente, activa=True)
        self.limpieza = self._paso(DIURNA, 'Limpieza')
        self.protector = self._paso(DIURNA, 'Protector')
        self.desmaquillante = self._paso(NOCTURNA, 'Doble limpieza')
        # Martes (1) y viernes (4).
        self.exfoliante = self._paso(NOCTURNA, 'Exfoliante', dias=[1, 4])

    def _paso(self, momento, paso, dias=None):
        orden = self.rutina.items.filter(momento=momento).count() + 1
        return RutinaItem.objects.create(
            rutina=self.rutina, momento=momento, orden=orden, paso=paso, dias=dias or [],
        )

    def _cumplir(self, fecha, momento=DIURNA):
        RutinaDiaCumplido.objects.create(cliente=self.cliente, fecha=fecha, momento=momento)


class PasosDelDiaTests(RutinaBase):

    def test_un_paso_sin_dias_va_todos_los_dias(self):
        for i in range(7):
            self.assertTrue(self.limpieza.va_el(VIERNES + timedelta(days=i)))

    def test_un_paso_con_dias_va_solo_esos_dias(self):
        self.assertTrue(self.exfoliante.va_el(VIERNES))
        self.assertFalse(self.exfoliante.va_el(VIERNES + timedelta(days=1)))

    def test_los_de_hoy_respetan_el_momento(self):
        sabado = VIERNES + timedelta(days=1)
        self.assertEqual(
            rutina_diaria.pasos_del_dia(self.rutina, sabado, NOCTURNA), [self.desmaquillante]
        )


class MarcarPasoTests(RutinaBase):

    def test_completar_todos_los_pasos_del_momento_lo_da_por_cumplido(self):
        self.assertFalse(rutina_diaria.marcar_paso(self.rutina, self.limpieza, True, fecha=VIERNES))
        self.assertTrue(rutina_diaria.marcar_paso(self.rutina, self.protector, True, fecha=VIERNES))

        self.assertTrue(
            RutinaDiaCumplido.objects.filter(cliente=self.cliente, fecha=VIERNES, momento=DIURNA).exists()
        )

    def test_destildar_un_paso_deshace_el_cumplimiento(self):
        rutina_diaria.marcar_paso(self.rutina, self.limpieza, True, fecha=VIERNES)
        rutina_diaria.marcar_paso(self.rutina, self.protector, True, fecha=VIERNES)

        rutina_diaria.marcar_paso(self.rutina, self.protector, False, fecha=VIERNES)

        self.assertFalse(RutinaDiaCumplido.objects.exists())

    def test_marcar_dos_veces_no_duplica(self):
        rutina_diaria.marcar_paso(self.rutina, self.limpieza, True, fecha=VIERNES)
        rutina_diaria.marcar_paso(self.rutina, self.limpieza, True, fecha=VIERNES)

        self.assertEqual(RutinaPasoHecho.objects.count(), 1)

    def test_el_paso_que_hoy_no_toca_no_hace_falta_para_cumplir(self):
        sabado = VIERNES + timedelta(days=1)

        self.assertTrue(rutina_diaria.marcar_paso(self.rutina, self.desmaquillante, True, fecha=sabado))

    def test_no_se_puede_marcar_un_paso_que_hoy_no_toca(self):
        with self.assertRaises(rutina_diaria.PasoInvalido):
            rutina_diaria.marcar_paso(self.rutina, self.exfoliante, True, fecha=VIERNES + timedelta(days=1))

    def test_no_se_puede_marcar_un_paso_de_otra_rutina(self):
        otra = RutinaCuidado.objects.create(cliente=self.cliente, activa=False)
        ajeno = RutinaItem.objects.create(rutina=otra, momento=DIURNA, paso='Ajeno')

        with self.assertRaises(rutina_diaria.PasoInvalido):
            rutina_diaria.marcar_paso(self.rutina, ajeno, True, fecha=VIERNES)


class RachaTests(RutinaBase):

    def test_cuenta_los_dias_seguidos_hasta_hoy(self):
        for i in range(3):
            self._cumplir(VIERNES - timedelta(days=i))

        self.assertEqual(rutina_diaria.racha(self.cliente, VIERNES), 3)

    def test_si_hoy_todavia_no_la_hizo_cuenta_hasta_ayer(self):
        self._cumplir(VIERNES - timedelta(days=1))
        self._cumplir(VIERNES - timedelta(days=2))

        self.assertEqual(rutina_diaria.racha(self.cliente, VIERNES), 2)

    def test_un_dia_salteado_la_corta(self):
        self._cumplir(VIERNES)
        self._cumplir(VIERNES - timedelta(days=2))

        self.assertEqual(rutina_diaria.racha(self.cliente, VIERNES), 1)

    def test_alcanza_con_uno_de_los_dos_momentos(self):
        self._cumplir(VIERNES, NOCTURNA)
        self._cumplir(VIERNES - timedelta(days=1), DIURNA)

        self.assertEqual(rutina_diaria.racha(self.cliente, VIERNES), 2)

    def test_la_semana_va_de_lunes_a_domingo(self):
        self._cumplir(VIERNES - timedelta(days=4))  # lunes
        self._cumplir(VIERNES)

        semana = rutina_diaria.estado_del_dia(self.rutina, VIERNES)['semana']

        self.assertEqual(semana[0]['fecha'], '2026-10-12')
        self.assertEqual([d['cumplido'] for d in semana], [True, False, False, False, True, False, False])


class EdicionDesdeElCrmTests(RutinaBase):

    def setUp(self):
        super().setUp()
        self.staff = Usuario.objects.create_user(
            username='staff', password='x', centro_estetica=self.centro, rol=Usuario.Rol.EMPLEADO,
        )
        self.client.force_authenticate(self.staff)
        self.url = reverse('rutina-cuidado-detail', args=[self.rutina.id])

    def _items(self):
        return [
            {'id': i.id, 'momento': i.momento, 'orden': i.orden, 'paso': i.paso, 'dias': i.dias}
            for i in self.rutina.items.all()
        ]

    def test_editar_conserva_los_pasos_y_lo_que_ya_tildo_hoy(self):
        RutinaPasoHecho.objects.create(item=self.limpieza, fecha=VIERNES)
        items = self._items()
        items[0]['nota'] = 'Con agua tibia'
        items.append({'momento': NOCTURNA, 'orden': 3, 'paso': 'Crema'})

        resp = self.client.patch(self.url, {'items': items}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.limpieza.refresh_from_db()
        self.assertEqual(self.limpieza.nota, 'Con agua tibia')
        self.assertTrue(RutinaPasoHecho.objects.filter(item=self.limpieza).exists())
        self.assertEqual(self.rutina.items.count(), 5)

    def test_los_pasos_que_no_vienen_se_borran(self):
        items = [i for i in self._items() if i['id'] != self.protector.id]

        self.client.patch(self.url, {'items': items}, format='json')

        self.assertFalse(RutinaItem.objects.filter(id=self.protector.id).exists())

    def test_un_id_de_otra_rutina_crea_un_paso_nuevo(self):
        otra = RutinaCuidado.objects.create(cliente=self.cliente, activa=False)
        ajeno = RutinaItem.objects.create(rutina=otra, momento=DIURNA, paso='Ajeno')

        self.client.patch(
            self.url, {'items': [{'id': ajeno.id, 'momento': DIURNA, 'paso': 'Copiado'}]}, format='json',
        )

        ajeno.refresh_from_db()
        self.assertEqual(ajeno.paso, 'Ajeno')
        self.assertEqual(list(self.rutina.items.values_list('paso', flat=True)), ['Copiado'])

    def test_los_siete_dias_se_guardan_como_todos_los_dias(self):
        items = self._items()
        items[0]['dias'] = [6, 0, 1, 2, 3, 4, 5]
        items[1]['dias'] = [4, 1, 1]

        self.client.patch(self.url, {'items': items}, format='json')

        self.limpieza.refresh_from_db()
        self.protector.refresh_from_db()
        self.assertEqual(self.limpieza.dias, [])
        self.assertEqual(self.protector.dias, [1, 4])

    def test_un_dia_fuera_de_rango_se_rechaza(self):
        items = self._items()
        items[0]['dias'] = [7]

        resp = self.client.patch(self.url, {'items': items}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_la_rutina_activa_trae_la_constancia(self):
        self._cumplir(VIERNES)
        with mock.patch('django.utils.timezone.localdate', return_value=VIERNES):
            resp = self.client.get(self.url)

        self.assertEqual(resp.data['constancia']['cumplidos'], 1)
        self.assertEqual(resp.data['constancia']['racha'], 1)
        self.assertEqual(len(resp.data['constancia']['ultimos']), 7)


class RecordatorioDePruebaTests(RutinaBase):

    def setUp(self):
        super().setUp()
        self.staff = Usuario.objects.create_user(
            username='staff', password='x', centro_estetica=self.centro, rol=Usuario.Rol.EMPLEADO,
        )
        self.client.force_authenticate(self.staff)
        self.url = reverse('rutina-cuidado-recordatorio-prueba', args=[self.rutina.id])

    def _vincular(self):
        usuario = UsuarioCliente.objects.create_user(email='martina@mail.com', password='Secreta123!')
        VinculacionCliente.objects.create(
            usuario_cliente=usuario, cliente=self.cliente,
            metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
        )
        return usuario

    def test_manda_el_aviso_del_momento_pedido(self):
        self._vincular()

        resp = self.client.post(self.url, {'momento': NOCTURNA}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(Aviso.objects.get().titulo, 'Tu rutina de la noche')

    def test_sin_cuenta_en_la_app_avisa_por_que_no_sale(self):
        resp = self.client.post(self.url, {'momento': NOCTURNA}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no tiene cuenta', str(resp.data['detail']))

    def test_si_apago_mi_rutina_no_sale(self):
        usuario = self._vincular()
        PreferenciaNotificacion.objects.create(usuario_cliente=usuario, categoria='RUTINA', habilitada=False)

        resp = self.client.post(self.url, {'momento': DIURNA}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Aviso.objects.count(), 0)

    def test_no_se_puede_con_la_rutina_de_otro_centro(self):
        otro = CentroEstetica.objects.create(nombre='Otro', telefono='2', email='otro@test.local')
        ajena = Usuario.objects.create_user(
            username='ajena', password='x', centro_estetica=otro, rol=Usuario.Rol.ADMIN,
        )
        self.client.force_authenticate(ajena)

        resp = self.client.post(self.url, {'momento': DIURNA}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

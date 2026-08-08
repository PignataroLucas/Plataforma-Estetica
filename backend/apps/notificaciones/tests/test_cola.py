"""
Tests de la cola: envío, multi-dispositivo, reintentos y limpieza de tokens.

Nada de esto sale a la red: se sustituye el canal por un doble y se verifica lo
que la cola decide, que es lo propio del sistema.
"""
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from apps.notificaciones import cola, despacho, eventos
from apps.notificaciones.canales import Resultado
from apps.notificaciones.models import Aviso, DispositivoPush, EnvioPush

from .base import CanalFalso, NotificacionesTestBase


class ColaTests(NotificacionesTestBase):

    def setUp(self):
        super().setUp()
        self.canal = CanalFalso()
        # Se parchea el selector, no un atributo del módulo: la cola resuelve el
        # canal en cada llamada para que se pueda cambiar por configuración.
        parche = patch('apps.notificaciones.canales.activo', return_value=self.canal)
        parche.start()
        self.addCleanup(parche.stop)

    def _crear_aviso(self, **kwargs):
        kwargs.setdefault('evento', eventos.TURNO_CONFIRMADO)
        kwargs.setdefault('usuario_cliente', self.usuario)
        return despacho.crear_aviso(**kwargs)

    # ---------- Camino feliz ----------

    def test_manda_el_aviso_y_lo_marca_enviado(self):
        self.crear_dispositivo()
        aviso = self._crear_aviso()

        resumen = cola.procesar_pendientes()

        self.assertEqual(resumen['enviados'], 1)
        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.ENVIADO)
        self.assertIsNotNone(aviso.enviado_en)
        self.assertEqual(len(self.canal.enviados), 1)

    def test_el_mensaje_lleva_la_ruta_y_el_id_del_aviso(self):
        self.crear_dispositivo()
        self._crear_aviso()
        cola.procesar_pendientes()

        datos = self.canal.enviados[0].datos
        self.assertEqual(datos['ruta'], '/turnos')
        self.assertIn('avisoId', datos)

    def test_el_canal_de_android_es_la_categoria(self):
        """Deja silenciar promociones desde el sistema operativo sin perder turnos."""
        self.crear_dispositivo()
        self._crear_aviso(evento=eventos.OFERTA_NUEVA)
        cola.procesar_pendientes()
        self.assertEqual(self.canal.enviados[0].canal_android, 'promociones')

    def test_una_cuenta_con_dos_telefonos_recibe_en_los_dos(self):
        self.crear_dispositivo(token='ExponentPushToken[viejo]')
        self.crear_dispositivo(token='ExponentPushToken[nuevo]')
        aviso = self._crear_aviso()

        cola.procesar_pendientes()

        self.assertEqual(len(self.canal.enviados), 2)
        self.assertEqual(EnvioPush.objects.filter(aviso=aviso).count(), 2)

    def test_un_dispositivo_de_baja_no_recibe(self):
        activo = self.crear_dispositivo(token='ExponentPushToken[activo]')
        self.crear_dispositivo(token='ExponentPushToken[baja]').dar_de_baja(
            DispositivoPush.MotivoBaja.SESION_CERRADA
        )
        self._crear_aviso()

        cola.procesar_pendientes()

        self.assertEqual(len(self.canal.enviados), 1)
        self.assertEqual(self.canal.enviados[0].destino, activo.token)

    # ---------- Sin destino ----------

    def test_sin_dispositivos_queda_marcado_y_no_se_reintenta(self):
        aviso = self._crear_aviso()

        resumen = cola.procesar_pendientes()

        self.assertEqual(resumen['sin_destino'], 1)
        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.SIN_DESTINO)
        self.assertEqual(len(self.canal.enviados), 0)

    # ---------- No se manda antes de tiempo ----------

    def test_un_aviso_programado_a_futuro_no_sale_todavia(self):
        self.crear_dispositivo()
        aviso = self._crear_aviso(programado_para=timezone.now() + timedelta(hours=5))

        cola.procesar_pendientes()

        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.PENDIENTE)
        self.assertEqual(len(self.canal.enviados), 0)

    # ---------- Errores ----------

    def test_un_token_muerto_se_da_de_baja_solo(self):
        dispositivo = self.crear_dispositivo()
        self.canal.respuesta = lambda m, i: Resultado(
            destino=m.destino, ok=False, error='DeviceNotRegistered',
            destino_muerto=True,
        )
        aviso = self._crear_aviso()

        cola.procesar_pendientes()

        dispositivo.refresh_from_db()
        self.assertFalse(dispositivo.activo)
        self.assertEqual(dispositivo.motivo_baja, DispositivoPush.MotivoBaja.TOKEN_MUERTO)
        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.FALLIDO)

    def test_un_error_pasajero_se_reintenta_y_despues_se_rinde(self):
        self.crear_dispositivo()
        self.canal.respuesta = lambda m, i: Resultado(
            destino=m.destino, ok=False, error='Se cayó la red', reintentable=True,
        )
        aviso = self._crear_aviso()

        cola.procesar_pendientes()
        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.PENDIENTE)
        self.assertEqual(aviso.intentos, 1)

        cola.procesar_pendientes()
        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.PENDIENTE)
        self.assertEqual(aviso.intentos, 2)

        # Tercer intento: se agota y deja de ocupar la cola.
        cola.procesar_pendientes()
        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.FALLIDO)
        self.assertEqual(aviso.intentos, 3)

    def test_alcanza_con_que_llegue_a_un_telefono(self):
        """Si el token viejo murió pero el nuevo recibió, el aviso salió."""
        self.crear_dispositivo(token='ExponentPushToken[muerto]')
        self.crear_dispositivo(token='ExponentPushToken[vivo]')
        self.canal.respuesta = lambda m, i: (
            Resultado(destino=m.destino, ok=False, error='DeviceNotRegistered',
                      destino_muerto=True)
            if 'muerto' in m.destino
            else Resultado(destino=m.destino, ok=True, ticket_id='t1')
        )
        aviso = self._crear_aviso()

        cola.procesar_pendientes()

        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.ENVIADO)
        self.assertEqual(
            DispositivoPush.objects.filter(activo=True).count(), 1
        )

    # ---------- Concurrencia y recuperación ----------

    def test_una_segunda_corrida_no_reenvia_lo_ya_tomado(self):
        self.crear_dispositivo()
        aviso = self._crear_aviso()
        Aviso.objects.filter(id=aviso.id).update(estado=Aviso.Estado.PROCESANDO)

        resumen = cola.procesar_pendientes()

        self.assertEqual(resumen['tomados'], 0)
        self.assertEqual(len(self.canal.enviados), 0)

    def test_un_aviso_colgado_vuelve_a_la_cola(self):
        self.crear_dispositivo()
        aviso = self._crear_aviso()
        viejo = timezone.now() - timedelta(minutes=cola.MINUTOS_PARA_RESCATAR + 5)
        Aviso.objects.filter(id=aviso.id).update(estado=Aviso.Estado.PROCESANDO)
        Aviso.objects.filter(id=aviso.id).update(creado_en=viejo)

        resumen = cola.procesar_pendientes()

        self.assertEqual(resumen['rescatados'], 1)
        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.ENVIADO)

    # ---------- Recibos ----------

    def test_el_recibo_confirma_la_entrega(self):
        self.crear_dispositivo()
        self._crear_aviso()
        cola.procesar_pendientes()

        envio = EnvioPush.objects.get()
        self.assertEqual(envio.estado, EnvioPush.Estado.ACEPTADO)
        EnvioPush.objects.filter(id=envio.id).update(
            creado_en=timezone.now() - timedelta(minutes=30)
        )
        self.canal.recibos = {envio.ticket_id: Resultado(destino='', ok=True)}

        resumen = cola.procesar_recibos()

        self.assertEqual(resumen['entregados'], 1)
        envio.refresh_from_db()
        self.assertEqual(envio.estado, EnvioPush.Estado.ENTREGADO)

    def test_el_recibo_tambien_detecta_la_app_desinstalada(self):
        dispositivo = self.crear_dispositivo()
        self._crear_aviso()
        cola.procesar_pendientes()

        envio = EnvioPush.objects.get()
        EnvioPush.objects.filter(id=envio.id).update(
            creado_en=timezone.now() - timedelta(minutes=30)
        )
        self.canal.recibos = {
            envio.ticket_id: Resultado(
                destino='', ok=False, error='DeviceNotRegistered', destino_muerto=True
            )
        }

        cola.procesar_recibos()

        dispositivo.refresh_from_db()
        self.assertFalse(dispositivo.activo)

    def test_no_se_pide_el_recibo_antes_de_los_15_minutos(self):
        self.crear_dispositivo()
        self._crear_aviso()
        cola.procesar_pendientes()

        resumen = cola.procesar_recibos()

        self.assertEqual(resumen['consultados'], 0)
        self.assertEqual(self.canal.recibos_pedidos, [])

    def test_pasadas_24h_se_deja_de_esperar_el_recibo(self):
        self.crear_dispositivo()
        self._crear_aviso()
        cola.procesar_pendientes()

        envio = EnvioPush.objects.get()
        EnvioPush.objects.filter(id=envio.id).update(
            creado_en=timezone.now() - timedelta(hours=25)
        )

        resumen = cola.procesar_recibos()

        self.assertEqual(resumen['sin_recibo'], 1)
        self.assertEqual(resumen['consultados'], 0)
        envio.refresh_from_db()
        self.assertIsNotNone(envio.confirmado_en)

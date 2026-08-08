"""
Tests de la selección de canal y del canal de simulación.

Lo importante acá es que simular no sea un camino aparte: la cola tiene que
comportarse igual con el canal de consola que con el real, para que probar con
uno diga algo sobre el otro.
"""
from django.test import override_settings

from apps.notificaciones import canales, cola, despacho, eventos
from apps.notificaciones.canales import MensajeSaliente, consola, expo
from apps.notificaciones.models import Aviso, EnvioPush

from .base import NotificacionesTestBase


class SeleccionDeCanalTests(NotificacionesTestBase):

    @override_settings(NOTIFICACIONES_CANAL='expo')
    def test_elige_expo(self):
        self.assertIs(canales.activo(), expo)

    @override_settings(NOTIFICACIONES_CANAL='consola')
    def test_elige_consola(self):
        self.assertIs(canales.activo(), consola)

    @override_settings(NOTIFICACIONES_CANAL='inventado')
    def test_un_canal_inexistente_falla_claro(self):
        with self.assertRaises(ValueError) as ctx:
            canales.activo()
        self.assertIn('inventado', str(ctx.exception))

    def test_se_resuelve_en_cada_llamada(self):
        """Si se resolviera al importar, override_settings no tendría efecto."""
        with override_settings(NOTIFICACIONES_CANAL='consola'):
            self.assertIs(canales.activo(), consola)
        with override_settings(NOTIFICACIONES_CANAL='expo'):
            self.assertIs(canales.activo(), expo)


class CanalConsolaTests(NotificacionesTestBase):

    def test_acepta_todo_y_respeta_el_orden(self):
        mensajes = [
            MensajeSaliente(destino=f'ExponentPushToken[{i}]', titulo=f'T{i}', cuerpo='c')
            for i in range(5)
        ]
        resultados = consola.enviar(mensajes)

        self.assertEqual(len(resultados), len(mensajes))
        self.assertTrue(all(r.ok for r in resultados))
        self.assertEqual(
            [r.destino for r in resultados], [m.destino for m in mensajes]
        )

    def test_los_tickets_son_distintos(self):
        """La cola guarda el ticket por envío: repetirlos rompería los recibos."""
        mensajes = [
            MensajeSaliente(destino='ExponentPushToken[x]', titulo='T', cuerpo='c')
            for _ in range(3)
        ]
        tickets = {r.ticket_id for r in consola.enviar(mensajes)}
        self.assertEqual(len(tickets), 3)

    def test_sin_mensajes_no_devuelve_nada(self):
        self.assertEqual(consola.enviar([]), [])

    def test_da_todos_los_recibos_por_entregados(self):
        recibos = consola.consultar_recibos(['a', 'b'])
        self.assertEqual(set(recibos), {'a', 'b'})
        self.assertTrue(all(r.ok for r in recibos.values()))


@override_settings(NOTIFICACIONES_CANAL='consola')
class ColaConCanalDeConsolaTests(NotificacionesTestBase):
    """La tubería entera, sin red, tal como corre en la máquina de desarrollo."""

    def test_un_aviso_llega_a_enviado_sin_salir_a_internet(self):
        self.crear_dispositivo()
        aviso = despacho.crear_aviso(
            evento=eventos.CUMPLEANOS,
            usuario_cliente=self.usuario,
            centro_estetica=self.centro,
            contexto={'nombre': 'Sofía', 'centro': 'AME'},
        )

        resumen = cola.procesar_pendientes()

        self.assertEqual(resumen['enviados'], 1)
        aviso.refresh_from_db()
        self.assertEqual(aviso.estado, Aviso.Estado.ENVIADO)
        self.assertEqual(EnvioPush.objects.get().estado, EnvioPush.Estado.ACEPTADO)

    def test_sin_dispositivo_tambien_se_comporta_igual(self):
        despacho.crear_aviso(evento=eventos.CUMPLEANOS, usuario_cliente=self.usuario)

        resumen = cola.procesar_pendientes()

        self.assertEqual(resumen['sin_destino'], 1)
        self.assertEqual(EnvioPush.objects.count(), 0)

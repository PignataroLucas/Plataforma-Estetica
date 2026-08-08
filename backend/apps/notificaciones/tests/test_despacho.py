"""
Reglas de creación de avisos: preferencias, plantillas e idempotencia.

Son las tres cosas que no queremos que cada llamador reimplemente, así que se
prueban acá una vez y en profundidad.
"""
from django.utils import timezone

from apps.notificaciones import despacho, eventos
from apps.notificaciones.models import Aviso, PlantillaNotificacion, PreferenciaNotificacion

from .base import NotificacionesTestBase


class DespachoTests(NotificacionesTestBase):

    def test_crea_el_aviso_con_el_texto_del_catalogo(self):
        aviso = despacho.crear_aviso(
            evento=eventos.TURNO_CONFIRMADO,
            usuario_cliente=self.usuario,
            centro_estetica=self.centro,
            contexto={'servicio': 'Limpieza facial', 'fecha': '12 de agosto', 'hora': '15:00'},
        )
        self.assertEqual(aviso.titulo, 'Turno confirmado')
        self.assertIn('Limpieza facial', aviso.cuerpo)
        self.assertIn('15:00', aviso.cuerpo)
        self.assertEqual(aviso.estado, Aviso.Estado.PENDIENTE)
        self.assertEqual(aviso.datos['ruta'], '/turnos')

    def test_la_plantilla_del_centro_le_gana_al_catalogo(self):
        PlantillaNotificacion.objects.create(
            centro_estetica=self.centro,
            evento=eventos.TURNO_CONFIRMADO,
            titulo='Listo, {servicio}',
            cuerpo='Nos vemos el {fecha}.',
        )
        aviso = despacho.crear_aviso(
            evento=eventos.TURNO_CONFIRMADO,
            usuario_cliente=self.usuario,
            centro_estetica=self.centro,
            contexto={'servicio': 'Peeling', 'fecha': '12 de agosto'},
        )
        self.assertEqual(aviso.titulo, 'Listo, Peeling')
        self.assertEqual(aviso.cuerpo, 'Nos vemos el 12 de agosto.')

    def test_una_plantilla_desactivada_vuelve_al_texto_por_defecto(self):
        PlantillaNotificacion.objects.create(
            centro_estetica=self.centro,
            evento=eventos.TURNO_CONFIRMADO,
            titulo='No debería verse',
            cuerpo='Tampoco esto',
            activa=False,
        )
        aviso = despacho.crear_aviso(
            evento=eventos.TURNO_CONFIRMADO,
            usuario_cliente=self.usuario,
            centro_estetica=self.centro,
        )
        self.assertEqual(aviso.titulo, 'Turno confirmado')

    def test_una_variable_que_falta_no_deja_llaves_a_la_vista(self):
        aviso = despacho.crear_aviso(
            evento=eventos.CUMPLEANOS,
            usuario_cliente=self.usuario,
            contexto={'nombre': 'Sofía'},  # falta {centro}
        )
        self.assertNotIn('{', aviso.titulo + aviso.cuerpo)

    # ---------- Preferencias ----------

    def test_no_se_crea_si_la_categoria_esta_apagada(self):
        PreferenciaNotificacion.objects.create(
            usuario_cliente=self.usuario,
            categoria=eventos.Categoria.PROMOCIONES,
            habilitada=False,
        )
        aviso = despacho.crear_aviso(
            evento=eventos.OFERTA_NUEVA, usuario_cliente=self.usuario
        )
        self.assertIsNone(aviso)
        self.assertEqual(Aviso.objects.count(), 0)

    def test_un_aviso_transaccional_ignora_la_preferencia(self):
        """Apagar 'Turnos' silencia recordatorios, no que te cancelen el turno."""
        PreferenciaNotificacion.objects.create(
            usuario_cliente=self.usuario,
            categoria=eventos.Categoria.TURNOS,
            habilitada=False,
        )
        cancelacion = despacho.crear_aviso(
            evento=eventos.TURNO_CANCELADO, usuario_cliente=self.usuario
        )
        recordatorio = despacho.crear_aviso(
            evento=eventos.TURNO_RECORDATORIO_24H, usuario_cliente=self.usuario
        )
        self.assertIsNotNone(cancelacion)
        self.assertIsNone(recordatorio)

    # ---------- Idempotencia ----------

    def test_la_misma_clave_no_entra_dos_veces(self):
        for _ in range(3):
            despacho.crear_aviso(
                evento=eventos.TURNO_RECORDATORIO_24H,
                usuario_cliente=self.usuario,
                clave='turno:1:recordatorio_24h',
            )
        self.assertEqual(Aviso.objects.count(), 1)

    def test_sin_clave_se_puede_repetir(self):
        for _ in range(3):
            despacho.crear_aviso(
                evento=eventos.OFERTA_NUEVA, usuario_cliente=self.usuario
            )
        self.assertEqual(Aviso.objects.count(), 3)

    def test_la_clave_no_bloquea_a_otra_cuenta_de_la_misma_ficha(self):
        """Una ficha compartida entre dos cuentas tiene que avisarle a las dos."""
        from apps.clientes.models import UsuarioCliente, VinculacionCliente

        otra = UsuarioCliente.objects.create_user(email='mama@mail.com', password='Secreta123!')
        VinculacionCliente.objects.create(
            usuario_cliente=otra, cliente=self.cliente,
            metodo_vinculacion=VinculacionCliente.Metodo.INVITACION_STAFF,
        )

        avisos = despacho.crear_aviso_para_cliente(
            evento=eventos.TURNO_RECORDATORIO_24H,
            cliente=self.cliente,
            clave='turno:1:recordatorio_24h',
        )
        self.assertEqual(len(avisos), 2)

        # Y correr de nuevo no duplica ninguno de los dos.
        despacho.crear_aviso_para_cliente(
            evento=eventos.TURNO_RECORDATORIO_24H,
            cliente=self.cliente,
            clave='turno:1:recordatorio_24h',
        )
        self.assertEqual(Aviso.objects.count(), 2)

    def test_descartar_pendientes_libera_la_clave(self):
        """
        Un turno que se cancela y se reactiva tiene que poder recuperar su
        recordatorio: por eso los pendientes se borran en vez de cancelarse.
        """
        despacho.crear_aviso(
            evento=eventos.TURNO_RECORDATORIO_24H,
            usuario_cliente=self.usuario,
            clave='turno:7:recordatorio_24h',
        )
        borrados = despacho.descartar_pendientes(clave_prefijo='turno:7:')
        self.assertEqual(borrados, 1)

        de_nuevo = despacho.crear_aviso(
            evento=eventos.TURNO_RECORDATORIO_24H,
            usuario_cliente=self.usuario,
            clave='turno:7:recordatorio_24h',
        )
        self.assertIsNotNone(de_nuevo)

    def test_descartar_no_toca_lo_que_ya_salio(self):
        aviso = despacho.crear_aviso(
            evento=eventos.TURNO_RECORDATORIO_24H,
            usuario_cliente=self.usuario,
            clave='turno:8:recordatorio_24h',
        )
        Aviso.objects.filter(id=aviso.id).update(
            estado=Aviso.Estado.ENVIADO, enviado_en=timezone.now()
        )
        despacho.descartar_pendientes(clave_prefijo='turno:8:')
        self.assertTrue(Aviso.objects.filter(id=aviso.id).exists())

    # ---------- Masivo ----------

    def test_el_envio_masivo_saltea_a_quien_apago_la_categoria(self):
        from apps.clientes.models import UsuarioCliente

        otra = UsuarioCliente.objects.create_user(email='otra@mail.com', password='Secreta123!')
        PreferenciaNotificacion.objects.create(
            usuario_cliente=otra,
            categoria=eventos.Categoria.PROMOCIONES,
            habilitada=False,
        )

        despacho.crear_avisos_masivos(
            evento=eventos.OFERTA_NUEVA,
            usuarios=[self.usuario, otra],
            centro_estetica=self.centro,
            contexto={'centro': 'AME', 'oferta': '2x1 en faciales', 'vence': '30/8'},
            clave_base='oferta:5',
        )
        self.assertEqual(Aviso.objects.count(), 1)
        self.assertEqual(Aviso.objects.first().usuario_cliente, self.usuario)

    def test_el_envio_masivo_se_puede_reintentar_sin_duplicar(self):
        for _ in range(2):
            despacho.crear_avisos_masivos(
                evento=eventos.OFERTA_NUEVA,
                usuarios=[self.usuario],
                centro_estetica=self.centro,
                clave_base='oferta:5',
            )
        self.assertEqual(Aviso.objects.count(), 1)


class EventosTests(NotificacionesTestBase):

    def test_un_evento_inexistente_falla_temprano_y_claro(self):
        with self.assertRaises(ValueError) as ctx:
            eventos.obtener('evento_que_no_existe')
        self.assertIn('evento_que_no_existe', str(ctx.exception))

    def test_todos_los_eventos_tienen_categoria_valida(self):
        validas = {c for c, _ in eventos.Categoria.choices}
        for evento in eventos.EVENTOS.values():
            self.assertIn(evento.categoria, validas, evento.clave)

    def test_una_plantilla_rota_no_tumba_el_envio(self):
        self.assertEqual(eventos.renderizar('Hola {sin cerrar', {}), 'Hola {sin cerrar')

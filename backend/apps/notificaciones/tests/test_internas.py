"""
Tests de la bandeja del centro: los pedidos de turno que llegan desde la app.

Tres cosas se cuidan acá, y las tres son la diferencia entre un aviso que llega y
uno que se pierde en silencio:

1. **Que el aviso se cree solo cuando corresponde.** Un turno cargado en el CRM
   ya lo decidió quien lo cargó; uno que nace confirmado no tiene nada que
   resolver. Avisar de esos sería ruido, y el ruido hace que se deje de mirar la
   bandeja.
2. **Que reservar no espere a SES.** La señal escribe la fila y sigue; el mail lo
   manda el barrido. Si SES está caído la clienta reserva igual.
3. **Que un mail que falla se reintente y después se rinda.** Insistir para
   siempre con una dirección que no existe llena el log y no arregla nada.
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

from apps.notificaciones.correo import CorreoNoEnviado
from apps.notificaciones.internas import (
    MAX_INTENTOS,
    avisar_los_que_vencen,
    avisar_pedido_de_turno,
    enviar_pendientes,
    url_del_turno,
)
from apps.notificaciones.models import NotificacionInterna
from apps.turnos.models import Turno
from apps.turnos.services import reservar_turno

from .base import NotificacionesTestBase


class BandejaTestBase(NotificacionesTestBase):
    """
    La fixture compartida arma la sucursal sin email, así que sin esto todos los
    avisos nacerían `SIN_DESTINO` y el barrido no tomaría ninguno. Se configura
    acá y no en `base.py` para no cambiarle el escenario a los tests de push.
    """

    def setUp(self):
        super().setUp()
        self.sucursal.email_avisos = 'duenia@ame.com'
        self.sucursal.save()


class TestSeCreaElAviso(BandejaTestBase):

    def _reservar_desde_la_app(self, **extra):
        inicio = timezone.now() + timedelta(days=3)
        inicio = inicio.replace(hour=14, minute=0, second=0, microsecond=0)
        datos = {
            'cliente': self.cliente,
            'servicio': self.servicio,
            'inicio': inicio,
            'origen': Turno.Origen.APP,
            'estado': Turno.Estado.PENDIENTE,
        }
        datos.update(extra)
        return reservar_turno(**datos)

    def test_un_pedido_de_la_app_entra_a_la_bandeja(self):
        turno = self._reservar_desde_la_app()

        aviso = NotificacionInterna.objects.get(turno=turno)
        self.assertEqual(aviso.tipo, NotificacionInterna.Tipo.TURNO_SOLICITADO)
        self.assertEqual(aviso.sucursal, self.sucursal)
        self.assertEqual(
            aviso.email_estado, NotificacionInterna.EstadoEntrega.PENDIENTE
        )

    def test_un_turno_del_crm_no_avisa_a_nadie(self):
        """Lo cargó el staff: ya está decidido."""
        self._reservar_desde_la_app(origen=Turno.Origen.CRM)

        self.assertEqual(NotificacionInterna.objects.count(), 0)

    def test_un_turno_que_nace_confirmado_no_avisa(self):
        """Sin aprobación pendiente no hay nada que resolver."""
        self._reservar_desde_la_app(estado=Turno.Estado.CONFIRMADO)

        self.assertEqual(NotificacionInterna.objects.count(), 0)

    def test_el_cuerpo_trae_lo_que_hace_falta_para_decidir(self):
        turno = self._reservar_desde_la_app()

        cuerpo = NotificacionInterna.objects.get(turno=turno).cuerpo
        self.assertIn('Sofía Paz', cuerpo)
        self.assertIn('1155667788', cuerpo)
        self.assertIn('Limpieza facial', cuerpo)
        # El plazo: es lo que le dice al centro cuánta urgencia tiene.
        self.assertIn('Podés responder hasta', cuerpo)

    def test_un_profesional_sin_nombre_no_deja_una_linea_vacia(self):
        """
        `Profesional:` seguido de nada lee como un dato que falta, no como uno
        que no aplica. Pasó en la primera prueba contra datos reales.
        """
        self.profesional.first_name = ''
        self.profesional.last_name = ''
        self.profesional.save()

        turno = self._reservar_desde_la_app()

        cuerpo = NotificacionInterna.objects.get(turno=turno).cuerpo
        self.assertNotIn('Profesional:', cuerpo)

    def test_el_destinatario_se_congela_en_la_fila(self):
        """
        Si mañana cambia el mail de la sucursal, la fila vieja tiene que seguir
        diciendo a dónde se mandó.
        """
        self.sucursal.email_avisos = 'duenia@ame.com'
        self.sucursal.save()

        turno = self._reservar_desde_la_app()
        aviso = NotificacionInterna.objects.get(turno=turno)
        self.assertEqual(aviso.email_destino, 'duenia@ame.com')

        self.sucursal.email_avisos = 'otra@ame.com'
        self.sucursal.save()
        aviso.refresh_from_db()
        self.assertEqual(aviso.email_destino, 'duenia@ame.com')

    def test_sin_destinatario_configurado_no_se_intenta_mandar(self):
        """
        Reintentar un mail sin destino no lo va a arreglar. Queda visible en otro
        estado para que se note que falta configurarlo.
        """
        self.sucursal.email_avisos = ''
        self.sucursal.email = ''
        self.sucursal.save()

        turno = self._reservar_desde_la_app()
        aviso = NotificacionInterna.objects.get(turno=turno)
        self.assertEqual(
            aviso.email_estado, NotificacionInterna.EstadoEntrega.SIN_DESTINO
        )

    def test_reservar_no_espera_a_ses(self):
        """
        La señal no envía: escribe la fila y sigue. Si llamara a SES, la clienta
        esperaría la red para ver su turno confirmado en pantalla.
        """
        with patch('apps.notificaciones.internas.enviar_correo') as enviar:
            self._reservar_desde_la_app()

        enviar.assert_not_called()

    def test_el_mail_sale_en_el_acto_sin_esperar_al_cron(self):
        """
        Los minutos de espera salen del plazo que el centro tiene para
        responder. El barrido queda como red, no como camino.
        """
        with patch('apps.notificaciones.internas.enviar_correo') as enviar:
            with self.captureOnCommitCallbacks(execute=True):
                self._reservar_desde_la_app()

        enviar.assert_called_once()

    def test_si_ses_falla_la_reserva_queda_hecha_igual(self):
        """
        Que el mail no salga no puede tumbar la reserva de la clienta, que ya
        está confirmada del lado de ella.
        """
        with patch('apps.notificaciones.internas.enviar_correo',
                   side_effect=CorreoNoEnviado('SES caído')):
            with self.captureOnCommitCallbacks(execute=True):
                turno = self._reservar_desde_la_app()

        self.assertEqual(turno.estado, Turno.Estado.PENDIENTE)
        aviso = NotificacionInterna.objects.get(turno=turno)
        # Sigue pendiente: el barrido lo reintenta.
        self.assertEqual(
            aviso.email_estado, NotificacionInterna.EstadoEntrega.PENDIENTE
        )

    def test_el_mismo_pedido_no_entra_dos_veces(self):
        """La clave de idempotencia, igual que en los avisos a clientas."""
        turno = self._reservar_desde_la_app()

        self.assertIsNone(avisar_pedido_de_turno(turno))
        self.assertEqual(NotificacionInterna.objects.filter(turno=turno).count(), 1)


class TestElLinkDelMail(BandejaTestBase):

    @override_settings(CRM_URL='https://crm.ame.com')
    def test_con_crm_url_el_mail_lleva_el_link(self):
        # A `/pedidos`: es donde están los botones de aceptar y rechazar.
        self.assertEqual(url_del_turno(12), 'https://crm.ame.com/pedidos?turno=12')

    @override_settings(CRM_URL='')
    def test_sin_crm_url_el_mail_sale_igual_sin_link(self):
        """
        Un aviso sin link es mejor que ningún aviso. La variable se puede cargar
        después sin tocar código.
        """
        self.assertEqual(url_del_turno(12), '')

        inicio = timezone.now() + timedelta(days=3)
        turno = reservar_turno(
            cliente=self.cliente, servicio=self.servicio, inicio=inicio,
            origen=Turno.Origen.APP, estado=Turno.Estado.PENDIENTE,
        )
        cuerpo = NotificacionInterna.objects.get(turno=turno).cuerpo
        self.assertNotIn('Aceptarlo o rechazarlo', cuerpo)
        self.assertIn('Sofía Paz', cuerpo)


class TestElBarridoEnvia(BandejaTestBase):

    def _pedido_pendiente(self):
        inicio = timezone.now() + timedelta(days=3)
        turno = reservar_turno(
            cliente=self.cliente, servicio=self.servicio, inicio=inicio,
            origen=Turno.Origen.APP, estado=Turno.Estado.PENDIENTE,
        )
        return NotificacionInterna.objects.get(turno=turno)

    def test_manda_y_lo_marca(self):
        aviso = self._pedido_pendiente()

        with patch('apps.notificaciones.internas.enviar_correo') as enviar:
            resumen = enviar_pendientes()

        enviar.assert_called_once()
        self.assertEqual(resumen['internas_enviadas'], 1)

        aviso.refresh_from_db()
        self.assertEqual(aviso.email_estado, NotificacionInterna.EstadoEntrega.ENVIADO)
        self.assertIsNotNone(aviso.email_enviado_en)

    def test_no_lo_manda_dos_veces(self):
        self._pedido_pendiente()

        with patch('apps.notificaciones.internas.enviar_correo') as enviar:
            enviar_pendientes()
            enviar_pendientes()

        self.assertEqual(enviar.call_count, 1)

    def test_un_error_pasajero_se_reintenta(self):
        aviso = self._pedido_pendiente()

        with patch('apps.notificaciones.internas.enviar_correo',
                   side_effect=CorreoNoEnviado('SES tosió')):
            enviar_pendientes()

        aviso.refresh_from_db()
        # Sigue pendiente: todavía le quedan intentos.
        self.assertEqual(
            aviso.email_estado, NotificacionInterna.EstadoEntrega.PENDIENTE
        )
        self.assertEqual(aviso.email_intentos, 1)
        self.assertIn('SES tosió', aviso.email_error)

        with patch('apps.notificaciones.internas.enviar_correo') as enviar:
            enviar_pendientes()

        enviar.assert_called_once()
        aviso.refresh_from_db()
        self.assertEqual(aviso.email_estado, NotificacionInterna.EstadoEntrega.ENVIADO)

    def test_despues_de_varios_intentos_se_rinde(self):
        """Insistir para siempre con una dirección rota llena el log y no arregla."""
        aviso = self._pedido_pendiente()

        with patch('apps.notificaciones.internas.enviar_correo',
                   side_effect=CorreoNoEnviado('no existe')):
            for _ in range(MAX_INTENTOS + 2):
                enviar_pendientes()

        aviso.refresh_from_db()
        self.assertEqual(aviso.email_estado, NotificacionInterna.EstadoEntrega.FALLIDO)
        self.assertEqual(aviso.email_intentos, MAX_INTENTOS)

    def test_un_aviso_sin_destino_no_se_toma(self):
        self.sucursal.email_avisos = ''
        self.sucursal.email = ''
        self.sucursal.save()
        self._pedido_pendiente()

        with patch('apps.notificaciones.internas.enviar_correo') as enviar:
            enviar_pendientes()

        enviar.assert_not_called()

    def test_un_error_no_frena_al_resto_de_la_tanda(self):
        """Que un mail falle no puede dejar sin avisar a los demás pedidos."""
        primero = self._pedido_pendiente()
        inicio = timezone.now() + timedelta(days=4)
        otro_turno = reservar_turno(
            cliente=self.cliente, servicio=self.servicio, inicio=inicio,
            origen=Turno.Origen.APP, estado=Turno.Estado.PENDIENTE,
        )
        segundo = NotificacionInterna.objects.get(turno=otro_turno)

        # Falla el primero de la tanda, sea cual sea: los dos avisos son de la
        # misma clienta, así que el asunto no sirve para distinguirlos.
        llamadas = []

        def falla_el_primero(destinatario, asunto, cuerpo):
            llamadas.append(asunto)
            if len(llamadas) == 1:
                raise CorreoNoEnviado('el primero falla')

        with patch('apps.notificaciones.internas.enviar_correo',
                   side_effect=falla_el_primero):
            resumen = enviar_pendientes()

        self.assertEqual(resumen['internas_enviadas'], 1)
        self.assertEqual(resumen['internas_fallidas'], 1)

        primero.refresh_from_db()
        segundo.refresh_from_db()
        estados = {primero.email_estado, segundo.email_estado}
        self.assertIn(NotificacionInterna.EstadoEntrega.ENVIADO, estados)
        self.assertIn(NotificacionInterna.EstadoEntrega.PENDIENTE, estados)


class TestAvisoPorVencer(BandejaTestBase):
    """
    Media hora antes del vencimiento sale un segundo aviso. Es lo que convierte
    el plazo en algo que el centro puede atajar en vez de algo que le pasa por
    encima.
    """

    def _pedido(self, *, vence_en):
        inicio = timezone.now() + timedelta(days=3)
        turno = reservar_turno(
            cliente=self.cliente, servicio=self.servicio, inicio=inicio,
            origen=Turno.Origen.APP, estado=Turno.Estado.PENDIENTE,
        )
        turno.vence_en = vence_en
        turno.save(update_fields=['vence_en'])
        return turno

    def test_avisa_a_los_que_estan_por_vencer(self):
        turno = self._pedido(vence_en=timezone.now() + timedelta(minutes=20))

        resumen = avisar_los_que_vencen()

        self.assertEqual(resumen['pedidos_por_vencer_avisados'], 1)
        aviso = NotificacionInterna.objects.get(
            turno=turno, tipo=NotificacionInterna.Tipo.TURNO_POR_VENCER
        )
        self.assertIn('está por vencer', aviso.cuerpo)

    def test_no_avisa_a_los_que_tienen_tiempo(self):
        self._pedido(vence_en=timezone.now() + timedelta(hours=2))

        resumen = avisar_los_que_vencen()

        self.assertEqual(resumen['pedidos_por_vencer_avisados'], 0)

    def test_no_avisa_dos_veces_aunque_el_barrido_corra_seguido(self):
        """
        El barrido corre cada cinco minutos: durante la media hora de la ventana
        pasa seis veces. Sin idempotencia serían seis mails por el mismo pedido.
        """
        self._pedido(vence_en=timezone.now() + timedelta(minutes=20))

        avisar_los_que_vencen()
        avisar_los_que_vencen()
        avisar_los_que_vencen()

        self.assertEqual(
            NotificacionInterna.objects.filter(
                tipo=NotificacionInterna.Tipo.TURNO_POR_VENCER
            ).count(),
            1,
        )

    def test_no_avisa_a_uno_que_ya_vencio(self):
        """De eso se ocupa el vencimiento, no este aviso."""
        self._pedido(vence_en=timezone.now() - timedelta(minutes=1))

        resumen = avisar_los_que_vencen()

        self.assertEqual(resumen['pedidos_por_vencer_avisados'], 0)

    def test_no_avisa_a_uno_ya_resuelto(self):
        turno = self._pedido(vence_en=timezone.now() + timedelta(minutes=20))
        turno.estado = Turno.Estado.CONFIRMADO
        turno.save(update_fields=['estado'])

        resumen = avisar_los_que_vencen()

        self.assertEqual(resumen['pedidos_por_vencer_avisados'], 0)


class TestElBarridoGeneralLoIncluye(BandejaTestBase):

    def test_correr_todos_despacha_los_avisos_internos(self):
        """
        Si no estuviera en `DISPARADORES`, los avisos se crearían y no saldrían
        nunca — y eso no se nota hasta que alguien pregunta por qué no le llegó
        ningún mail.
        """
        from apps.notificaciones.disparadores import correr_todos

        inicio = timezone.now() + timedelta(days=3)
        reservar_turno(
            cliente=self.cliente, servicio=self.servicio, inicio=inicio,
            origen=Turno.Origen.APP, estado=Turno.Estado.PENDIENTE,
        )

        with patch('apps.notificaciones.internas.enviar_correo') as enviar:
            resumen = correr_todos()

        enviar.assert_called_once()
        self.assertEqual(resumen['internas_enviadas'], 1)

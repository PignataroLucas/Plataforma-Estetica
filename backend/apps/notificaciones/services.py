"""
Servicios para el envío de notificaciones WhatsApp usando Twilio
"""
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging

from .models import Notificacion

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Servicio para enviar mensajes de WhatsApp via Twilio"""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER
        self.client = None

        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)

    def _validar_configuracion(self):
        """Validar que Twilio esté configurado"""
        if not self.client:
            logger.error("Twilio no está configurado. Verifica TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN")
            return False
        if not self.whatsapp_number:
            logger.error("TWILIO_WHATSAPP_NUMBER no está configurado")
            return False
        return True

    def _formatear_telefono(self, telefono):
        """
        Formatear número de teléfono al formato de WhatsApp
        Entrada: +5491123456789 o 1123456789
        Salida: whatsapp:+5491123456789
        """
        if not telefono:
            return None

        # Remover espacios y guiones
        telefono = telefono.replace(' ', '').replace('-', '')

        # Si no tiene +, agregarlo asumiendo que es Argentina (+54)
        if not telefono.startswith('+'):
            if telefono.startswith('54'):
                telefono = '+' + telefono
            else:
                telefono = '+54' + telefono

        return f'whatsapp:{telefono}'

    def enviar_mensaje(self, telefono, mensaje, tipo_notificacion, cliente, turno=None, sucursal=None):
        """
        Enviar mensaje de WhatsApp y registrar en BD

        Args:
            telefono: Número de teléfono del destinatario
            mensaje: Contenido del mensaje
            tipo_notificacion: Tipo de notificación (ver Notificacion.TipoNotificacion)
            cliente: Instancia de Cliente
            turno: Instancia de Turno (opcional)
            sucursal: Instancia de Sucursal

        Returns:
            Notificacion: Objeto de notificación creado
        """
        # Validar configuración
        if not self._validar_configuracion():
            logger.warning(f"Twilio no configurado. Mensaje no enviado: {mensaje[:50]}...")
            # Crear notificación con estado fallido
            notificacion = Notificacion.objects.create(
                sucursal=sucursal or cliente.sucursal,
                cliente=cliente,
                turno=turno,
                tipo=tipo_notificacion,
                mensaje=mensaje,
                telefono_destino=telefono,
                estado=Notificacion.Estado.FALLIDO,
                error_mensaje="Twilio no está configurado"
            )
            return notificacion

        # Formatear teléfono
        telefono_whatsapp = self._formatear_telefono(telefono)
        if not telefono_whatsapp:
            logger.error(f"Teléfono inválido: {telefono}")
            notificacion = Notificacion.objects.create(
                sucursal=sucursal or cliente.sucursal,
                cliente=cliente,
                turno=turno,
                tipo=tipo_notificacion,
                mensaje=mensaje,
                telefono_destino=telefono,
                estado=Notificacion.Estado.FALLIDO,
                error_mensaje="Teléfono inválido"
            )
            return notificacion

        # Crear notificación con estado PENDIENTE
        notificacion = Notificacion.objects.create(
            sucursal=sucursal or cliente.sucursal,
            cliente=cliente,
            turno=turno,
            tipo=tipo_notificacion,
            mensaje=mensaje,
            telefono_destino=telefono,
            estado=Notificacion.Estado.PENDIENTE
        )

        try:
            # Enviar mensaje via Twilio
            message = self.client.messages.create(
                from_=f'whatsapp:{self.whatsapp_number}',
                to=telefono_whatsapp,
                body=mensaje
            )

            # Actualizar notificación con éxito
            notificacion.mensaje_id_externo = message.sid
            notificacion.estado = Notificacion.Estado.ENVIADO
            notificacion.enviado_en = timezone.now()
            notificacion.save()

            logger.info(f"WhatsApp enviado exitosamente a {telefono}. SID: {message.sid}")
            return notificacion

        except TwilioRestException as e:
            # Error de Twilio
            logger.error(f"Error al enviar WhatsApp a {telefono}: {str(e)}")
            notificacion.estado = Notificacion.Estado.FALLIDO
            notificacion.error_mensaje = str(e)
            notificacion.save()
            return notificacion

        except Exception as e:
            # Error genérico
            logger.error(f"Error inesperado al enviar WhatsApp: {str(e)}")
            notificacion.estado = Notificacion.Estado.FALLIDO
            notificacion.error_mensaje = str(e)
            notificacion.save()
            return notificacion

    def enviar_confirmacion_turno(self, turno):
        """Enviar confirmación de turno"""
        mensaje = self._generar_mensaje_confirmacion(turno)
        return self.enviar_mensaje(
            telefono=turno.cliente.telefono,
            mensaje=mensaje,
            tipo_notificacion=Notificacion.TipoNotificacion.CONFIRMACION_TURNO,
            cliente=turno.cliente,
            turno=turno,
            sucursal=turno.sucursal
        )

    def enviar_recordatorio_24h(self, turno):
        """Enviar recordatorio 24 horas antes"""
        mensaje = self._generar_mensaje_recordatorio_24h(turno)
        return self.enviar_mensaje(
            telefono=turno.cliente.telefono,
            mensaje=mensaje,
            tipo_notificacion=Notificacion.TipoNotificacion.RECORDATORIO_24H,
            cliente=turno.cliente,
            turno=turno,
            sucursal=turno.sucursal
        )

    def enviar_recordatorio_2h(self, turno):
        """Enviar recordatorio 2 horas antes"""
        mensaje = self._generar_mensaje_recordatorio_2h(turno)
        return self.enviar_mensaje(
            telefono=turno.cliente.telefono,
            mensaje=mensaje,
            tipo_notificacion=Notificacion.TipoNotificacion.RECORDATORIO_2H,
            cliente=turno.cliente,
            turno=turno,
            sucursal=turno.sucursal
        )

    def enviar_cancelacion_turno(self, turno):
        """Enviar notificación de cancelación"""
        mensaje = self._generar_mensaje_cancelacion(turno)
        return self.enviar_mensaje(
            telefono=turno.cliente.telefono,
            mensaje=mensaje,
            tipo_notificacion=Notificacion.TipoNotificacion.CANCELACION,
            cliente=turno.cliente,
            turno=turno,
            sucursal=turno.sucursal
        )

    # Templates de mensajes
    def _generar_mensaje_confirmacion(self, turno):
        """Template para confirmación de turno"""
        fecha_formato = turno.fecha_hora_inicio.strftime('%d/%m/%Y')
        hora_formato = turno.fecha_hora_inicio.strftime('%H:%M')

        mensaje = f"""¡Hola {turno.cliente.nombre}!

Tu turno ha sido confirmado ✅

📅 Fecha: {fecha_formato}
🕐 Hora: {hora_formato}
💆 Servicio: {turno.servicio.nombre}
👤 Profesional: {turno.profesional.nombre_completo if turno.profesional else 'Por asignar'}
📍 Sucursal: {turno.sucursal.nombre}

Te enviaremos recordatorios antes de tu turno.

¡Te esperamos!"""
        return mensaje

    def _generar_mensaje_recordatorio_24h(self, turno):
        """Template para recordatorio 24 horas antes"""
        fecha_formato = turno.fecha_hora_inicio.strftime('%d/%m/%Y')
        hora_formato = turno.fecha_hora_inicio.strftime('%H:%M')

        mensaje = f"""Hola {turno.cliente.nombre} 👋

Te recordamos tu turno para mañana:

🕐 {hora_formato} - {turno.servicio.nombre}
👤 {turno.profesional.nombre_completo if turno.profesional else 'Profesional asignado'}
📍 {turno.sucursal.nombre}

Si necesitas cancelar o reprogramar, contactanos.

¡Te esperamos!"""
        return mensaje

    def _generar_mensaje_recordatorio_2h(self, turno):
        """Template para recordatorio 2 horas antes"""
        hora_formato = turno.fecha_hora_inicio.strftime('%H:%M')

        mensaje = f"""¡Tu turno es en 2 horas! ⏰

🕐 {hora_formato} - {turno.servicio.nombre}
📍 {turno.sucursal.direccion if turno.sucursal.direccion else turno.sucursal.nombre}

¡Te esperamos!"""
        return mensaje

    def _generar_mensaje_cancelacion(self, turno):
        """Template para cancelación de turno"""
        fecha_formato = turno.fecha_hora_inicio.strftime('%d/%m/%Y')
        hora_formato = turno.fecha_hora_inicio.strftime('%H:%M')

        mensaje = f"""Hola {turno.cliente.nombre},

Tu turno del {fecha_formato} a las {hora_formato} ha sido cancelado.

Si deseas reprogramar, contactanos.

Saludos!"""
        return mensaje


# Instancia singleton del servicio
whatsapp_service = WhatsAppService()

"""
Servicios para el envío de notificaciones WhatsApp usando Twilio
"""
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
import pytz

from .models import Notificacion, MensajeTemplate

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

    def _convertir_a_hora_local(self, fecha_utc):
        """Convertir fecha UTC a hora local de Argentina"""
        # Convertir a timezone local (configurado en settings.TIME_ZONE)
        return timezone.localtime(fecha_utc)

    def _obtener_template(self, tipo, sucursal):
        """
        Obtener template configurado o usar default hardcodeado

        Args:
            tipo: Tipo de mensaje (ej: 'CONFIRMACION')
            sucursal: Instancia de Sucursal

        Returns:
            str: Contenido del template
        """
        try:
            template = MensajeTemplate.objects.get(
                sucursal=sucursal,
                tipo=tipo,
                activo=True
            )
            return template.mensaje
        except MensajeTemplate.DoesNotExist:
            # Usar templates hardcodeados como fallback
            if tipo == 'CONFIRMACION':
                return self._template_default_confirmacion()
            elif tipo == 'RECORDATORIO_24H':
                return self._template_default_recordatorio_24h()
            elif tipo == 'RECORDATORIO_2H':
                return self._template_default_recordatorio_2h()
            elif tipo == 'CANCELACION':
                return self._template_default_cancelacion()
            return ""

    def _reemplazar_variables(self, template, turno):
        """
        Reemplazar variables en el template con datos reales del turno

        Args:
            template: String con el template del mensaje
            turno: Instancia de Turno

        Returns:
            str: Mensaje con variables reemplazadas
        """
        fecha_hora_local = self._convertir_a_hora_local(turno.fecha_hora_inicio)

        # Definir todas las variables disponibles
        variables = {
            '{nombre_cliente}': turno.cliente.nombre,
            '{fecha}': fecha_hora_local.strftime('%d/%m/%Y'),
            '{hora}': fecha_hora_local.strftime('%H:%M'),
            '{servicio}': turno.servicio.nombre,
            '{profesional}': turno.profesional.nombre_completo if turno.profesional else 'Por asignar',
            '{sucursal_nombre}': turno.sucursal.nombre,
            '{sucursal_direccion}': turno.sucursal.direccion if turno.sucursal.direccion else turno.sucursal.nombre,
            '{sucursal_telefono}': getattr(turno.sucursal, 'telefono', ''),
            '{duracion}': str(turno.servicio.duracion_minutos),
            '{precio}': f"${turno.servicio.precio}",
        }

        # Reemplazar cada variable en el template
        mensaje = template
        for variable, valor in variables.items():
            mensaje = mensaje.replace(variable, str(valor))

        return mensaje

    # Templates de mensajes - AHORA USAN CONFIGURACIÓN
    def _generar_mensaje_confirmacion(self, turno):
        """Template para confirmación de turno - USA CONFIGURACIÓN"""
        template = self._obtener_template('CONFIRMACION', turno.sucursal)
        return self._reemplazar_variables(template, turno)

    def _generar_mensaje_recordatorio_24h(self, turno):
        """Template para recordatorio 24h - USA CONFIGURACIÓN"""
        template = self._obtener_template('RECORDATORIO_24H', turno.sucursal)
        return self._reemplazar_variables(template, turno)

    def _generar_mensaje_recordatorio_2h(self, turno):
        """Template para recordatorio 2h - USA CONFIGURACIÓN"""
        template = self._obtener_template('RECORDATORIO_2H', turno.sucursal)
        return self._reemplazar_variables(template, turno)

    def _generar_mensaje_cancelacion(self, turno):
        """Template para cancelación - USA CONFIGURACIÓN"""
        template = self._obtener_template('CANCELACION', turno.sucursal)
        return self._reemplazar_variables(template, turno)

    # Templates por defecto (fallback si no hay configuración en BD)
    def _template_default_confirmacion(self):
        return """¡Hola {nombre_cliente}!

Tu turno ha sido confirmado ✅

📅 Fecha: {fecha}
🕐 Hora: {hora}
💆 Servicio: {servicio}
👤 Profesional: {profesional}
📍 Sucursal: {sucursal_nombre}

Te enviaremos recordatorios antes de tu turno.

¡Te esperamos!"""

    def _template_default_recordatorio_24h(self):
        return """Hola {nombre_cliente} 👋

Te recordamos tu turno para mañana:

🕐 {hora} - {servicio}
👤 {profesional}
📍 {sucursal_nombre}

Si necesitas cancelar o reprogramar, contactanos.

¡Te esperamos!"""

    def _template_default_recordatorio_2h(self):
        return """¡Tu turno es en 2 horas! ⏰

🕐 {hora} - {servicio}
📍 {sucursal_direccion}

¡Te esperamos!"""

    def _template_default_cancelacion(self):
        return """Hola {nombre_cliente},

Tu turno del {fecha} a las {hora} ha sido cancelado.

Si deseas reprogramar, contactanos.

Saludos!"""


# Instancia singleton del servicio
whatsapp_service = WhatsAppService()

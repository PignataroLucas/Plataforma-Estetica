"""
Celery tasks para notificaciones WhatsApp
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from apps.turnos.models import Turno
from .services import whatsapp_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def enviar_confirmacion_turno_task(self, turno_id):
    """
    Task asíncrona para enviar confirmación de turno

    Args:
        turno_id: ID del turno
    """
    try:
        turno = Turno.objects.get(id=turno_id)

        # Enviar WhatsApp de confirmación
        notificacion = whatsapp_service.enviar_confirmacion_turno(turno)

        if notificacion.estado == 'ENVIADO':
            logger.info(f"Confirmación enviada para turno {turno_id}")
        else:
            logger.warning(f"Confirmación fallida para turno {turno_id}: {notificacion.error_mensaje}")

        return {
            'turno_id': turno_id,
            'notificacion_id': notificacion.id,
            'estado': notificacion.estado
        }

    except Turno.DoesNotExist:
        logger.error(f"Turno {turno_id} no existe")
        return {'error': 'Turno no encontrado'}

    except Exception as e:
        logger.error(f"Error enviando confirmación turno {turno_id}: {str(e)}")
        # Reintentar si falla
        raise self.retry(exc=e, countdown=60)  # Reintentar en 60 segundos


@shared_task(bind=True, max_retries=3)
def enviar_recordatorio_24h_task(self, turno_id):
    """
    Task asíncrona para enviar recordatorio 24h antes

    Args:
        turno_id: ID del turno
    """
    try:
        turno = Turno.objects.get(id=turno_id)

        # Verificar que el turno sigue activo
        if turno.estado in ['CANCELADO', 'COMPLETADO', 'NO_SHOW']:
            logger.info(f"Turno {turno_id} no está activo. No se envía recordatorio.")
            return {'turno_id': turno_id, 'estado': 'skipped'}

        # Enviar recordatorio
        notificacion = whatsapp_service.enviar_recordatorio_24h(turno)

        if notificacion.estado == 'ENVIADO':
            logger.info(f"Recordatorio 24h enviado para turno {turno_id}")
        else:
            logger.warning(f"Recordatorio 24h fallido para turno {turno_id}: {notificacion.error_mensaje}")

        return {
            'turno_id': turno_id,
            'notificacion_id': notificacion.id,
            'estado': notificacion.estado
        }

    except Turno.DoesNotExist:
        logger.error(f"Turno {turno_id} no existe")
        return {'error': 'Turno no encontrado'}

    except Exception as e:
        logger.error(f"Error enviando recordatorio 24h turno {turno_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def enviar_recordatorio_2h_task(self, turno_id):
    """
    Task asíncrona para enviar recordatorio 2h antes

    Args:
        turno_id: ID del turno
    """
    try:
        turno = Turno.objects.get(id=turno_id)

        # Verificar que el turno sigue activo
        if turno.estado in ['CANCELADO', 'COMPLETADO', 'NO_SHOW']:
            logger.info(f"Turno {turno_id} no está activo. No se envía recordatorio.")
            return {'turno_id': turno_id, 'estado': 'skipped'}

        # Enviar recordatorio
        notificacion = whatsapp_service.enviar_recordatorio_2h(turno)

        if notificacion.estado == 'ENVIADO':
            logger.info(f"Recordatorio 2h enviado para turno {turno_id}")
        else:
            logger.warning(f"Recordatorio 2h fallido para turno {turno_id}: {notificacion.error_mensaje}")

        return {
            'turno_id': turno_id,
            'notificacion_id': notificacion.id,
            'estado': notificacion.estado
        }

    except Turno.DoesNotExist:
        logger.error(f"Turno {turno_id} no existe")
        return {'error': 'Turno no encontrado'}

    except Exception as e:
        logger.error(f"Error enviando recordatorio 2h turno {turno_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def enviar_cancelacion_turno_task(self, turno_id):
    """
    Task asíncrona para enviar notificación de cancelación

    Args:
        turno_id: ID del turno
    """
    try:
        turno = Turno.objects.get(id=turno_id)

        # Enviar notificación de cancelación
        notificacion = whatsapp_service.enviar_cancelacion_turno(turno)

        if notificacion.estado == 'ENVIADO':
            logger.info(f"Cancelación enviada para turno {turno_id}")
        else:
            logger.warning(f"Cancelación fallida para turno {turno_id}: {notificacion.error_mensaje}")

        return {
            'turno_id': turno_id,
            'notificacion_id': notificacion.id,
            'estado': notificacion.estado
        }

    except Turno.DoesNotExist:
        logger.error(f"Turno {turno_id} no existe")
        return {'error': 'Turno no encontrado'}

    except Exception as e:
        logger.error(f"Error enviando cancelación turno {turno_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def procesar_recordatorios_pendientes():
    """
    Task periódica para enviar recordatorios programados
    Esta task se ejecuta cada hora via Celery Beat
    """
    ahora = timezone.now()

    # Recordatorios 24h antes (enviar entre 23-25 horas antes)
    inicio_ventana_24h = ahora + timedelta(hours=23)
    fin_ventana_24h = ahora + timedelta(hours=25)

    turnos_24h = Turno.objects.filter(
        fecha_hora_inicio__gte=inicio_ventana_24h,
        fecha_hora_inicio__lte=fin_ventana_24h,
        estado__in=['PENDIENTE', 'CONFIRMADO', 'CON_SENA'],
        recordatorio_24h_enviado=False
    )

    enviados_24h = 0
    for turno in turnos_24h:
        enviar_recordatorio_24h_task.delay(turno.id)
        turno.recordatorio_24h_enviado = True
        turno.save(update_fields=['recordatorio_24h_enviado'])
        enviados_24h += 1

    logger.info(f"Programados {enviados_24h} recordatorios de 24h")

    # Recordatorios 2h antes (enviar entre 1.5-2.5 horas antes)
    inicio_ventana_2h = ahora + timedelta(hours=1, minutes=30)
    fin_ventana_2h = ahora + timedelta(hours=2, minutes=30)

    turnos_2h = Turno.objects.filter(
        fecha_hora_inicio__gte=inicio_ventana_2h,
        fecha_hora_inicio__lte=fin_ventana_2h,
        estado__in=['PENDIENTE', 'CONFIRMADO', 'CON_SENA'],
        recordatorio_2h_enviado=False
    )

    enviados_2h = 0
    for turno in turnos_2h:
        enviar_recordatorio_2h_task.delay(turno.id)
        turno.recordatorio_2h_enviado = True
        turno.save(update_fields=['recordatorio_2h_enviado'])
        enviados_2h += 1

    logger.info(f"Programados {enviados_2h} recordatorios de 2h")

    return {
        'recordatorios_24h': enviados_24h,
        'recordatorios_2h': enviados_2h,
        'timestamp': ahora.isoformat()
    }

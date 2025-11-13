from django.db import models
from apps.clientes.models import Cliente
from apps.empleados.models import Sucursal


class Notificacion(models.Model):
    """
    Registro de notificaciones WhatsApp enviadas
    """
    class TipoNotificacion(models.TextChoices):
        CONFIRMACION_TURNO = 'CONFIRMACION', 'Confirmación de Turno'
        RECORDATORIO_24H = 'RECORDATORIO_24H', 'Recordatorio 24 horas'
        RECORDATORIO_2H = 'RECORDATORIO_2H', 'Recordatorio 2 horas'
        CANCELACION = 'CANCELACION', 'Cancelación de Turno'
        MODIFICACION = 'MODIFICACION', 'Modificación de Turno'
        SEGUIMIENTO = 'SEGUIMIENTO', 'Seguimiento Post-tratamiento'
        PROMOCION = 'PROMOCION', 'Promoción'
        OTRO = 'OTRO', 'Otro'

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        ENVIADO = 'ENVIADO', 'Enviado'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        LEIDO = 'LEIDO', 'Leído'
        FALLIDO = 'FALLIDO', 'Fallido'

    # Relaciones
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    turno = models.ForeignKey(
        'turnos.Turno',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones'
    )

    # Información de la notificación
    tipo = models.CharField(
        max_length=20,
        choices=TipoNotificacion.choices
    )
    mensaje = models.TextField()
    telefono_destino = models.CharField(max_length=20)

    # Estado del envío
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )

    # Respuesta del servicio (Twilio/WhatsApp API)
    mensaje_id_externo = models.CharField(max_length=100, blank=True)
    error_mensaje = models.TextField(blank=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    enviado_en = models.DateTimeField(null=True, blank=True)
    entregado_en = models.DateTimeField(null=True, blank=True)
    leido_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['sucursal', 'estado', 'creado_en']),
            models.Index(fields=['cliente', 'creado_en']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nombre_completo} - {self.get_estado_display()}"

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.clientes.models import Cliente
from apps.servicios.models import Servicio
from apps.empleados.models import Usuario, Sucursal


class Turno(models.Model):
    """
    Sistema de turnos/citas con prevención de double-booking
    """
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Confirmación'
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'
        COMPLETADO = 'COMPLETADO', 'Completado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        NO_SHOW = 'NO_SHOW', 'No Show'

    class EstadoPago(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        CON_SENA = 'CON_SENA', 'Con Seña'
        PAGADO = 'PAGADO', 'Pagado'

    # Relaciones
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='turnos'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='turnos'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='turnos'
    )
    profesional = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_asignados',
        help_text="Profesional asignado al turno"
    )

    # Fecha y hora
    fecha_hora_inicio = models.DateTimeField(db_index=True)
    fecha_hora_fin = models.DateTimeField(db_index=True)

    # Estados
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        db_index=True
    )
    estado_pago = models.CharField(
        max_length=15,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDIENTE
    )

    # Información adicional
    notas = models.TextField(blank=True)
    monto_sena = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    monto_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio del servicio al momento de la reserva"
    )

    # Recordatorios enviados
    recordatorio_24h_enviado = models.BooleanField(default=False)
    recordatorio_2h_enviado = models.BooleanField(default=False)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='turnos_creados'
    )

    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['-fecha_hora_inicio']
        indexes = [
            models.Index(fields=['sucursal', 'fecha_hora_inicio']),
            models.Index(fields=['profesional', 'fecha_hora_inicio']),
            models.Index(fields=['cliente', 'fecha_hora_inicio']),
            models.Index(fields=['estado', 'fecha_hora_inicio']),
        ]

    def __str__(self):
        return f"{self.cliente.nombre_completo} - {self.servicio.nombre} - {self.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}"

    def clean(self):
        """
        Validaciones antes de guardar
        """
        # Validar que fecha_fin sea posterior a fecha_inicio
        if self.fecha_hora_fin <= self.fecha_hora_inicio:
            raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")

        # Validar que el profesional pertenezca a la misma sucursal
        if self.profesional and self.profesional.sucursal != self.sucursal:
            raise ValidationError("El profesional debe pertenecer a la misma sucursal")

        # Validar que el servicio pertenezca a la misma sucursal
        if self.servicio.sucursal != self.sucursal:
            raise ValidationError("El servicio debe pertenecer a la misma sucursal")

    def save(self, *args, **kwargs):
        # Calcular fecha_hora_fin basado en duración del servicio si no está establecida
        if not self.fecha_hora_fin:
            from datetime import timedelta
            self.fecha_hora_fin = self.fecha_hora_inicio + timedelta(
                minutes=self.servicio.duracion_minutos
            )

        # Establecer monto_total desde el servicio si no está establecido
        if not self.monto_total:
            self.monto_total = self.servicio.precio

        self.full_clean()
        super().save(*args, **kwargs)

    def verificar_disponibilidad(self):
        """
        Verifica si hay conflictos de horario con otros turnos
        CRÍTICO: Prevención de double-booking
        """
        conflictos = Turno.objects.filter(
            sucursal=self.sucursal,
            profesional=self.profesional,
            estado__in=[self.Estado.PENDIENTE, self.Estado.CONFIRMADO],
        ).filter(
            models.Q(
                fecha_hora_inicio__lt=self.fecha_hora_fin,
                fecha_hora_fin__gt=self.fecha_hora_inicio
            )
        ).exclude(pk=self.pk)

        return not conflictos.exists(), conflictos

    @property
    def requiere_recordatorio_24h(self):
        """Verifica si debe enviar recordatorio de 24 horas"""
        if self.recordatorio_24h_enviado or self.estado not in [self.Estado.PENDIENTE, self.Estado.CONFIRMADO]:
            return False

        from datetime import timedelta
        ventana_24h = timezone.now() + timedelta(hours=24)
        return self.fecha_hora_inicio <= ventana_24h + timedelta(hours=1)

    @property
    def requiere_recordatorio_2h(self):
        """Verifica si debe enviar recordatorio de 2 horas"""
        if self.recordatorio_2h_enviado or self.estado not in [self.Estado.PENDIENTE, self.Estado.CONFIRMADO]:
            return False

        from datetime import timedelta
        ventana_2h = timezone.now() + timedelta(hours=2)
        return self.fecha_hora_inicio <= ventana_2h + timedelta(minutes=30)

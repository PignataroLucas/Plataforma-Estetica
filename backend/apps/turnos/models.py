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
        # Un pedido que el centro no tomó. **No es lo mismo que CANCELADO**: un
        # turno cancelado existió y se cayó; un pedido rechazado nunca llegó a
        # ser turno. La diferencia se paga en el texto que ve la clienta —"elegí
        # otro horario" en vez de una disculpa— y sobre todo en las métricas: la
        # tasa de rechazo mide si la disponibilidad que publica la app se parece
        # a la realidad del centro, y la de cancelación mide comportamiento de
        # las clientas. Mezcladas, las dos quedan inservibles.
        RECHAZADO = 'RECHAZADO', 'Rechazado'
        COMPLETADO = 'COMPLETADO', 'Completado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        NO_SHOW = 'NO_SHOW', 'No Show'

    class MotivoRechazo(models.TextChoices):
        """
        Lista cerrada a propósito, no texto libre.

        Con texto libre el reporte de rechazos no se puede agrupar, y esa es la
        métrica más útil del circuito: *por qué* estamos rechazando. Además, un
        campo vacío frena a quien está apurada y termina escribiendo "no".
        """
        SIN_DISPONIBILIDAD = 'SIN_DISPONIBILIDAD', 'No hay disponibilidad real'
        EQUIPO_NO_DISPONIBLE = 'EQUIPO_NO_DISPONIBLE', 'El equipo no está disponible'
        DEUDA_PENDIENTE = 'DEUDA_PENDIENTE', 'La clienta tiene una deuda'
        REQUIERE_EVALUACION = 'REQUIERE_EVALUACION', 'Requiere evaluación previa'
        OTRO = 'OTRO', 'Otro'
        # Lo pone el sistema cuando nadie responde a tiempo. **No se ofrece en el
        # CRM**: separar "dijimos que no" de "nadie lo miró" es lo que hace que
        # las métricas sirvan, porque son dos problemas con dos soluciones
        # distintas.
        VENCIDO = 'VENCIDO', 'Venció sin respuesta'

    class Origen(models.TextChoices):
        """
        De dónde salió el turno.

        Se guarda explícito en vez de inferirlo de ``creado_por`` —que es nulo
        cuando reservó la clienta— porque el circuito de aprobación aplica solo a
        los de la app, y porque Analytics necesita contar cuántos turnos trae la
        app sin depender de un nulo que podría significar otra cosa mañana.
        """
        APP = 'APP', 'App de clientas'
        CRM = 'CRM', 'Cargado en el CRM'

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

    origen = models.CharField(
        max_length=10,
        choices=Origen.choices,
        default=Origen.CRM,
        db_index=True,
        help_text="De dónde salió el turno. La app manda APP; el CRM es el default."
    )
    vence_en = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Hasta cuándo el centro puede aceptar o rechazar este pedido. "
                  "Solo se completa en los que esperan aprobación."
    )

    # --- Resolución del pedido (APROBACION_TURNOS_SPEC.md) ---
    motivo_rechazo = models.CharField(
        max_length=25,
        choices=MotivoRechazo.choices,
        blank=True,
        help_text="Obligatorio al rechazar. Lo completa el sistema si vence."
    )
    detalle_rechazo = models.CharField(
        max_length=300,
        blank=True,
        help_text="Aclaración opcional del motivo. Nunca se le muestra a la clienta."
    )
    resuelto_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_resueltos',
        help_text="Quién aceptó o rechazó el pedido. Vacío si venció sin respuesta."
    )
    resuelto_en = models.DateTimeField(null=True, blank=True)

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
        blank=True,
        related_name='turnos_creados',
        help_text="Empleado que cargó el turno. Vacío si lo reservó el cliente desde la app"
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
            # El barrido de vencimientos: pendientes cuyo plazo ya pasó. Con
            # nombre explícito y no derivado, para que la migración no dependa
            # del hash que genera Django.
            models.Index(
                fields=['estado', 'vence_en'], name='turnos_turn_estado_vence_idx'
            ),
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

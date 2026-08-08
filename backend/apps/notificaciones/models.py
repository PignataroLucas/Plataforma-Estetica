from django.db import models
from apps.clientes.models import Cliente, UsuarioCliente
from apps.empleados.models import CentroEstetica, Sucursal

from .eventos import Categoria


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


class MensajeTemplate(models.Model):
    """
    Plantillas configurables de mensajes WhatsApp
    Cada centro puede personalizar sus mensajes
    """

    class TipoMensaje(models.TextChoices):
        CONFIRMACION_TURNO = 'CONFIRMACION', 'Confirmación de Turno'
        RECORDATORIO_24H = 'RECORDATORIO_24H', 'Recordatorio 24 horas'
        RECORDATORIO_2H = 'RECORDATORIO_2H', 'Recordatorio 2 horas'
        CANCELACION = 'CANCELACION', 'Cancelación de Turno'
        MODIFICACION = 'MODIFICACION', 'Modificación de Turno'
        PROMOCION = 'PROMOCION', 'Mensaje Promocional'

    # Multi-tenancy
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='mensajes_templates'
    )

    # Tipo de mensaje
    tipo = models.CharField(max_length=30, choices=TipoMensaje.choices)

    # Contenido del mensaje
    mensaje = models.TextField(
        help_text="Contenido del mensaje. Usa variables: {nombre_cliente}, {fecha}, {hora}, {servicio}, {profesional}, {sucursal_nombre}, {sucursal_direccion}"
    )

    # Metadata
    activo = models.BooleanField(
        default=True,
        help_text="Si está inactivo, se usa el mensaje por defecto"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mensajes_templates_actualizados'
    )

    class Meta:
        verbose_name = "Plantilla de Mensaje"
        verbose_name_plural = "Plantillas de Mensajes"
        unique_together = ['sucursal', 'tipo']  # Una plantilla por tipo por sucursal
        ordering = ['tipo']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.sucursal.nombre}"


# ===================================================================== #
# Notificaciones push a la app de clientas
#
# Los modelos de arriba son el log de WhatsApp (canal hoy caído) y quedan
# como están. Lo que sigue es el núcleo nuevo, pensado para servir a todos
# los avisos de la app --turnos, rutina, cumpleaños, promos-- con una sola
# tubería: se declara el evento en ``eventos.py``, se crea un ``Aviso`` y
# la cola se encarga del resto.
# ===================================================================== #


class DispositivoPush(models.Model):
    """
    Un teléfono habilitado para recibir push.

    Es una tabla y no un campo en la cuenta porque **una cuenta puede tener
    varios dispositivos** (el teléfono viejo y el nuevo, el de la clienta y la
    tablet del centro). Guardarlo como campo único hacía que instalar la app en
    otro teléfono apagara silenciosamente el anterior.

    El token es único a nivel global: si una clienta presta el teléfono y otra
    cuenta inicia sesión ahí, el token se reasigna a la cuenta nueva en lugar de
    duplicarse. Es lo que evita que le lleguen los turnos de otra persona.
    """

    class Plataforma(models.TextChoices):
        IOS = 'IOS', 'iOS'
        ANDROID = 'ANDROID', 'Android'
        WEB = 'WEB', 'Web'
        DESCONOCIDA = 'DESCONOCIDA', 'Desconocida'

    class MotivoBaja(models.TextChoices):
        SESION_CERRADA = 'SESION_CERRADA', 'Cerró sesión'
        TOKEN_MUERTO = 'TOKEN_MUERTO', 'Expo lo rechazó (app desinstalada)'
        REASIGNADO = 'REASIGNADO', 'El teléfono pasó a otra cuenta'

    usuario_cliente = models.ForeignKey(
        UsuarioCliente,
        on_delete=models.CASCADE,
        related_name='dispositivos_push',
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Expo push token (ExponentPushToken[...])",
    )
    plataforma = models.CharField(
        max_length=15,
        choices=Plataforma.choices,
        default=Plataforma.DESCONOCIDA,
    )
    activo = models.BooleanField(default=True)
    motivo_baja = models.CharField(
        max_length=20,
        choices=MotivoBaja.choices,
        blank=True,
        help_text="Por qué se dio de baja. Vacío mientras está activo.",
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dispositivo push'
        verbose_name_plural = 'Dispositivos push'
        ordering = ['-actualizado_en']
        indexes = [
            models.Index(fields=['usuario_cliente', 'activo']),
        ]

    def __str__(self):
        estado = 'activo' if self.activo else 'de baja'
        return f"{self.usuario_cliente.email} · {self.get_plataforma_display()} ({estado})"

    def dar_de_baja(self, motivo):
        """Apaga el dispositivo sin borrarlo, para no perder el historial de envíos."""
        self.activo = False
        self.motivo_baja = motivo
        self.save(update_fields=['activo', 'motivo_baja', 'actualizado_en'])


class PreferenciaNotificacion(models.Model):
    """
    Opt-out por categoría.

    Ausencia de fila = habilitada. Se guarda solo cuando la clienta apaga algo,
    así no hay que sembrar filas al crear cada cuenta ni migrar cuando se suma
    una categoría nueva.
    """

    usuario_cliente = models.ForeignKey(
        UsuarioCliente,
        on_delete=models.CASCADE,
        related_name='preferencias_notificacion',
    )
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    habilitada = models.BooleanField(default=True)

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Preferencia de notificación'
        verbose_name_plural = 'Preferencias de notificación'
        unique_together = ['usuario_cliente', 'categoria']
        ordering = ['categoria']

    def __str__(self):
        estado = 'sí' if self.habilitada else 'no'
        return f"{self.usuario_cliente.email} · {self.get_categoria_display()}: {estado}"


class PlantillaNotificacion(models.Model):
    """
    Texto propio de un centro para un evento.

    Si no hay fila, se usa el texto por defecto de ``eventos.py``. Guardar solo
    las excepciones evita que un cambio en el texto base quede pisado en todos
    los centros que nunca lo tocaron.
    """

    centro_estetica = models.ForeignKey(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='plantillas_notificacion',
    )
    evento = models.CharField(
        max_length=50,
        help_text="Clave del evento (ver apps.notificaciones.eventos)",
    )
    titulo = models.CharField(
        max_length=100,
        help_text="Título de la notificación. Admite variables entre llaves.",
    )
    cuerpo = models.CharField(
        max_length=300,
        help_text="Cuerpo de la notificación. Admite variables entre llaves.",
    )
    activa = models.BooleanField(
        default=True,
        help_text="Si se desactiva, vuelve a usarse el texto por defecto.",
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plantilla de notificación'
        verbose_name_plural = 'Plantillas de notificación'
        unique_together = ['centro_estetica', 'evento']
        ordering = ['evento']

    def __str__(self):
        return f"{self.evento} · {self.centro_estetica.nombre}"


class Aviso(models.Model):
    """
    Una notificación ya resuelta para una persona, esperando salir.

    Es un *outbox*: quien dispara el aviso solo escribe esta fila y sigue. El
    envío lo hace después el proceso de cola. Eso da tres cosas que importan:
    el request del staff no espera a la API de Expo, un envío no se pierde si el
    proceso de turno está caído, y reintentar es releer una fila.

    ``clave`` es la idempotencia: ``turno:12:recordatorio_24h`` entra una sola
    vez por más que el cron corra dos veces o se solapen dos procesos.
    """

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        # Tomado por un proceso de cola. Existe para que dos corridas solapadas
        # no manden el mismo aviso dos veces sin tener que sostener un lock de
        # base durante la llamada HTTP a Expo.
        PROCESANDO = 'PROCESANDO', 'En curso'
        ENVIADO = 'ENVIADO', 'Enviado'
        SIN_DESTINO = 'SIN_DESTINO', 'Sin dispositivo activo'
        FALLIDO = 'FALLIDO', 'Fallido'
        CANCELADO = 'CANCELADO', 'Cancelado'

    evento = models.CharField(max_length=50, help_text="Clave del evento")
    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        help_text="Se copia del evento al crear, para poder filtrar sin resolver el catálogo.",
    )

    usuario_cliente = models.ForeignKey(
        UsuarioCliente,
        on_delete=models.CASCADE,
        related_name='avisos',
    )
    centro_estetica = models.ForeignKey(
        CentroEstetica,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='avisos',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avisos',
        help_text="Ficha del centro, para rastrear el aviso desde el CRM.",
    )

    titulo = models.CharField(max_length=150)
    cuerpo = models.CharField(max_length=400)
    datos = models.JSONField(
        default=dict,
        blank=True,
        help_text="Carga útil que viaja al teléfono: ruta de la app e ids del origen.",
    )

    clave = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
        help_text="Clave de idempotencia. Nula para avisos que sí pueden repetirse.",
    )
    programado_para = models.DateTimeField(
        help_text="No sale antes de este momento. Igual a la creación si es inmediato.",
    )

    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    intentos = models.PositiveSmallIntegerField(default=0)
    error = models.TextField(blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    enviado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Aviso'
        verbose_name_plural = 'Avisos'
        ordering = ['-creado_en']
        indexes = [
            # El índice que usa la cola en cada corrida.
            models.Index(fields=['estado', 'programado_para']),
            models.Index(fields=['usuario_cliente', '-creado_en']),
            models.Index(fields=['evento', '-creado_en']),
        ]

    def __str__(self):
        return f"{self.evento} → {self.usuario_cliente.email} ({self.get_estado_display()})"


class EnvioPush(models.Model):
    """
    Entrega de un ``Aviso`` a un dispositivo concreto.

    Un aviso para una cuenta con dos teléfonos son dos filas acá. Separarlo del
    aviso permite saber que llegó al teléfono nuevo y no al viejo, y es donde se
    guarda el ticket de Expo para después consultar el recibo.
    """

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        ACEPTADO = 'ACEPTADO', 'Aceptado por Expo'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        FALLIDO = 'FALLIDO', 'Fallido'

    aviso = models.ForeignKey(
        Aviso,
        on_delete=models.CASCADE,
        related_name='envios',
    )
    dispositivo = models.ForeignKey(
        DispositivoPush,
        on_delete=models.CASCADE,
        related_name='envios',
    )

    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    ticket_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Id que devuelve Expo al aceptar el mensaje; se usa para pedir el recibo.",
    )
    error = models.CharField(max_length=300, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    confirmado_en = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cuándo se leyó el recibo definitivo de Expo.",
    )

    class Meta:
        verbose_name = 'Envío push'
        verbose_name_plural = 'Envíos push'
        unique_together = ['aviso', 'dispositivo']
        ordering = ['-creado_en']
        indexes = [
            # Los que esperan recibo.
            models.Index(fields=['estado', 'creado_en']),
        ]

    def __str__(self):
        return f"{self.aviso_id} → {self.dispositivo_id} ({self.get_estado_display()})"

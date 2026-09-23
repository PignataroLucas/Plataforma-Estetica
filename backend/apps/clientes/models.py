import secrets
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from apps.empleados.models import CentroEstetica


class SegmentoApp(models.Model):
    """
    Grupo de clientas de la app con el descuento que les corresponde.

    El porcentaje vive acá y no suelto en cada ficha: el día que VIP pase de 15%
    a 20% hay que editar un registro y no cuarenta (COMPRA_EN_APP_SPEC.md §5.8).

    La segmentación es de la plataforma y no de Tienda Nube, y no por gusto: la
    API de TN no permite atar un cupón a un cliente, así que allá no existe ni
    puede existir el concepto de "esta clienta es VIP". TN solo recibe un
    porcentaje ya resuelto.
    """
    centro_estetica = models.ForeignKey(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='segmentos_app'
    )
    nombre = models.CharField(max_length=60)
    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name='Descuento',
        help_text="Porcentaje que se le descuenta a las clientas de este segmento"
    )
    es_predeterminado = models.BooleanField(
        default=False,
        verbose_name='Es el general de la app',
        help_text="El descuento que le corresponde a toda clienta sin segmento propio"
    )
    activo = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Segmento de la app'
        verbose_name_plural = 'Segmentos de la app'
        ordering = ['-es_predeterminado', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['centro_estetica', 'nombre'],
                name='segmento_app_nombre_unico_por_centro',
            ),
            # Un solo general por centro: con dos, cuál gana lo decidiría el
            # orden de la tabla, y el precio de la app dependería de eso.
            models.UniqueConstraint(
                fields=['centro_estetica'],
                condition=models.Q(es_predeterminado=True),
                name='segmento_app_un_solo_predeterminado_por_centro',
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje_descuento}%)"


class Cliente(models.Model):
    """
    Información completa de clientes del centro de estética
    """
    # Tenant
    centro_estetica = models.ForeignKey(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='clientes'
    )

    # Información personal
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20)
    telefono_alternativo = models.CharField(max_length=20, blank=True)
    # Forma canónica E.164 de ``telefono`` (ej: +5491123456789). Se calcula en save().
    # Se usa para el detector de duplicados y para el matching de vinculación.
    telefono_normalizado = models.CharField(max_length=20, blank=True, db_index=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    # Dirección
    direccion = models.CharField(max_length=300, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=10, blank=True)

    # Documento
    tipo_documento = models.CharField(
        max_length=10,
        choices=[
            ('DNI', 'DNI'),
            ('PASAPORTE', 'Pasaporte'),
            ('OTRO', 'Otro')
        ],
        default='DNI'
    )
    numero_documento = models.CharField(max_length=20, blank=True)

    # A) Datos del paciente (tracking)
    motivo_consulta = models.TextField(blank=True, help_text="Motivo principal de consulta")
    objetivo_principal = models.CharField(max_length=500, blank=True, help_text="Objetivo principal en una frase")

    # B) Historia / contraindicaciones
    embarazo_lactancia = models.BooleanField(default=False, help_text="¿Embarazo o lactancia?")
    marcapasos_implantes = models.BooleanField(default=False, help_text="¿Marcapasos o implantes metálicos?")
    cancer_historial = models.BooleanField(default=False, help_text="¿Cáncer actual o antecedente?")
    herpes_historial = models.BooleanField(default=False, help_text="¿Historial de herpes?")

    # Alergias (ya existe, se mantiene)
    alergias = models.TextField(blank=True, help_text="Alergias o sensibilidades")
    tiene_alergias = models.BooleanField(default=False, help_text="¿Tiene alergias?")

    # Medicación
    medicacion_actual = models.BooleanField(default=False, help_text="¿Toma medicación actual?")
    medicacion_detalle = models.TextField(blank=True, help_text="Detalle de medicación actual")

    # Tratamientos previos
    tratamientos_previos = models.BooleanField(default=False, help_text="¿Tratamientos estéticos previos?")
    tratamientos_previos_detalle = models.TextField(blank=True, help_text="Detalle de tratamientos previos")

    # Tatuajes (importante para depilación definitiva)
    tatuajes_zona_tratamiento = models.BooleanField(default=False, help_text="¿Tatuajes en zona a tratar?")
    tatuajes_zonas = models.TextField(blank=True, help_text="Zonas con tatuajes")

    # Contraindicaciones y notas (ya existen, se mantienen)
    contraindicaciones = models.TextField(blank=True)
    notas_medicas = models.TextField(blank=True)
    detalle_general = models.TextField(blank=True, help_text="Aclaraciones adicionales generales")

    # C) Evaluación facial
    tipo_piel = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('NORMAL', 'Normal'),
            ('SECA', 'Seca'),
            ('MIXTA', 'Mixta'),
            ('GRASA', 'Grasa'),
            ('NO_DETERMINADO', 'No determinado'),
        ],
        help_text="Tipo de piel"
    )

    poros = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('FINOS', 'Finos'),
            ('MEDIOS', 'Medios'),
            ('DILATADOS', 'Dilatados'),
            ('MIXTO', 'Mixto'),
        ],
        help_text="Estado de poros"
    )

    brillo = models.CharField(
        max_length=10,
        blank=True,
        choices=[
            ('BAJO', 'Bajo'),
            ('MEDIO', 'Medio'),
            ('ALTO', 'Alto'),
        ],
        help_text="Nivel de brillo"
    )

    textura = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('UNIFORME', 'Uniforme'),
            ('ASPERA', 'Áspera'),
            ('DESCAMACION', 'Descamación'),
            ('MIXTA', 'Mixta'),
        ],
        help_text="Textura de la piel"
    )

    estado_piel = models.TextField(blank=True, help_text="Estado de piel: deshidratada, sensible, rosácea, manchas, acné, etc.")
    observaciones_faciales = models.TextField(blank=True, help_text="Observaciones de zonas puntuales")
    diagnostico_facial = models.TextField(blank=True, help_text="Diagnóstico facial resumen")

    # D) Evaluación corporal
    zonas_tratar = models.TextField(blank=True, help_text="Zonas corporales a tratar")

    celulitis_grado = models.IntegerField(
        null=True,
        blank=True,
        choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')],
        help_text="Grado de celulitis (0-3)"
    )

    celulitis_tipo = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('EDEMATOSA', 'Edematosa'),
            ('FIBROSA', 'Fibrosa'),
            ('BLANDA', 'Blanda'),
            ('MIXTA', 'Mixta'),
            ('NO_APLICA', 'No aplica'),
        ],
        help_text="Tipo de celulitis"
    )

    adiposidad = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('BAJA', 'Baja'),
            ('MEDIA', 'Media'),
            ('ALTA', 'Alta'),
            ('NO_APLICA', 'No aplica'),
        ],
        help_text="Adiposidad localizada"
    )

    flacidez = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('LEVE', 'Leve'),
            ('MODERADA', 'Moderada'),
            ('MARCADA', 'Marcada'),
            ('NO_APLICA', 'No aplica'),
        ],
        help_text="Flacidez corporal"
    )

    estrias = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('NO', 'No'),
            ('BLANCAS', 'Blancas'),
            ('ROJAS', 'Rojas'),
            ('MIXTAS', 'Mixtas'),
        ],
        help_text="Estrías"
    )

    retencion_liquidos = models.BooleanField(default=False, help_text="¿Retención de líquidos?")
    observaciones_corporales = models.TextField(blank=True, help_text="Observaciones corporales")
    diagnostico_corporal = models.TextField(blank=True, help_text="Diagnóstico corporal resumen")

    # Preferencias (se mantiene)
    preferencias = models.TextField(blank=True, help_text="Preferencias del cliente")

    # Foto de perfil
    foto = models.ImageField(upload_to='clientes/', null=True, blank=True)

    # Marketing
    acepta_promociones = models.BooleanField(default=True)
    acepta_whatsapp = models.BooleanField(default=True)

    # App
    segmento_app = models.ForeignKey(
        SegmentoApp,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
        verbose_name='Segmento de la app',
        help_text="Vacío significa que le corresponde el descuento general de la app"
    )

    # Estado
    activo = models.BooleanField(default=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    ultima_visita = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['apellido', 'nombre']
        indexes = [
            models.Index(fields=['centro_estetica', 'apellido']),
            models.Index(fields=['centro_estetica', 'telefono']),
        ]

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    def save(self, *args, **kwargs):
        from .utils import normalizar_telefono
        self.telefono_normalizado = normalizar_telefono(self.telefono)
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def clean(self):
        """El segmento tiene que ser del mismo centro que la ficha."""
        super().clean()
        if (
            self.segmento_app_id
            and self.centro_estetica_id
            and self.segmento_app.centro_estetica_id != self.centro_estetica_id
        ):
            raise ValidationError({
                'segmento_app': 'El segmento pertenece a otro centro de estética'
            })

    @property
    def segmento_app_efectivo(self):
        """
        El segmento que manda para esta clienta: el suyo, o el general del centro.

        Un segmento desactivado cae al general en vez de a cero: apagar "VIP" es
        dejar de tratarlas distinto, no dejarlas sin el descuento que tiene
        cualquiera que use la app.
        """
        if self.segmento_app and self.segmento_app.activo:
            return self.segmento_app
        return SegmentoApp.objects.filter(
            centro_estetica_id=self.centro_estetica_id,
            es_predeterminado=True,
            activo=True,
        ).first()

    @property
    def descuento_app(self):
        """
        Porcentaje de descuento de la app para esta clienta.

        Es EL número, y tiene un solo origen a propósito: el mismo que la app
        usa para mostrar los precios es el que después se materializa como cupón
        en Tienda Nube. Si se calculara en dos lados, la clienta vería un precio
        y pagaría otro, que es la trampa del §6.1.
        """
        segmento = self.segmento_app_efectivo
        return segmento.porcentaje_descuento if segmento else Decimal('0.00')


class HistorialCliente(models.Model):
    """
    Registro histórico de tratamientos y servicios realizados
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    servicio = models.ForeignKey(
        'servicios.Servicio',
        on_delete=models.SET_NULL,
        null=True,
        related_name='historiales'
    )
    profesional = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='historiales_atendidos'
    )

    # Información del tratamiento
    fecha = models.DateTimeField()
    observaciones = models.TextField(blank=True)
    resultado = models.TextField(blank=True)

    # Fotos antes/después
    foto_antes = models.ImageField(upload_to='tratamientos/antes/', null=True, blank=True)
    foto_despues = models.ImageField(upload_to='tratamientos/despues/', null=True, blank=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historial de Cliente'
        verbose_name_plural = 'Historiales de Clientes'
        ordering = ['-fecha']

    def __str__(self):
        servicio_nombre = self.servicio.nombre if self.servicio else "Servicio eliminado"
        return f"{self.cliente.nombre_completo} - {servicio_nombre} - {self.fecha.strftime('%d/%m/%Y')}"


class PlanTratamiento(models.Model):
    """
    E) Plan de tratamiento para el cliente
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='planes_tratamiento'
    )

    # Información del plan
    tratamiento_sugerido = models.TextField(help_text="Tratamiento sugerido (resumen)")
    frecuencia = models.CharField(max_length=100, blank=True, help_text="Ej: semanal / quincenal / mensual")
    sesiones_estimadas = models.IntegerField(null=True, blank=True, help_text="Número de sesiones estimadas")
    indicaciones = models.TextField(blank=True, help_text="Indicaciones / homecare / post tratamiento")
    proximo_turno = models.DateTimeField(null=True, blank=True, help_text="Fecha y hora del próximo turno")

    # Auditoría
    creado_por = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='planes_creados'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plan de Tratamiento'
        verbose_name_plural = 'Planes de Tratamiento'
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.cliente.nombre_completo} - Plan {self.creado_en.strftime('%d/%m/%Y')}"


class RutinaCuidado(models.Model):
    """
    F) Rutina de cuidado recomendada para el cliente
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='rutinas_cuidado'
    )

    # Rutina diurna
    rutina_diurna_pasos = models.TextField(blank=True, help_text="Pasos de la rutina diurna")
    rutina_diurna_productos = models.TextField(blank=True, help_text="Productos recomendados para rutina diurna")

    # Rutina nocturna
    rutina_nocturna_pasos = models.TextField(blank=True, help_text="Pasos de la rutina nocturna")
    rutina_nocturna_productos = models.TextField(blank=True, help_text="Productos recomendados para rutina nocturna")

    # Auditoría
    creado_por = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='rutinas_creadas'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    activa = models.BooleanField(default=True, help_text="¿Es la rutina activa actual?")

    class Meta:
        verbose_name = 'Rutina de Cuidado'
        verbose_name_plural = 'Rutinas de Cuidado'
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.cliente.nombre_completo} - Rutina {self.creado_en.strftime('%d/%m/%Y')}"


class RutinaItem(models.Model):
    """
    Paso estructurado de una RutinaCuidado (modelo híbrido).

    ``paso`` es texto libre; ``producto`` linkea opcionalmente al catálogo (para
    mostrar precio/foto en la app y, a futuro, comprar/recompra). ``producto_texto``
    permite nombrar un producto que todavía no está en el catálogo.

    Las rutinas viejas sin items siguen funcionando por los TextField legacy de
    ``RutinaCuidado``; la app usa ``items`` si existen y cae al texto si no.
    """
    class Momento(models.TextChoices):
        DIURNA = 'DIURNA', 'Diurna'
        NOCTURNA = 'NOCTURNA', 'Nocturna'

    rutina = models.ForeignKey(
        RutinaCuidado,
        on_delete=models.CASCADE,
        related_name='items',
    )
    momento = models.CharField(max_length=10, choices=Momento.choices)
    orden = models.PositiveIntegerField(default=0)
    paso = models.CharField(
        max_length=200,
        blank=True,
        help_text="Descripción del paso (ej: Limpieza, Serum, Protector solar)",
    )
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rutina_items',
        help_text="Producto del catálogo (opcional). Habilita precio/foto/compra.",
    )
    producto_texto = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre del producto si no está en el catálogo",
    )
    nota = models.CharField(max_length=300, blank=True, help_text="Indicación adicional")

    class Meta:
        verbose_name = 'Ítem de rutina'
        verbose_name_plural = 'Ítems de rutina'
        ordering = ['momento', 'orden', 'id']

    def __str__(self):
        etiqueta = self.paso or self.producto_texto or (self.producto.nombre if self.producto else '')
        return f"{self.get_momento_display()} · {etiqueta}"


class NotaCliente(models.Model):
    """
    G) Notas del paciente - Registro de notas
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='notas'
    )

    tipo_nota = models.CharField(
        max_length=20,
        choices=[
            ('GENERAL', 'General'),
            ('RECORDATORIO', 'Recordatorio'),
            ('OBSERVACION', 'Observación'),
            ('IMPORTANTE', 'Importante'),
            ('SEGUIMIENTO', 'Seguimiento'),
        ],
        default='GENERAL',
        help_text="Tipo de nota"
    )

    contenido = models.TextField(help_text="Contenido de la nota")

    visible_para = models.CharField(
        max_length=20,
        choices=[
            ('TODOS', 'Todos'),
            ('SOLO_ADMIN', 'Solo Admin'),
            ('SOLO_AUTOR', 'Solo profesional que creó'),
        ],
        default='TODOS',
        help_text="Visibilidad de la nota"
    )

    destacada = models.BooleanField(default=False, help_text="¿Nota importante destacada?")

    # Auditoría
    autor = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='notas_creadas'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Nota de Cliente'
        verbose_name_plural = 'Notas de Clientes'
        ordering = ['-destacada', '-creado_en']  # Destacadas primero, luego más recientes

    def __str__(self):
        return f"{self.cliente.nombre_completo} - {self.tipo_nota} - {self.creado_en.strftime('%d/%m/%Y %H:%M')}"


# ============================================================
# App Mobile Cliente - Vinculación de cuentas
# ============================================================

# Alfabeto sin caracteres ambiguos (sin 0/O, 1/I/L) para códigos legibles de boca en boca
_CODIGO_ALFABETO = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def _segmento_codigo(longitud=4):
    """Genera un segmento aleatorio para un código de invitación."""
    return ''.join(secrets.choice(_CODIGO_ALFABETO) for _ in range(longitud))


class UsuarioClienteManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario


class UsuarioCliente(AbstractBaseUser):
    """
    Cuenta de la app mobile del cliente. Es una identidad SEPARADA del ``Usuario`` (staff):
    no es ``AUTH_USER_MODEL`` y tiene su propia autenticación JWT en ``client_api``.

    Multi-centro (M2M): una misma cuenta puede vincularse a fichas ``Cliente`` de varios
    centros a través de ``VinculacionCliente``. La "pertenencia" a un centro se deriva de
    sus vinculaciones, no de un FK directo.
    """
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100, blank=True)
    apellido = models.CharField(max_length=100, blank=True)
    email_verificado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    # Los push tokens NO viven acá: una cuenta puede tener varios teléfonos.
    # Ver ``apps.notificaciones.models.DispositivoPush`` (related_name
    # ``dispositivos_push``).

    # Timestamps (last_login lo provee AbstractBaseUser)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    clientes = models.ManyToManyField(
        Cliente,
        through='VinculacionCliente',
        related_name='usuarios_app',
        blank=True,
    )

    objects = UsuarioClienteManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Usuario de App (Cliente)'
        verbose_name_plural = 'Usuarios de App (Clientes)'
        ordering = ['email']

    def __str__(self):
        return self.email

    @property
    def is_active(self):
        """Alias requerido por DRF/simplejwt; mapea al campo ``activo``."""
        return self.activo

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip() or self.email

    @property
    def centros(self):
        """Centros de estética a los que la cuenta tiene acceso (vía vinculaciones)."""
        return CentroEstetica.objects.filter(
            clientes__vinculaciones__usuario_cliente=self
        ).distinct()


class VinculacionCliente(models.Model):
    """
    Vínculo entre una cuenta de app (``UsuarioCliente``) y una ficha ``Cliente`` de un centro.
    Tabla intermedia del M2M: una cuenta puede tener varias vinculaciones (multi-centro),
    pero no puede vincularse dos veces al mismo ``Cliente``.
    """
    class Metodo(models.TextChoices):
        CODIGO_INVITACION = 'CODIGO_INVITACION', 'Código de invitación'
        INVITACION_STAFF = 'INVITACION_STAFF', 'Invitación manual por staff'
        REGISTRO_NUEVO = 'REGISTRO_NUEVO', 'Registro como cliente nuevo'
        AUTO_MATCH = 'AUTO_MATCH', 'Match automático al registrarse'
        MERGE_MANUAL = 'MERGE_MANUAL', 'Consolidación manual'

    usuario_cliente = models.ForeignKey(
        UsuarioCliente,
        on_delete=models.CASCADE,
        related_name='vinculaciones'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='vinculaciones'
    )
    metodo_vinculacion = models.CharField(max_length=20, choices=Metodo.choices)
    vinculado_en = models.DateTimeField(auto_now_add=True)
    vinculado_por = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vinculaciones_realizadas'
    )

    class Meta:
        verbose_name = 'Vinculación de Cliente'
        verbose_name_plural = 'Vinculaciones de Clientes'
        ordering = ['-vinculado_en']
        unique_together = [('usuario_cliente', 'cliente')]

    def __str__(self):
        return f"{self.usuario_cliente.email} ↔ {self.cliente.nombre_completo}"


class CodigoInvitacion(models.Model):
    """
    Código único de un solo uso para vincular una cuenta de app a un ``Cliente`` existente.
    Lo genera el staff desde la ficha del cliente y se lo entrega al cliente (email, ticket
    o verbal). Válido por ``VIGENCIA_HORAS`` horas.
    """
    VIGENCIA_HORAS = 72

    codigo = models.CharField(max_length=16, unique=True, db_index=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='codigos_invitacion'
    )
    generado_por = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='codigos_generados'
    )
    generado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado_en = models.DateTimeField(null=True, blank=True)
    usado_por = models.ForeignKey(
        UsuarioCliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='codigos_usados'
    )

    class Meta:
        verbose_name = 'Código de Invitación'
        verbose_name_plural = 'Códigos de Invitación'
        ordering = ['-generado_en']
        indexes = [
            models.Index(fields=['cliente', 'usado_en']),
        ]

    def __str__(self):
        return f"{self.codigo} → {self.cliente.nombre_completo} ({self.estado})"

    @property
    def esta_expirado(self):
        return timezone.now() >= self.expira_en

    @property
    def esta_usado(self):
        return self.usado_en is not None

    @property
    def esta_vigente(self):
        return not self.esta_usado and not self.esta_expirado

    @property
    def estado(self):
        if self.esta_usado:
            return 'USADO'
        if self.esta_expirado:
            return 'EXPIRADO'
        return 'VIGENTE'

    def _prefijo_centro(self):
        nombre = self.cliente.centro_estetica.nombre or 'APP'
        letras = ''.join(c for c in nombre.upper() if c.isalpha())
        return letras[:3] or 'APP'

    @classmethod
    def _generar_codigo_unico(cls, prefijo='APP'):
        while True:
            codigo = f"{prefijo}-{_segmento_codigo()}-{_segmento_codigo()}"
            if not cls.objects.filter(codigo=codigo).exists():
                return codigo

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self._generar_codigo_unico(self._prefijo_centro())
        if not self.expira_en:
            self.expira_en = timezone.now() + timedelta(hours=self.VIGENCIA_HORAS)
        super().save(*args, **kwargs)

    def marcar_usado(self, usuario_cliente):
        """Marca el código como consumido por una cuenta de app."""
        self.usado_en = timezone.now()
        self.usado_por = usuario_cliente
        self.save(update_fields=['usado_en', 'usado_por'])


class CodigoRecuperacion(models.Model):
    """
    Código de un solo uso para restablecer la contraseña de una cuenta de app.

    Es de seis dígitos y no un enlace, a propósito: la clienta lo tipea en la app
    y no hace falta configurar deep links ni depender de que el cliente de mail
    respete el esquema. Un enlace que abre el navegador equivocado no lleva a
    ninguna parte; un número siempre se puede copiar.

    **Se guarda hasheado.** Con seis dígitos el hash no es una gran barrera
    —el espacio es chico—, así que la protección real son las otras tres: vive
    quince minutos, admite cinco intentos y el endpoint está limitado por
    throttle. El hash es la cuarta capa, para que un volcado de la base no
    entregue códigos vivos en texto plano.

    Pedir uno nuevo **borra los anteriores sin usar**: si no, quedan varios
    válidos a la vez y cada uno es una puerta más. No se guarda historial porque
    de un código quemado no hay nada que auditar.
    """
    VIGENCIA_MINUTOS = 15
    MAX_INTENTOS = 5
    LONGITUD = 6

    usuario_cliente = models.ForeignKey(
        UsuarioCliente,
        on_delete=models.CASCADE,
        related_name='codigos_recuperacion',
    )
    codigo_hash = models.CharField(max_length=128)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado_en = models.DateTimeField(null=True, blank=True)
    intentos = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Código de recuperación'
        verbose_name_plural = 'Códigos de recuperación'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['usuario_cliente', 'usado_en']),
        ]

    def __str__(self):
        return f"Recuperación de {self.usuario_cliente.email} ({self.estado})"

    @property
    def esta_expirado(self):
        return timezone.now() >= self.expira_en

    @property
    def esta_usado(self):
        return self.usado_en is not None

    @property
    def sin_intentos(self):
        return self.intentos >= self.MAX_INTENTOS

    @property
    def esta_vigente(self):
        return not self.esta_usado and not self.esta_expirado and not self.sin_intentos

    @property
    def estado(self):
        if self.esta_usado:
            return 'USADO'
        if self.esta_expirado:
            return 'EXPIRADO'
        if self.sin_intentos:
            return 'BLOQUEADO'
        return 'VIGENTE'

    @classmethod
    def emitir(cls, usuario_cliente):
        """
        Crea un código nuevo y devuelve ``(instancia, codigo_en_claro)``.

        El código en claro se devuelve porque es la **única** oportunidad de
        verlo: en la base solo queda el hash. Se manda por mail y se descarta.
        """
        cls.objects.filter(usuario_cliente=usuario_cliente, usado_en__isnull=True).delete()

        codigo = f"{secrets.randbelow(10 ** cls.LONGITUD):0{cls.LONGITUD}d}"
        instancia = cls.objects.create(
            usuario_cliente=usuario_cliente,
            codigo_hash=make_password(codigo),
            expira_en=timezone.now() + timedelta(minutes=cls.VIGENCIA_MINUTOS),
        )
        return instancia, codigo

    def verificar(self, codigo):
        """
        ¿Es este el código? Cada intento cuenta, acierte o no.

        Contar también los aciertos es intencional: si no, un atacante que da con
        el código correcto en el último intento no consumiría nada y podría
        reusarlo. El uso lo cierra `marcar_usado`.
        """
        if not self.esta_vigente:
            return False

        self.intentos += 1
        self.save(update_fields=['intentos'])
        return check_password(codigo, self.codigo_hash)

    def marcar_usado(self):
        self.usado_en = timezone.now()
        self.save(update_fields=['usado_en'])

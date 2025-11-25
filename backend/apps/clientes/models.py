from django.db import models
from apps.empleados.models import CentroEstetica


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

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


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

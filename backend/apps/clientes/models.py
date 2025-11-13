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

    # Información médica y preferencias
    alergias = models.TextField(blank=True, help_text="Alergias o sensibilidades")
    contraindicaciones = models.TextField(blank=True)
    notas_medicas = models.TextField(blank=True)
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

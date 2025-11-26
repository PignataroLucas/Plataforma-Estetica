from django.contrib.auth.models import AbstractUser
from django.db import models


class CentroEstetica(models.Model):
    """
    Tenant principal - cada centro de estética es una instancia separada lógicamente
    """
    nombre = models.CharField(max_length=200)
    razon_social = models.CharField(max_length=200, blank=True)
    cuit = models.CharField(max_length=13, blank=True, help_text="CUIT/CUIL del centro")
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    direccion = models.CharField(max_length=300, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=100, default='Argentina')

    # Configuración
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    activo = models.BooleanField(default=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Centro Estética'
        verbose_name_plural = 'Centros de Estética'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Sucursal(models.Model):
    """
    Múltiples locaciones por centro de estética
    """
    centro_estetica = models.ForeignKey(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='sucursales'
    )
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=300)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    # Ubicación
    ciudad = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10, blank=True)

    # Configuración
    activa = models.BooleanField(default=True)
    es_principal = models.BooleanField(default=False)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['centro_estetica', 'nombre']
        unique_together = [['centro_estetica', 'nombre']]

    def __str__(self):
        return f"{self.centro_estetica.nombre} - {self.nombre}"


class Usuario(AbstractUser):
    """
    Usuario personalizado con roles y permisos para el sistema
    """
    class Rol(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador/Dueño'
        MANAGER = 'MANAGER', 'Manager'
        EMPLEADO = 'EMPLEADO', 'Empleado Básico'

    # Relaciones
    centro_estetica = models.ForeignKey(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='usuarios',
        null=True,
        blank=True
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'
    )

    # Información personal
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    foto = models.ImageField(upload_to='usuarios/', null=True, blank=True)

    # Rol y permisos
    rol = models.CharField(
        max_length=10,
        choices=Rol.choices,
        default=Rol.EMPLEADO
    )

    # Información laboral
    fecha_ingreso = models.DateField(null=True, blank=True)
    especialidades = models.TextField(blank=True, help_text="Especialidades del empleado")
    sueldo_mensual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Sueldo mensual del empleado"
    )
    activo = models.BooleanField(default=True)

    # Horario laboral
    horario_inicio = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de inicio del día laboral (ej: 09:00)"
    )
    horario_fin = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de fin del día laboral (ej: 18:00)"
    )
    dias_laborales = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de días laborales: ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']"
    )
    intervalo_minutos = models.PositiveIntegerField(
        default=30,
        help_text="Intervalo en minutos para la agenda (granularidad de slots)"
    )

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    # Sobrescribir relaciones de AbstractUser para evitar conflictos
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='usuario_set',
        related_query_name='usuario',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='usuario_set',
        related_query_name='usuario',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN

    @property
    def es_manager(self):
        return self.rol in [self.Rol.ADMIN, self.Rol.MANAGER]


# TEMPORAL: Comision comentado para evitar dependencia circular
# Se agregará en una migración posterior
# class Comision(models.Model):
#     """
#     Sistema de comisiones para empleados
#     Nota: Simplificado para MVP - solo % por servicio
#     """
#     usuario = models.ForeignKey(
#         Usuario,
#         on_delete=models.CASCADE,
#         related_name='comisiones'
#     )
#
#     # Relación con turno o venta de producto
#     turno = models.ForeignKey(
#         'turnos.Turno',
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name='comisiones'
#     )
#
#     # Cálculo de comisión
#     monto_base = models.DecimalField(max_digits=10, decimal_places=2)
#     porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
#     monto_comision = models.DecimalField(max_digits=10, decimal_places=2)
#
#     # Estado de pago
#     pagada = models.BooleanField(default=False)
#     fecha_pago = models.DateField(null=True, blank=True)
#
#     # Notas
#     notas = models.TextField(blank=True)
#
#     # Timestamps
#     creado_en = models.DateTimeField(auto_now_add=True)
#     actualizado_en = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         verbose_name = 'Comisión'
#         verbose_name_plural = 'Comisiones'
#         ordering = ['-creado_en']
#
#     def __str__(self):
#         return f"Comisión {self.usuario.get_full_name()} - ${self.monto_comision}"
#
#     def save(self, *args, **kwargs):
#         # Calcular monto de comisión automáticamente
#         self.monto_comision = self.monto_base * (self.porcentaje / 100)
#         super().save(*args, **kwargs)

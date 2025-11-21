from django.db import models
from apps.empleados.models import Sucursal


class MaquinaAlquilada(models.Model):
    """
    Máquinas/equipos alquilados que se usan para servicios.
    El costo de alquiler es POR DÍA.
    """
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='maquinas_alquiladas'
    )
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre de la máquina (ej: Liposonix Pro)"
    )
    descripcion = models.TextField(blank=True)
    costo_diario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo de alquiler por DÍA"
    )
    proveedor = models.CharField(
        max_length=200,
        blank=True,
        help_text="Empresa que alquila la máquina"
    )
    activa = models.BooleanField(default=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Máquina Alquilada'
        verbose_name_plural = 'Máquinas Alquiladas'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['sucursal', 'activa']),
        ]

    def __str__(self):
        return f"{self.nombre} - ${self.costo_diario}/día"


class AlquilerMaquina(models.Model):
    """
    Registro de alquileres de máquinas programados.
    Permite control sobre cuándo se alquila realmente la máquina.

    Estados:
    - PROGRAMADO: Alquiler planeado pero no confirmado
    - CONFIRMADO: Alquiler confirmado, se cobrará al completar turnos
    - CANCELADO: Alquiler cancelado, no se cobrará
    - COBRADO: Ya se generó el gasto en finanzas
    """

    class Estado(models.TextChoices):
        PROGRAMADO = 'PROGRAMADO', 'Programado'
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        COBRADO = 'COBRADO', 'Cobrado'

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='alquileres_maquinas'
    )
    maquina = models.ForeignKey(
        MaquinaAlquilada,
        on_delete=models.PROTECT,
        related_name='alquileres'
    )
    fecha = models.DateField(
        help_text="Fecha del alquiler"
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROGRAMADO
    )
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo del alquiler (se copia del costo_diario de la máquina)"
    )
    notas = models.TextField(blank=True)

    # Referencias
    transaccion_gasto = models.ForeignKey(
        'finanzas.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alquiler_maquina',
        help_text="Transacción de gasto generada"
    )

    # Auditoría
    creado_por = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='alquileres_creados'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Alquiler de Máquina'
        verbose_name_plural = 'Alquileres de Máquinas'
        ordering = ['-fecha']
        unique_together = [['maquina', 'fecha', 'sucursal']]
        indexes = [
            models.Index(fields=['sucursal', 'fecha', 'estado']),
            models.Index(fields=['maquina', 'fecha']),
        ]

    def __str__(self):
        return f"{self.maquina.nombre} - {self.fecha.strftime('%d/%m/%Y')} ({self.get_estado_display()})"


class CategoriaServicio(models.Model):
    """
    Categorías para organizar los servicios
    """
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='categorias_servicio'
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Color en formato hexadecimal para visualización en calendario"
    )
    activa = models.BooleanField(default=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría de Servicio'
        verbose_name_plural = 'Categorías de Servicios'
        ordering = ['nombre']
        unique_together = [['sucursal', 'nombre']]

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    """
    Catálogo de servicios ofrecidos (tratamientos, masajes, etc.)
    """
    # Relaciones
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='servicios'
    )
    categoria = models.ForeignKey(
        CategoriaServicio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='servicios'
    )
    maquina_alquilada = models.ForeignKey(
        MaquinaAlquilada,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='servicios',
        help_text="Máquina alquilada necesaria para este servicio"
    )

    # Información básica
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=50, blank=True, help_text="Código interno del servicio")

    # Duración y precio
    duracion_minutos = models.PositiveIntegerField(
        help_text="Duración en minutos del servicio"
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    # Comisión por defecto para empleados
    comision_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Porcentaje de comisión por defecto"
    )

    # Recursos necesarios
    requiere_profesional = models.BooleanField(default=True)
    requiere_equipamiento = models.CharField(
        max_length=200,
        blank=True,
        help_text="Equipamiento o máquina necesaria"
    )

    # Configuración
    activo = models.BooleanField(default=True)
    color = models.CharField(
        max_length=7,
        default='#10B981',
        help_text="Color para calendario (hereda de categoría si existe)"
    )

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['sucursal', 'nombre']
        indexes = [
            models.Index(fields=['sucursal', 'activo']),
        ]

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

    @property
    def color_display(self):
        """Retorna el color de la categoría si existe, sino el propio"""
        return self.categoria.color if self.categoria else self.color

    @property
    def costo_maquina_diario(self):
        """Retorna el costo diario de la máquina si tiene una asociada"""
        return self.maquina_alquilada.costo_diario if self.maquina_alquilada else 0

    @property
    def ganancia_por_servicio(self):
        """Calcula la ganancia neta por servicio (precio - costo máquina)"""
        return self.precio - self.costo_maquina_diario

    @property
    def profit_porcentaje(self):
        """Calcula el porcentaje de profit considerando el costo de la máquina"""
        if self.precio == 0:
            return 0
        return ((self.precio - self.costo_maquina_diario) / self.precio) * 100

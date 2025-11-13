from django.db import models
from apps.empleados.models import Sucursal, Usuario
from apps.clientes.models import Cliente


class CategoriaTransaccion(models.Model):
    """
    Categorías para organizar transacciones financieras
    """
    class TipoCategoria(models.TextChoices):
        INGRESO = 'INGRESO', 'Ingreso'
        GASTO = 'GASTO', 'Gasto'

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='categorias_transaccion'
    )
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(
        max_length=10,
        choices=TipoCategoria.choices
    )
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría de Transacción'
        verbose_name_plural = 'Categorías de Transacciones'
        ordering = ['tipo', 'nombre']
        unique_together = [['sucursal', 'nombre', 'tipo']]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nombre}"


class Transaccion(models.Model):
    """
    Registro de todas las transacciones financieras (ingresos y gastos)
    """
    class TipoTransaccion(models.TextChoices):
        INGRESO_SERVICIO = 'INGRESO_SERVICIO', 'Ingreso por Servicio'
        INGRESO_PRODUCTO = 'INGRESO_PRODUCTO', 'Ingreso por Venta de Producto'
        INGRESO_OTRO = 'INGRESO_OTRO', 'Otro Ingreso'
        GASTO_SUELDO = 'GASTO_SUELDO', 'Gasto - Sueldo'
        GASTO_ALQUILER = 'GASTO_ALQUILER', 'Gasto - Alquiler'
        GASTO_INSUMO = 'GASTO_INSUMO', 'Gasto - Insumos'
        GASTO_SERVICIO = 'GASTO_SERVICIO', 'Gasto - Servicios (luz, agua, etc.)'
        GASTO_MARKETING = 'GASTO_MARKETING', 'Gasto - Marketing'
        GASTO_OTRO = 'GASTO_OTRO', 'Otro Gasto'

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia'
        TARJETA_DEBITO = 'TARJETA_DEBITO', 'Tarjeta de Débito'
        TARJETA_CREDITO = 'TARJETA_CREDITO', 'Tarjeta de Crédito'
        MERCADOPAGO = 'MERCADOPAGO', 'MercadoPago'
        OTRO = 'OTRO', 'Otro'

    # Relaciones
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='transacciones'
    )
    categoria = models.ForeignKey(
        CategoriaTransaccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones',
        help_text="Cliente asociado (solo para ingresos)"
    )

    # Relación con turno o producto
    turno = models.ForeignKey(
        'turnos.Turno',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones'
    )
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones'
    )

    # Información de la transacción
    tipo = models.CharField(
        max_length=20,
        choices=TipoTransaccion.choices,
        db_index=True
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto de la transacción"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO
    )
    fecha = models.DateField(db_index=True)
    descripcion = models.CharField(max_length=300)
    notas = models.TextField(blank=True)

    # Comprobante
    numero_comprobante = models.CharField(max_length=50, blank=True)
    archivo_comprobante = models.FileField(
        upload_to='comprobantes/',
        null=True,
        blank=True
    )

    # Usuario que registró la transacción
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transacciones_registradas'
    )

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-fecha', '-creado_en']
        indexes = [
            models.Index(fields=['sucursal', 'fecha']),
            models.Index(fields=['sucursal', 'tipo', 'fecha']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.monto} - {self.fecha.strftime('%d/%m/%Y')}"

    @property
    def es_ingreso(self):
        """Verifica si la transacción es un ingreso"""
        return self.tipo.startswith('INGRESO_')

    @property
    def es_gasto(self):
        """Verifica si la transacción es un gasto"""
        return self.tipo.startswith('GASTO_')


class CuentaPorCobrar(models.Model):
    """
    Tracking de deudas de clientes
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='cuentas_por_cobrar'
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='cuentas_por_cobrar'
    )
    turno = models.ForeignKey(
        'turnos.Turno',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuentas_por_cobrar'
    )

    # Información de la deuda
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_pendiente = models.DecimalField(max_digits=10, decimal_places=2)

    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    fecha_pago_completo = models.DateField(null=True, blank=True)

    descripcion = models.CharField(max_length=300)
    notas = models.TextField(blank=True)

    # Estado
    pagada = models.BooleanField(default=False)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cuenta por Cobrar'
        verbose_name_plural = 'Cuentas por Cobrar'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"{self.cliente.nombre_completo} - ${self.monto_pendiente} pendiente"

    def save(self, *args, **kwargs):
        # Calcular monto pendiente
        self.monto_pendiente = self.monto_total - self.monto_pagado

        # Actualizar estado de pago
        if self.monto_pendiente <= 0:
            self.pagada = True
            if not self.fecha_pago_completo:
                from django.utils import timezone
                self.fecha_pago_completo = timezone.now().date()

        super().save(*args, **kwargs)

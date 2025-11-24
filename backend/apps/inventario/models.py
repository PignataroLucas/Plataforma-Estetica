from django.db import models
from apps.empleados.models import Sucursal, Usuario


class CategoriaProducto(models.Model):
    """
    Categorías para organizar productos
    """
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='categorias_producto'
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría de Producto'
        verbose_name_plural = 'Categorías de Productos'
        ordering = ['nombre']
        unique_together = [['sucursal', 'nombre']]

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    """
    Proveedores de productos
    """
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='proveedores'
    )
    nombre = models.CharField(max_length=200)
    razon_social = models.CharField(max_length=200, blank=True)
    cuit = models.CharField(max_length=13, blank=True)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    sitio_web = models.URLField(blank=True)
    notas = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Inventario de productos (para reventa y uso interno)
    """
    class TipoProducto(models.TextChoices):
        REVENTA = 'REVENTA', 'Producto de Reventa'
        USO_INTERNO = 'USO_INTERNO', 'Uso Interno'
        INSUMO = 'INSUMO', 'Insumo'

    # Relaciones
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='productos'
    )
    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )

    # Información básica
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    marca = models.CharField(max_length=100, blank=True)
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, unique=True)
    sku = models.CharField(max_length=50, blank=True)
    tipo = models.CharField(
        max_length=15,
        choices=TipoProducto.choices,
        default=TipoProducto.REVENTA
    )

    # Stock
    stock_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cantidad actual en stock"
    )
    stock_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Nivel mínimo de stock (genera alerta)"
    )
    stock_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Nivel máximo de stock recomendado"
    )
    unidad_medida = models.CharField(
        max_length=20,
        default='UNIDAD',
        help_text="Ej: UNIDAD, ML, GR, KG, etc."
    )

    # Precios
    precio_costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio de compra/costo"
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio de venta al público (mantiene compatibilidad, usar precios específicos por método de pago)"
    )

    # Precios por método de pago (opcionales - si no se especifican, se usa precio_venta)
    precio_efectivo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio de venta en efectivo (generalmente el más bajo)"
    )
    precio_transferencia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio de venta con transferencia bancaria"
    )
    precio_debito = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio de venta con tarjeta de débito"
    )
    precio_credito = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio de venta con tarjeta de crédito - TODO: Implementar precios por cantidad de cuotas"
    )

    # Ofertas y descuentos
    en_oferta = models.BooleanField(
        default=False,
        help_text="¿Este producto está en oferta?"
    )
    precio_oferta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio de venta durante la oferta (opcional)"
    )

    # Configuración
    activo = models.BooleanField(default=True)
    foto = models.ImageField(upload_to='productos/', null=True, blank=True)

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['sucursal', 'nombre']
        indexes = [
            models.Index(fields=['sucursal', 'stock_actual']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.unidad_medida})"

    def get_precio_por_metodo_pago(self, metodo_pago):
        """
        Returns price based on payment method
        Falls back to precio_venta if specific method price is not set
        metodo_pago: 'CASH', 'BANK_TRANSFER', 'DEBIT_CARD', 'CREDIT_CARD'
        """
        precio_map = {
            'CASH': self.precio_efectivo,
            'BANK_TRANSFER': self.precio_transferencia,
            'DEBIT_CARD': self.precio_debito,
            'CREDIT_CARD': self.precio_credito,
        }

        precio = precio_map.get(metodo_pago)

        # If specific price is not set, use precio_venta as fallback
        if precio is None or precio <= 0:
            precio = self.precio_venta

        # Apply offer price if product is on offer
        if self.en_oferta and self.precio_oferta and self.precio_oferta < precio:
            return self.precio_oferta

        return precio

    @property
    def precio_venta_final(self):
        """
        Returns final sale price considering offers
        If product is on offer and has offer price, use it; otherwise use regular price
        For products with payment method prices, this returns the cash price or precio_venta
        """
        if self.en_oferta and self.precio_oferta:
            return self.precio_oferta

        # Use precio_efectivo as primary price if set, otherwise precio_venta
        if self.precio_efectivo and self.precio_efectivo > 0:
            return self.precio_efectivo

        return self.precio_venta

    @property
    def porcentaje_descuento(self):
        """
        Calculates discount percentage if product is on offer
        """
        if self.en_oferta and self.precio_oferta and self.precio_oferta < self.precio_venta:
            descuento = ((self.precio_venta - self.precio_oferta) / self.precio_venta) * 100
            return round(descuento, 2)
        return 0

    @property
    def margen_ganancia(self):
        """
        Calcula el margen de ganancia porcentual basado en precio de efectivo (principal)
        Si no hay precio de efectivo, usa precio_venta
        """
        if self.precio_costo > 0:
            precio_base = self.precio_efectivo if self.precio_efectivo and self.precio_efectivo > 0 else self.precio_venta
            return ((precio_base - self.precio_costo) / self.precio_costo) * 100
        return 0

    @property
    def margen_ganancia_real(self):
        """
        Calculates real profit margin using final sale price (with offers)
        """
        if self.precio_costo > 0:
            return ((self.precio_venta_final - self.precio_costo) / self.precio_costo) * 100
        return 0

    @property
    def stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo


class MovimientoInventario(models.Model):
    """
    Registro de movimientos de inventario (entradas, salidas, ajustes)
    """
    class TipoMovimiento(models.TextChoices):
        ENTRADA = 'ENTRADA', 'Entrada (Compra)'
        SALIDA = 'SALIDA', 'Salida (Venta/Uso)'
        AJUSTE = 'AJUSTE', 'Ajuste de Inventario'
        TRANSFERENCIA_IN = 'TRANSFERENCIA_IN', 'Transferencia Entrada'
        TRANSFERENCIA_OUT = 'TRANSFERENCIA_OUT', 'Transferencia Salida'

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='movimientos'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoMovimiento.choices
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    stock_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    stock_nuevo = models.DecimalField(max_digits=10, decimal_places=2)

    # Información adicional
    motivo = models.CharField(max_length=200, blank=True)
    notas = models.TextField(blank=True)
    costo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo unitario (para ENTRADA/compras)"
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio de venta unitario (para SALIDA/ventas). Si es null, usa precio_venta_final del producto"
    )

    # Usuario que realizó el movimiento
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='movimientos_inventario'
    )

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre} ({self.cantidad})"

    @property
    def monto_total(self):
        """
        Calculates total amount of the movement
        For ENTRADA: quantity × cost per unit
        For SALIDA: quantity × sale price per unit
        """
        if self.tipo == 'ENTRADA' and self.costo_unitario:
            return self.cantidad * self.costo_unitario
        elif self.tipo == 'SALIDA':
            # Use custom price if provided, otherwise use product's final price
            precio = self.precio_unitario if self.precio_unitario else self.producto.precio_venta_final
            return self.cantidad * precio
        return 0

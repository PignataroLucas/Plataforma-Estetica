"""
Django Admin configuration for Inventory module
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import CategoriaProducto, Proveedor, Producto, MovimientoInventario


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    """Admin for product categories"""
    list_display = ['nombre', 'sucursal', 'activa', 'creado_en']
    list_filter = ['activa', 'sucursal']
    search_fields = ['nombre', 'descripcion']
    ordering = ['sucursal', 'nombre']


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    """Admin for suppliers"""
    list_display = ['nombre', 'sucursal', 'telefono', 'email', 'activo']
    list_filter = ['activo', 'sucursal']
    search_fields = ['nombre', 'razon_social', 'cuit', 'email']
    ordering = ['sucursal', 'nombre']

    fieldsets = (
        ('Información Básica', {
            'fields': ('sucursal', 'nombre', 'razon_social', 'cuit')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'direccion', 'sitio_web')
        }),
        ('Notas', {
            'fields': ('notas', 'activo')
        }),
    )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Admin for products with offer management"""
    list_display = [
        'nombre',
        'sucursal',
        'categoria',
        'stock_actual_formatted',
        'precio_costo_formatted',
        'precio_venta_formatted',
        'offer_badge',
        'stock_status',
        'activo'
    ]
    list_filter = ['tipo', 'en_oferta', 'activo', 'sucursal', 'categoria']
    search_fields = ['nombre', 'descripcion', 'marca', 'codigo_barras', 'sku']
    ordering = ['sucursal', 'nombre']
    readonly_fields = ['creado_en', 'actualizado_en', 'margen_ganancia', 'margen_ganancia_real', 'porcentaje_descuento']

    fieldsets = (
        ('Información Básica', {
            'fields': ('sucursal', 'nombre', 'descripcion', 'marca', 'tipo', 'categoria', 'proveedor')
        }),
        ('Identificación', {
            'fields': ('codigo_barras', 'sku')
        }),
        ('Stock', {
            'fields': ('stock_actual', 'stock_minimo', 'stock_maximo', 'unidad_medida')
        }),
        ('Precios', {
            'fields': (
                'precio_costo',
                'precio_venta',
                'margen_ganancia'
            )
        }),
        ('Ofertas y Descuentos', {
            'fields': (
                'en_oferta',
                'precio_oferta',
                'porcentaje_descuento',
                'margen_ganancia_real'
            ),
            'description': 'Activa ofertas y descuentos temporales. El precio de oferta se usará automáticamente en las ventas.'
        }),
        ('Configuración', {
            'fields': ('activo', 'foto')
        }),
        ('Timestamps', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )

    def stock_actual_formatted(self, obj):
        """Format stock with units and color coding"""
        if obj.stock_bajo:
            color = 'red'
            icon = '⚠️'
        else:
            color = 'green'
            icon = '✓'
        return format_html(
            '<span style="color: {};">{} {} {}</span>',
            color,
            icon,
            obj.stock_actual,
            obj.unidad_medida
        )
    stock_actual_formatted.short_description = 'Stock'

    def precio_costo_formatted(self, obj):
        """Format cost price"""
        return format_html('${:,.2f}', obj.precio_costo)
    precio_costo_formatted.short_description = 'P. Costo'

    def precio_venta_formatted(self, obj):
        """Format sale price with offer indicator"""
        if obj.en_oferta and obj.precio_oferta:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">${:,.2f}</span><br>'
                '<span style="color: #10B981; font-weight: bold;">${:,.2f}</span>',
                obj.precio_venta,
                obj.precio_oferta
            )
        return format_html('<span style="color: #059669;">${:,.2f}</span>', obj.precio_venta)
    precio_venta_formatted.short_description = 'P. Venta'

    def offer_badge(self, obj):
        """Show offer badge if product is on offer"""
        if obj.en_oferta and obj.precio_oferta:
            return format_html(
                '<span style="background-color: #FEE2E2; color: #DC2626; padding: 3px 8px; border-radius: 4px; font-weight: bold;">'
                '🏷️ {}% OFF'
                '</span>',
                obj.porcentaje_descuento
            )
        return '-'
    offer_badge.short_description = 'Oferta'

    def stock_status(self, obj):
        """Show stock status badge"""
        if obj.stock_bajo:
            return format_html(
                '<span style="background-color: #FEE2E2; color: #DC2626; padding: 3px 8px; border-radius: 4px;">'
                'Stock Bajo'
                '</span>'
            )
        return format_html(
            '<span style="background-color: #D1FAE5; color: #065F46; padding: 3px 8px; border-radius: 4px;">'
            'OK'
            '</span>'
        )
    stock_status.short_description = 'Estado'


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    """Admin for inventory movements (purchases and sales)"""
    list_display = [
        'creado_en',
        'tipo_badge',
        'producto',
        'cantidad_formatted',
        'precio_formatted',
        'monto_total_formatted',
        'usuario'
    ]
    list_filter = ['tipo', 'producto__sucursal', 'creado_en']
    search_fields = ['producto__nombre', 'motivo', 'notas']
    ordering = ['-creado_en']
    readonly_fields = ['stock_anterior', 'stock_nuevo', 'creado_en', 'monto_total']

    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('tipo', 'producto', 'cantidad', 'motivo')
        }),
        ('Precios', {
            'fields': ('costo_unitario', 'precio_unitario', 'monto_total'),
            'description': 'Para ENTRADA (compras): usar costo_unitario. Para SALIDA (ventas): usar precio_unitario'
        }),
        ('Stock', {
            'fields': ('stock_anterior', 'stock_nuevo')
        }),
        ('Información Adicional', {
            'fields': ('notas', 'usuario', 'creado_en')
        }),
    )

    def tipo_badge(self, obj):
        """Show movement type with colored badge"""
        colors = {
            'ENTRADA': '#10B981',  # Green
            'SALIDA': '#EF4444',   # Red
            'AJUSTE': '#F59E0B',   # Orange
            'TRANSFERENCIA_IN': '#3B82F6',   # Blue
            'TRANSFERENCIA_OUT': '#8B5CF6',  # Purple
        }
        color = colors.get(obj.tipo, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">'
            '{}'
            '</span>',
            color,
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'

    def cantidad_formatted(self, obj):
        """Format quantity with units"""
        return f"{obj.cantidad} {obj.producto.unidad_medida}"
    cantidad_formatted.short_description = 'Cantidad'

    def precio_formatted(self, obj):
        """Show relevant price based on movement type"""
        if obj.tipo == 'ENTRADA' and obj.costo_unitario:
            return format_html('<span style="color: #EF4444;">${:,.2f}/u</span>', obj.costo_unitario)
        elif obj.tipo == 'SALIDA':
            precio = obj.precio_unitario if obj.precio_unitario else obj.producto.precio_venta_final
            return format_html('<span style="color: #10B981;">${:,.2f}/u</span>', precio)
        return '-'
    precio_formatted.short_description = 'Precio Unit.'

    def monto_total_formatted(self, obj):
        """Format total amount"""
        if obj.monto_total > 0:
            color = '#EF4444' if obj.tipo == 'ENTRADA' else '#10B981'
            return format_html(
                '<span style="color: {}; font-weight: bold;">${:,.2f}</span>',
                color,
                obj.monto_total
            )
        return '-'
    monto_total_formatted.short_description = 'Monto Total'

from rest_framework import serializers
from .models import Producto, CategoriaProducto, Proveedor, MovimientoInventario


class CategoriaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProducto
        fields = ['id', 'sucursal', 'nombre', 'descripcion', 'activa', 'creado_en', 'actualizado_en']
        read_only_fields = ['id', 'sucursal', 'creado_en', 'actualizado_en']


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = [
            'id', 'sucursal', 'nombre', 'razon_social', 'cuit', 'telefono',
            'email', 'direccion', 'sitio_web', 'notas', 'activo',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'sucursal', 'creado_en', 'actualizado_en']


class ProductoListSerializer(serializers.ModelSerializer):
    """Serializer para listado de productos (con datos anidados)"""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    margen_ganancia = serializers.ReadOnlyField()
    stock_bajo = serializers.ReadOnlyField()

    class Meta:
        model = Producto
        fields = [
            'id', 'sucursal', 'categoria', 'categoria_nombre',
            'proveedor', 'proveedor_nombre', 'nombre', 'descripcion',
            'marca', 'codigo_barras', 'sku', 'tipo',
            'stock_actual', 'stock_minimo', 'stock_maximo', 'unidad_medida',
            'precio_costo', 'precio_venta', 'margen_ganancia', 'stock_bajo',
            'activo', 'foto', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'sucursal', 'margen_ganancia', 'stock_bajo', 'creado_en', 'actualizado_en']


class ProductoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de producto (con objetos completos)"""
    categoria_data = CategoriaProductoSerializer(source='categoria', read_only=True)
    proveedor_data = ProveedorSerializer(source='proveedor', read_only=True)
    margen_ganancia = serializers.ReadOnlyField()
    stock_bajo = serializers.ReadOnlyField()

    class Meta:
        model = Producto
        fields = [
            'id', 'sucursal', 'categoria', 'categoria_data',
            'proveedor', 'proveedor_data', 'nombre', 'descripcion',
            'marca', 'codigo_barras', 'sku', 'tipo',
            'stock_actual', 'stock_minimo', 'stock_maximo', 'unidad_medida',
            'precio_costo', 'precio_venta', 'margen_ganancia', 'stock_bajo',
            'activo', 'foto', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'sucursal', 'margen_ganancia', 'stock_bajo', 'creado_en', 'actualizado_en']


class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar productos"""
    class Meta:
        model = Producto
        fields = [
            'id', 'categoria', 'proveedor', 'nombre', 'descripcion',
            'marca', 'codigo_barras', 'sku', 'tipo',
            'stock_actual', 'stock_minimo', 'stock_maximo', 'unidad_medida',
            'precio_costo', 'precio_venta', 'activo', 'foto'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """Validar que el precio de venta sea mayor que el costo"""
        precio_costo = data.get('precio_costo')
        precio_venta = data.get('precio_venta')

        if precio_costo and precio_venta and precio_venta < precio_costo:
            raise serializers.ValidationError({
                'precio_venta': "El precio de venta debe ser mayor o igual al precio de costo"
            })
        return data

    def validate_stock_minimo(self, value):
        """Validar que el stock mínimo sea positivo"""
        if value < 0:
            raise serializers.ValidationError("El stock mínimo no puede ser negativo")
        return value


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    """Serializer para movimientos de inventario"""
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'id', 'producto', 'producto_nombre', 'tipo', 'cantidad',
            'stock_anterior', 'stock_nuevo', 'motivo', 'notas',
            'costo_unitario', 'usuario', 'usuario_nombre', 'creado_en'
        ]
        read_only_fields = ['id', 'stock_anterior', 'stock_nuevo', 'usuario', 'creado_en']


class AjustarStockSerializer(serializers.Serializer):
    """Serializer para ajustar stock de un producto"""
    tipo_movimiento = serializers.ChoiceField(choices=MovimientoInventario.TipoMovimiento.choices)
    cantidad = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    motivo = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notas = serializers.CharField(required=False, allow_blank=True)
    costo_unitario = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

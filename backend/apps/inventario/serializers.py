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
            'precio_costo', 'precio_venta',
            'precio_efectivo', 'precio_transferencia', 'precio_debito', 'precio_credito',
            'margen_ganancia', 'stock_bajo',
            'activo', 'foto', 'foto_thumb', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'sucursal', 'margen_ganancia', 'stock_bajo', 'foto_thumb',
            'creado_en', 'actualizado_en'
        ]


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
            'precio_costo', 'precio_venta',
            'precio_efectivo', 'precio_transferencia', 'precio_debito', 'precio_credito',
            'margen_ganancia', 'stock_bajo',
            'activo', 'foto', 'foto_thumb', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'id', 'sucursal', 'margen_ganancia', 'stock_bajo', 'foto_thumb',
            'creado_en', 'actualizado_en'
        ]


class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar productos"""

    # Un multipart no puede mandar "campo vacío" para un archivo, así que sacar
    # la foto necesita una señal propia.
    quitar_foto = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Producto
        fields = [
            'id', 'categoria', 'proveedor', 'nombre', 'descripcion',
            'marca', 'codigo_barras', 'sku', 'tipo',
            'stock_actual', 'stock_minimo', 'stock_maximo', 'unidad_medida',
            'precio_costo', 'precio_venta',
            'precio_efectivo', 'precio_transferencia', 'precio_debito', 'precio_credito',
            'activo', 'foto', 'quitar_foto'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data.pop('quitar_foto', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.pop('quitar_foto', False):
            validated_data['foto'] = None
        return super().update(instance, validated_data)

    def validate_foto(self, value):
        """
        Tope de tamaño, también del lado del servidor.

        El formulario del CRM ya valida, pero el que sube las 31 fotos puede
        estar mandando el original de la cámara y el límite tiene que valer
        aunque la subida no venga del formulario.
        """
        maximo = 5 * 1024 * 1024
        if value and value.size > maximo:
            raise serializers.ValidationError(
                f"La foto no puede superar los 5 MB (pesa "
                f"{value.size / (1024 * 1024):.1f} MB)"
            )
        return value

    def validate(self, data):
        """Validar precios por método de pago"""
        precio_costo = data.get('precio_costo')
        precio_venta = data.get('precio_venta')
        precio_efectivo = data.get('precio_efectivo')
        precio_transferencia = data.get('precio_transferencia')
        precio_debito = data.get('precio_debito')
        precio_credito = data.get('precio_credito')

        errors = {}

        # Validate precio_venta is greater than cost
        if precio_costo and precio_venta and precio_venta < precio_costo:
            errors['precio_venta'] = "El precio de venta debe ser mayor o igual al precio de costo"

        # Validate each payment method price is greater than cost (if specified)
        if precio_costo:
            if precio_efectivo and precio_efectivo < precio_costo:
                errors['precio_efectivo'] = "El precio en efectivo debe ser mayor o igual al precio de costo"
            if precio_transferencia and precio_transferencia < precio_costo:
                errors['precio_transferencia'] = "El precio de transferencia debe ser mayor o igual al precio de costo"
            if precio_debito and precio_debito < precio_costo:
                errors['precio_debito'] = "El precio de débito debe ser mayor o igual al precio de costo"
            if precio_credito and precio_credito < precio_costo:
                errors['precio_credito'] = "El precio de crédito debe ser mayor o igual al precio de costo"

        # Validate SKU uniqueness within the branch
        sku_error = self._validate_sku_uniqueness(data)
        if sku_error:
            errors['sku'] = sku_error

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def _validate_sku_uniqueness(self, data):
        """
        Check the SKU is not already used in the branch.

        The database enforces this through `unique_sku_per_sucursal`, but Django
        does not validate UniqueConstraints that use expressions (this one
        compares uppercased), and DRF does not call full_clean(). Without this
        check a duplicate SKU would surface as an IntegrityError, so a typo
        would return a 500 instead of a field error.

        The SKU is the join key against Conto, so duplicates are worth blocking
        clearly rather than tolerating.
        """
        if 'sku' not in data:
            return None

        sku = (data.get('sku') or '').strip()
        if not sku:
            # Empty SKUs are excluded from the constraint: many may coexist.
            return None

        if self.instance:
            branch = self.instance.sucursal
        else:
            # The serializer can be used without a request (scripts, nested
            # usage), so this must not assume the context is populated.
            request = self.context.get('request')
            branch = getattr(getattr(request, 'user', None), 'sucursal', None)

        if not branch:
            return None

        clash = Producto.objects.filter(sucursal=branch, sku__iexact=sku)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)

        existing = clash.first()
        if existing:
            return (
                f"El código '{sku}' ya lo usa el producto \"{existing.nombre}\" "
                f"en esta sucursal"
            )
        return None

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

from rest_framework import serializers
from apps.finanzas.models import Transaction
from apps.inventario.models import Producto, MovimientoInventario
from apps.turnos.models import Turno
from apps.servicios.models import Servicio
from apps.clientes.models import Cliente
from .models import CierreCaja
from decimal import Decimal


class TransaccionMiCajaSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para transacciones en Mi Caja
    """
    created_by_nombre = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    concepto = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'type', 'amount', 'payment_method', 'date',
            'description', 'notes', 'created_by_nombre', 'cliente_nombre',
            'concepto', 'created_at'
        ]

    def get_created_by_nombre(self, obj):
        if obj.registered_by:
            return obj.registered_by.get_full_name()
        return None

    def get_cliente_nombre(self, obj):
        if obj.client:
            return f"{obj.client.nombre} {obj.client.apellido}"
        return None

    def get_concepto(self, obj):
        """Retorna descripción del concepto según el tipo"""
        if obj.appointment:
            return f"{obj.appointment.servicio.nombre}"
        elif obj.product:
            return f"{obj.product.nombre}"
        return obj.description


class VentaUnificadaItemSerializer(serializers.Serializer):
    """
    Serializer for individual item in unified sale.
    Supports: producto, servicio (from turno), servicio_directo (without turno)
    """
    tipo = serializers.ChoiceField(choices=['producto', 'servicio', 'servicio_directo'])
    producto_id = serializers.IntegerField(required=False, allow_null=True)
    turno_id = serializers.IntegerField(required=False, allow_null=True)
    servicio_id = serializers.IntegerField(required=False, allow_null=True)
    cantidad = serializers.IntegerField(min_value=1, default=1)
    precio_unitario = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0.01'),
        help_text="Override del precio. Si no se envía, usa el precio del catálogo."
    )
    descuento_porcentaje = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00')
    )

    def validate(self, data):
        tipo = data.get('tipo')

        if tipo == 'producto':
            if not data.get('producto_id'):
                raise serializers.ValidationError({
                    'producto_id': 'Requerido para items de tipo producto'
                })
            try:
                producto = Producto.objects.get(id=data['producto_id'])
                if not producto.activo:
                    raise serializers.ValidationError({
                        'producto_id': 'Producto no activo'
                    })
                cantidad = data.get('cantidad', 1)
                if producto.stock_actual < cantidad:
                    raise serializers.ValidationError({
                        'cantidad': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}'
                    })
            except Producto.DoesNotExist:
                raise serializers.ValidationError({
                    'producto_id': 'Producto no encontrado'
                })

        elif tipo == 'servicio':
            if not data.get('turno_id'):
                raise serializers.ValidationError({
                    'turno_id': 'Requerido para items de tipo servicio'
                })
            try:
                turno = Turno.objects.get(id=data['turno_id'])
                if turno.estado != 'COMPLETADO':
                    raise serializers.ValidationError({
                        'turno_id': 'Solo se pueden cobrar turnos completados'
                    })
                if turno.transactions.filter(type='INCOME_SERVICE').exists():
                    raise serializers.ValidationError({
                        'turno_id': 'Este turno ya tiene un pago registrado'
                    })
            except Turno.DoesNotExist:
                raise serializers.ValidationError({
                    'turno_id': 'Turno no encontrado'
                })

        elif tipo == 'servicio_directo':
            if not data.get('servicio_id'):
                raise serializers.ValidationError({
                    'servicio_id': 'Requerido para servicio directo (sin turno)'
                })
            try:
                servicio = Servicio.objects.get(id=data['servicio_id'])
                if not servicio.activo:
                    raise serializers.ValidationError({
                        'servicio_id': 'Servicio no activo'
                    })
            except Servicio.DoesNotExist:
                raise serializers.ValidationError({
                    'servicio_id': 'Servicio no encontrado'
                })

        return data


class VentaUnificadaSerializer(serializers.Serializer):
    """
    Serializer for unified sale (multiple products and/or services).
    Cliente is optional (supports anonymous/walk-in sales).
    """
    items = VentaUnificadaItemSerializer(many=True)
    cliente_id = serializers.IntegerField(required=False, allow_null=True)
    payment_method = serializers.ChoiceField(choices=Transaction.PaymentMethod.choices)
    notas = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_items(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError('Debe agregar al menos un item')
        return value

    def validate_cliente_id(self, value):
        if value is not None:
            try:
                Cliente.objects.get(id=value)
            except Cliente.DoesNotExist:
                raise serializers.ValidationError("Cliente no encontrado")
        return value


class EditarTransaccionSerializer(serializers.Serializer):
    """
    Serializer para editar una transacción existente de Mi Caja.
    Todos los campos son opcionales (solo se actualizan los enviados).
    """
    transaccion_id = serializers.IntegerField()
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        required=False, min_value=Decimal('0.01')
    )
    payment_method = serializers.ChoiceField(
        choices=Transaction.PaymentMethod.choices,
        required=False
    )
    notas = serializers.CharField(required=False, allow_blank=True)
    cliente_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_cliente_id(self, value):
        if value is not None:
            try:
                Cliente.objects.get(id=value)
            except Cliente.DoesNotExist:
                raise serializers.ValidationError("Cliente no encontrado")
        return value


class EliminarTransaccionSerializer(serializers.Serializer):
    """
    Serializer para eliminar una transacción de Mi Caja.
    Requiere motivo obligatorio.
    """
    transaccion_id = serializers.IntegerField()
    motivo = serializers.CharField(min_length=5, max_length=500)


class CierreCajaSerializer(serializers.ModelSerializer):
    """
    Serializer for CierreCaja model
    """
    empleado_nombre = serializers.SerializerMethodField()
    tiene_diferencia = serializers.BooleanField(read_only=True)
    diferencia_significativa = serializers.BooleanField(read_only=True)

    class Meta:
        model = CierreCaja
        fields = [
            'id', 'empleado', 'empleado_nombre', 'sucursal', 'fecha',
            'total_sistema', 'efectivo_contado', 'diferencia',
            'desglose_metodos', 'notas', 'tiene_diferencia',
            'diferencia_significativa', 'cerrado_en'
        ]
        read_only_fields = ['id', 'total_sistema', 'diferencia', 'desglose_metodos', 'cerrado_en']

    def get_empleado_nombre(self, obj):
        return obj.empleado.get_full_name()


class CierreCajaCreateSerializer(serializers.Serializer):
    """
    Serializer para crear un cierre de caja
    """
    fecha = serializers.DateField()
    efectivo_contado = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    notas = serializers.CharField(required=False, allow_blank=True)

    def validate_fecha(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("No se puede cerrar caja de fecha futura")
        return value

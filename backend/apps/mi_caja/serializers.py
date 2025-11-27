from rest_framework import serializers
from apps.finanzas.models import Transaction
from apps.inventario.models import Producto, MovimientoInventario
from apps.turnos.models import Turno
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
            'description', 'created_by_nombre', 'cliente_nombre',
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


class CobrarTurnoSerializer(serializers.Serializer):
    """
    Serializer para cobrar un turno completado
    """
    turno_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Transaction.PaymentMethod.choices)
    notas = serializers.CharField(required=False, allow_blank=True)

    def validate_turno_id(self, value):
        try:
            turno = Turno.objects.get(id=value)
        except Turno.DoesNotExist:
            raise serializers.ValidationError("Turno no encontrado")

        # Validar que el turno esté completado
        if turno.estado != 'COMPLETADO':
            raise serializers.ValidationError("Solo se pueden cobrar turnos completados")

        # Validar que no tenga transacción de pago asociada
        if turno.transactions.filter(type='INCOME_SERVICE').exists():
            raise serializers.ValidationError("Este turno ya tiene un pago registrado")

        return value


class VenderProductoSerializer(serializers.Serializer):
    """
    Serializer para vender un producto
    """
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)
    cliente_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=Transaction.PaymentMethod.choices)
    descuento_porcentaje = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00')
    )

    def validate_producto_id(self, value):
        try:
            producto = Producto.objects.get(id=value)
        except Producto.DoesNotExist:
            raise serializers.ValidationError("Producto no encontrado")

        if not producto.activo:
            raise serializers.ValidationError("Producto no activo")

        return value

    def validate_cliente_id(self, value):
        try:
            Cliente.objects.get(id=value)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("Cliente no encontrado")

        return value

    def validate(self, data):
        # Validar stock suficiente
        producto = Producto.objects.get(id=data['producto_id'])
        if producto.stock_actual < data['cantidad']:
            raise serializers.ValidationError({
                'cantidad': f'Stock insuficiente. Disponible: {producto.stock_actual}'
            })

        return data


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
        # No permitir cierre futuro
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("No se puede cerrar caja de fecha futura")

        return value

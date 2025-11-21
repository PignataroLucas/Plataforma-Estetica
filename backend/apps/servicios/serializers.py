from rest_framework import serializers
from .models import Servicio, CategoriaServicio, MaquinaAlquilada, AlquilerMaquina
from django.utils import timezone


class MaquinaAlquiladaSerializer(serializers.ModelSerializer):
    """
    Serializer para MaquinaAlquilada
    """
    class Meta:
        model = MaquinaAlquilada
        fields = [
            'id',
            'sucursal',
            'nombre',
            'descripcion',
            'costo_diario',
            'proveedor',
            'activa',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['id', 'sucursal', 'creado_en', 'actualizado_en']


class ServicioSerializer(serializers.ModelSerializer):
    """
    Serializer para Servicio
    Aplica principios SOLID:
    - SRP: Solo serializa datos de Servicio
    - OCP: Extensible via Meta.fields
    - DIP: Depende de abstracciones (ModelSerializer)
    """
    color_display = serializers.ReadOnlyField()
    costo_maquina_diario = serializers.ReadOnlyField()
    ganancia_por_servicio = serializers.ReadOnlyField()
    profit_porcentaje = serializers.ReadOnlyField()
    maquina_nombre = serializers.CharField(source='maquina_alquilada.nombre', read_only=True, allow_null=True)

    class Meta:
        model = Servicio
        fields = [
            'id',
            'sucursal',
            'categoria',
            'maquina_alquilada',
            'maquina_nombre',
            'nombre',
            'descripcion',
            'codigo',
            'duracion_minutos',
            'precio',
            'costo_maquina_diario',
            'ganancia_por_servicio',
            'profit_porcentaje',
            'comision_porcentaje',
            'requiere_profesional',
            'requiere_equipamiento',
            'activo',
            'color',
            'color_display',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = [
            'id',
            'sucursal',
            'creado_en',
            'actualizado_en',
            'color_display',
            'costo_maquina_diario',
            'ganancia_por_servicio',
            'profit_porcentaje',
            'maquina_nombre'
        ]


class CategoriaServicioSerializer(serializers.ModelSerializer):
    """
    Serializer para CategoriaServicio
    """
    class Meta:
        model = CategoriaServicio
        fields = [
            'id',
            'sucursal',
            'nombre',
            'descripcion',
            'color',
            'activa',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['id', 'sucursal', 'creado_en', 'actualizado_en']


class AlquilerMaquinaSerializer(serializers.ModelSerializer):
    """
    Serializer para AlquilerMaquina - Programación de alquileres
    """
    maquina_nombre = serializers.CharField(source='maquina.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tiene_turnos = serializers.SerializerMethodField()

    class Meta:
        model = AlquilerMaquina
        fields = [
            'id',
            'sucursal',
            'maquina',
            'maquina_nombre',
            'fecha',
            'estado',
            'estado_display',
            'costo',
            'notas',
            'transaccion_gasto',
            'tiene_turnos',
            'creado_por',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = [
            'id',
            'sucursal',
            'transaccion_gasto',
            'creado_por',
            'creado_en',
            'actualizado_en',
            'maquina_nombre',
            'estado_display',
            'tiene_turnos'
        ]

    def get_tiene_turnos(self, obj):
        """Check if there are appointments with this machine on this date"""
        from apps.turnos.models import Turno
        return Turno.objects.filter(
            servicio__maquina_alquilada=obj.maquina,
            fecha_hora_inicio__date=obj.fecha,
            sucursal=obj.sucursal
        ).exists()

    def validate(self, data):
        """Validation"""
        # Auto-set cost from machine if not provided
        if 'costo' not in data and 'maquina' in data:
            data['costo'] = data['maquina'].costo_diario

        # Prevent scheduling in the past
        if data.get('fecha') and data['fecha'] < timezone.now().date():
            # Allow if editing existing rental
            if not self.instance:
                raise serializers.ValidationError({
                    'fecha': 'No puedes programar alquileres en fechas pasadas.'
                })

        return data

from rest_framework import serializers
from .models import Servicio, CategoriaServicio, MaquinaAlquilada


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

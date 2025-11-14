from rest_framework import serializers
from .models import Servicio, CategoriaServicio


class ServicioSerializer(serializers.ModelSerializer):
    """
    Serializer para Servicio
    Aplica principios SOLID:
    - SRP: Solo serializa datos de Servicio
    - OCP: Extensible via Meta.fields
    - DIP: Depende de abstracciones (ModelSerializer)
    """
    color_display = serializers.ReadOnlyField()

    class Meta:
        model = Servicio
        fields = [
            'id',
            'sucursal',
            'categoria',
            'nombre',
            'descripcion',
            'codigo',
            'duracion_minutos',
            'precio',
            'comision_porcentaje',
            'requiere_profesional',
            'requiere_equipamiento',
            'activo',
            'color',
            'color_display',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['id', 'sucursal', 'creado_en', 'actualizado_en', 'color_display']


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

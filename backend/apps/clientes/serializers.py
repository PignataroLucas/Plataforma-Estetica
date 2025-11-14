from rest_framework import serializers
from .models import Cliente, HistorialCliente


class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para Cliente
    Aplica principios SOLID:
    - SRP: Solo serializa datos de Cliente
    - OCP: Extensible via Meta.fields
    - DIP: Depende de abstracciones (ModelSerializer)
    """
    nombre_completo = serializers.ReadOnlyField()

    class Meta:
        model = Cliente
        fields = [
            'id',
            'centro_estetica',
            'nombre',
            'apellido',
            'nombre_completo',
            'email',
            'telefono',
            'telefono_alternativo',
            'fecha_nacimiento',
            'direccion',
            'ciudad',
            'provincia',
            'codigo_postal',
            'tipo_documento',
            'numero_documento',
            'alergias',
            'contraindicaciones',
            'notas_medicas',
            'preferencias',
            'foto',
            'acepta_promociones',
            'acepta_whatsapp',
            'activo',
            'creado_en',
            'actualizado_en',
            'ultima_visita',
        ]
        read_only_fields = ['id', 'centro_estetica', 'creado_en', 'actualizado_en', 'nombre_completo']

    def create(self, validated_data):
        """
        Asignar automáticamente el centro_estetica del usuario actual
        Multi-tenancy: garantiza aislamiento de datos
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'centro_estetica'):
            validated_data['centro_estetica'] = request.user.centro_estetica
        return super().create(validated_data)


class HistorialClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para HistorialCliente
    """
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    profesional_nombre = serializers.CharField(source='profesional.get_full_name', read_only=True)

    class Meta:
        model = HistorialCliente
        fields = [
            'id',
            'cliente',
            'servicio',
            'servicio_nombre',
            'profesional',
            'profesional_nombre',
            'fecha',
            'observaciones',
            'resultado',
            'foto_antes',
            'foto_despues',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']

from rest_framework import serializers
from .models import Notificacion, MensajeTemplate
from apps.clientes.serializers import ClienteSerializer
from apps.turnos.serializers import TurnoListSerializer


class NotificacionSerializer(serializers.ModelSerializer):
    """
    Serializer para Notificación WhatsApp
    Incluye información del cliente y turno relacionados
    """
    cliente_info = ClienteSerializer(source='cliente', read_only=True)
    turno_info = TurnoListSerializer(source='turno', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            'id',
            # Relaciones
            'sucursal',
            'cliente',
            'cliente_info',
            'turno',
            'turno_info',
            # Información de la notificación
            'tipo',
            'tipo_display',
            'mensaje',
            'telefono_destino',
            # Estado del envío
            'estado',
            'estado_display',
            'mensaje_id_externo',
            'error_mensaje',
            # Timestamps
            'creado_en',
            'enviado_en',
            'entregado_en',
            'leido_en',
        ]
        read_only_fields = [
            'id',
            'mensaje_id_externo',
            'error_mensaje',
            'creado_en',
            'enviado_en',
            'entregado_en',
            'leido_en',
        ]


class NotificacionListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar notificaciones (sin nested data)
    Optimizado para listas grandes
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'tipo',
            'tipo_display',
            'estado',
            'estado_display',
            'telefono_destino',
            'creado_en',
            'enviado_en',
        ]


class EnviarNotificacionManualSerializer(serializers.Serializer):
    """
    Serializer para enviar notificaciones manuales
    """
    cliente_id = serializers.IntegerField(required=True)
    tipo = serializers.ChoiceField(
        choices=Notificacion.TipoNotificacion.choices,
        required=True
    )
    mensaje = serializers.CharField(required=True, max_length=1600)
    turno_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_mensaje(self, value):
        """Validar longitud del mensaje para WhatsApp"""
        if len(value) > 1600:
            raise serializers.ValidationError(
                "El mensaje no puede exceder 1600 caracteres"
            )
        return value


class MensajeTemplateSerializer(serializers.ModelSerializer):
    """Serializer completo para templates de mensajes"""

    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    actualizado_por_nombre = serializers.CharField(
        source='actualizado_por.nombre_completo',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = MensajeTemplate
        fields = [
            'id',
            'sucursal',
            'tipo',
            'tipo_display',
            'mensaje',
            'activo',
            'creado_en',
            'actualizado_en',
            'actualizado_por',
            'actualizado_por_nombre'
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']

    def validate_mensaje(self, value):
        """Validar que el mensaje no esté vacío"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "El mensaje debe tener al menos 10 caracteres"
            )
        return value


class MensajeTemplateListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""

    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    preview = serializers.SerializerMethodField()

    class Meta:
        model = MensajeTemplate
        fields = ['id', 'tipo', 'tipo_display', 'activo', 'preview', 'actualizado_en']

    def get_preview(self, obj):
        """Mostrar preview del mensaje (primeros 100 caracteres)"""
        return obj.mensaje[:100] + "..." if len(obj.mensaje) > 100 else obj.mensaje

from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import Turno
from apps.clientes.serializers import ClienteSerializer
from apps.servicios.serializers import ServicioSerializer
from apps.empleados.serializers import UsuarioSerializer


class TurnoListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar turnos con datos nested de relaciones
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    profesional_nombre = serializers.SerializerMethodField()
    duracion_minutos = serializers.IntegerField(source='servicio.duracion_minutos', read_only=True)

    class Meta:
        model = Turno
        fields = [
            'id', 'cliente', 'cliente_nombre', 'servicio', 'servicio_nombre',
            'profesional', 'profesional_nombre', 'duracion_minutos',
            'fecha_hora_inicio', 'fecha_hora_fin', 'estado', 'estado_pago',
            'monto_total', 'monto_sena', 'notas',
            'recordatorio_24h_enviado', 'recordatorio_2h_enviado',
            'creado_en', 'actualizado_en',
        ]

    def get_profesional_nombre(self, obj):
        if obj.profesional:
            return f"{obj.profesional.first_name} {obj.profesional.last_name}".strip() or obj.profesional.username
        return None


class TurnoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado con objetos completos nested
    """
    cliente_data = ClienteSerializer(source='cliente', read_only=True)
    servicio_data = ServicioSerializer(source='servicio', read_only=True)
    profesional_data = UsuarioSerializer(source='profesional', read_only=True)
    creado_por_data = UsuarioSerializer(source='creado_por', read_only=True)

    class Meta:
        model = Turno
        fields = [
            'id', 'sucursal', 'cliente', 'cliente_data', 'servicio', 'servicio_data',
            'profesional', 'profesional_data', 'fecha_hora_inicio', 'fecha_hora_fin',
            'estado', 'estado_pago', 'monto_total', 'monto_sena', 'notas',
            'recordatorio_24h_enviado', 'recordatorio_2h_enviado',
            'creado_por', 'creado_por_data', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'sucursal', 'creado_en', 'actualizado_en', 'creado_por']


class TurnoCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar turnos con validación de double-booking
    """
    # Campos opcionales que se calculan automáticamente
    fecha_hora_fin = serializers.DateTimeField(required=False, allow_null=True)
    monto_total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = Turno
        fields = [
            'id', 'cliente', 'servicio', 'profesional', 'fecha_hora_inicio',
            'fecha_hora_fin', 'estado', 'estado_pago', 'monto_total',
            'monto_sena', 'notas',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        """
        Validación de disponibilidad y prevención de double-booking
        """
        fecha_hora_inicio = attrs.get('fecha_hora_inicio')
        servicio = attrs.get('servicio')
        profesional = attrs.get('profesional')

        # Validar que la fecha no sea en el pasado
        if fecha_hora_inicio and fecha_hora_inicio < timezone.now():
            raise serializers.ValidationError({
                'fecha_hora_inicio': 'No se pueden crear turnos en el pasado'
            })

        # Calcular fecha_hora_fin si no se proporciona
        if not attrs.get('fecha_hora_fin') and servicio and fecha_hora_inicio:
            from datetime import timedelta
            attrs['fecha_hora_fin'] = fecha_hora_inicio + timedelta(
                minutes=servicio.duracion_minutos
            )

        # Validar disponibilidad del profesional (prevención de double-booking)
        if profesional and fecha_hora_inicio and attrs.get('fecha_hora_fin'):
            # Crear un objeto temporal para usar el método del modelo
            turno_temp = Turno(
                profesional=profesional,
                sucursal=self.context['request'].user.sucursal,
                fecha_hora_inicio=fecha_hora_inicio,
                fecha_hora_fin=attrs['fecha_hora_fin'],
                servicio=servicio,
                cliente=attrs.get('cliente'),
            )

            # Si estamos actualizando, establecer el pk
            if self.instance:
                turno_temp.pk = self.instance.pk

            disponible, conflictos = turno_temp.verificar_disponibilidad()

            if not disponible:
                conflicto = conflictos.first()
                raise serializers.ValidationError({
                    'fecha_hora_inicio': f'El profesional ya tiene un turno asignado en ese horario '
                                        f'({conflicto.fecha_hora_inicio.strftime("%H:%M")} - '
                                        f'{conflicto.fecha_hora_fin.strftime("%H:%M")})'
                })

        return attrs

    def create(self, validated_data):
        """
        Crear turno con transacción atómica para prevenir race conditions
        """
        with transaction.atomic():
            # Asignar sucursal y creado_por desde el usuario autenticado
            validated_data['sucursal'] = self.context['request'].user.sucursal
            validated_data['creado_por'] = self.context['request'].user

            # Establecer monto_total desde el servicio si no se proporciona
            if 'monto_total' not in validated_data:
                validated_data['monto_total'] = validated_data['servicio'].precio

            turno = Turno.objects.create(**validated_data)
            return turno

    def update(self, instance, validated_data):
        """
        Actualizar turno con validación de disponibilidad
        """
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance

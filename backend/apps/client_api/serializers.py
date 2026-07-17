from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.clientes.models import (
    CodigoInvitacion,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.empleados.models import CentroEstetica

from .tokens import CLIENTE_TOKEN_USE


class VinculacionResumenSerializer(serializers.ModelSerializer):
    """Resumen de un vínculo cuenta ↔ ficha de cliente (incluye centro)."""
    cliente_id = serializers.IntegerField(source='cliente.id', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    centro_id = serializers.IntegerField(source='cliente.centro_estetica_id', read_only=True)
    centro_nombre = serializers.CharField(source='cliente.centro_estetica.nombre', read_only=True)

    class Meta:
        model = VinculacionCliente
        fields = [
            'id', 'cliente_id', 'cliente_nombre',
            'centro_id', 'centro_nombre',
            'metodo_vinculacion', 'vinculado_en',
        ]


class PerfilSerializer(serializers.ModelSerializer):
    vinculaciones = VinculacionResumenSerializer(many=True, read_only=True)

    class Meta:
        model = UsuarioCliente
        fields = [
            'id', 'email', 'nombre', 'apellido',
            'email_verificado', 'push_token', 'creado_en',
            'vinculaciones',
        ]
        read_only_fields = ['id', 'email', 'email_verificado', 'creado_en']


class RegistroSerializer(serializers.Serializer):
    """
    Registro de una cuenta de app.

    - Con ``codigo``: vincula a la ficha ``Cliente`` existente del código (flujo staff).
    - Sin ``codigo``: crea una ficha ``Cliente`` nueva en el centro indicado (auto-registro).
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    codigo = serializers.CharField(required=False, allow_blank=True)
    # Requeridos solo para auto-registro (sin código)
    nombre = serializers.CharField(required=False, allow_blank=True)
    apellido = serializers.CharField(required=False, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_blank=True)
    centro = serializers.IntegerField(required=False)

    def validate_email(self, value):
        value = value.strip().lower()
        if UsuarioCliente.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe una cuenta con este email')
        return value

    def validate(self, attrs):
        codigo = (attrs.get('codigo') or '').strip().upper()

        if codigo:
            try:
                invitacion = CodigoInvitacion.objects.select_related(
                    'cliente', 'cliente__centro_estetica'
                ).get(codigo=codigo)
            except CodigoInvitacion.DoesNotExist:
                raise serializers.ValidationError({'codigo': 'Código inválido'})

            if not invitacion.esta_vigente:
                raise serializers.ValidationError(
                    {'codigo': 'El código expiró o ya fue utilizado'}
                )

            attrs['_invitacion'] = invitacion
        else:
            centro_id = attrs.get('centro')
            if not centro_id:
                raise serializers.ValidationError(
                    {'centro': 'Requerido para registrarse sin código de invitación'}
                )
            try:
                centro = CentroEstetica.objects.get(pk=centro_id, activo=True)
            except CentroEstetica.DoesNotExist:
                raise serializers.ValidationError({'centro': 'Centro no encontrado'})

            if not attrs.get('nombre') or not attrs.get('apellido'):
                raise serializers.ValidationError(
                    'nombre y apellido son requeridos para registrarse sin código'
                )

            attrs['_centro'] = centro

        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PushTokenSerializer(serializers.Serializer):
    push_token = serializers.CharField(max_length=255)


class PerfilUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioCliente
        fields = ['nombre', 'apellido']


class ClienteTokenRefreshSerializer(TokenRefreshSerializer):
    """Refresh que solo acepta tokens de cliente (claim ``token_use='cliente'``)."""

    def validate(self, attrs):
        refresh = RefreshToken(attrs['refresh'])
        if refresh.get('token_use') != CLIENTE_TOKEN_USE:
            raise InvalidToken('El token no corresponde a un usuario de la app')
        return super().validate(attrs)

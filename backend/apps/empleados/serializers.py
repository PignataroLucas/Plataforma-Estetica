from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, CentroEstetica, Sucursal


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer básico para Usuario
    """
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'centro_estetica', 'sucursal', 'telefono', 'fecha_nacimiento',
            'direccion', 'foto', 'rol', 'fecha_ingreso', 'especialidades',
            'activo', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado que incluye los datos del usuario en la respuesta
    """
    def validate(self, attrs):
        data = super().validate(attrs)

        # Agregar datos del usuario a la respuesta
        user_serializer = UsuarioSerializer(self.user)
        data['user'] = user_serializer.data

        return data


class CentroEsteticaSerializer(serializers.ModelSerializer):
    """
    Serializer para CentroEstetica
    """
    class Meta:
        model = CentroEstetica
        fields = '__all__'


class SucursalSerializer(serializers.ModelSerializer):
    """
    Serializer para Sucursal
    """
    class Meta:
        model = Sucursal
        fields = '__all__'

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, CentroEstetica, Sucursal


class UsuarioListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar usuarios con datos básicos
    """
    nombre_completo = serializers.SerializerMethodField()
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True, allow_null=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'nombre_completo',
            'sucursal', 'sucursal_nombre', 'telefono', 'rol', 'rol_display',
            'especialidades', 'activo', 'fecha_ingreso', 'creado_en'
        ]

    def get_nombre_completo(self, obj):
        return obj.get_full_name() or obj.username


class UsuarioDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver/editar usuario
    """
    nombre_completo = serializers.SerializerMethodField()
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    sucursal_data = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'nombre_completo',
            'centro_estetica', 'sucursal', 'sucursal_data', 'telefono',
            'fecha_nacimiento', 'direccion', 'foto', 'rol', 'rol_display',
            'fecha_ingreso', 'especialidades', 'activo',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'centro_estetica', 'creado_en', 'actualizado_en']

    def get_nombre_completo(self, obj):
        return obj.get_full_name() or obj.username

    def get_sucursal_data(self, obj):
        if obj.sucursal:
            return {
                'id': obj.sucursal.id,
                'nombre': obj.sucursal.nombre
            }
        return None


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevos usuarios/empleados
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'sucursal', 'telefono',
            'fecha_nacimiento', 'direccion', 'foto', 'rol',
            'fecha_ingreso', 'especialidades', 'activo'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return attrs

    def create(self, validated_data):
        # Remover password2 ya que no es parte del modelo
        validated_data.pop('password2')

        # Asignar centro_estetica desde el usuario autenticado
        validated_data['centro_estetica'] = self.context['request'].user.centro_estetica

        # Si no se especifica sucursal, usar la del usuario creador
        if 'sucursal' not in validated_data:
            validated_data['sucursal'] = self.context['request'].user.sucursal

        # Crear usuario con create_user para hashear la contraseña
        password = validated_data.pop('password')
        usuario = Usuario.objects.create_user(**validated_data)
        usuario.set_password(password)
        usuario.save()

        return usuario


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar usuarios (sin cambiar contraseña)
    """
    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 'sucursal', 'telefono',
            'fecha_nacimiento', 'direccion', 'foto', 'rol',
            'fecha_ingreso', 'especialidades', 'activo'
        ]
        read_only_fields = ['id']


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer básico para Usuario (usado en relaciones)
    """
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'nombre_completo',
            'centro_estetica', 'sucursal', 'telefono', 'fecha_nacimiento',
            'direccion', 'foto', 'rol', 'fecha_ingreso', 'especialidades',
            'activo', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']

    def get_nombre_completo(self, obj):
        return obj.get_full_name() or obj.username


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

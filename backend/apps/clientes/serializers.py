from rest_framework import serializers
from .models import Cliente, HistorialCliente, PlanTratamiento, RutinaCuidado, NotaCliente


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
            # Información personal
            'nombre',
            'apellido',
            'nombre_completo',
            'email',
            'telefono',
            'telefono_alternativo',
            'fecha_nacimiento',
            # Dirección
            'direccion',
            'ciudad',
            'provincia',
            'codigo_postal',
            # Documento
            'tipo_documento',
            'numero_documento',
            # A) Datos del paciente (tracking)
            'motivo_consulta',
            'objetivo_principal',
            # B) Historia / contraindicaciones
            'embarazo_lactancia',
            'marcapasos_implantes',
            'cancer_historial',
            'herpes_historial',
            'alergias',
            'tiene_alergias',
            'medicacion_actual',
            'medicacion_detalle',
            'tratamientos_previos',
            'tratamientos_previos_detalle',
            'tatuajes_zona_tratamiento',
            'tatuajes_zonas',
            'contraindicaciones',
            'notas_medicas',
            'detalle_general',
            # C) Evaluación facial
            'tipo_piel',
            'poros',
            'brillo',
            'textura',
            'estado_piel',
            'observaciones_faciales',
            'diagnostico_facial',
            # D) Evaluación corporal
            'zonas_tratar',
            'celulitis_grado',
            'celulitis_tipo',
            'adiposidad',
            'flacidez',
            'estrias',
            'retencion_liquidos',
            'observaciones_corporales',
            'diagnostico_corporal',
            # Preferencias y marketing
            'preferencias',
            'foto',
            'acepta_promociones',
            'acepta_whatsapp',
            # Estado
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


class PlanTratamientoSerializer(serializers.ModelSerializer):
    """
    Serializer para PlanTratamiento (Sección E)
    Plan de tratamiento sugerido para el cliente
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    creado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = PlanTratamiento
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'tratamiento_sugerido',
            'frecuencia',
            'sesiones_estimadas',
            'indicaciones',
            'proximo_turno',
            'creado_por',
            'creado_por_nombre',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_por', 'creado_en', 'actualizado_en']

    def get_creado_por_nombre(self, obj):
        """
        Obtener el nombre del creador, usando username como fallback
        """
        if obj.creado_por:
            full_name = obj.creado_por.get_full_name()
            return full_name.strip() if full_name.strip() else obj.creado_por.username
        return None

    def create(self, validated_data):
        """
        Asignar automáticamente el usuario que crea el plan
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['creado_por'] = request.user
        return super().create(validated_data)


class RutinaCuidadoSerializer(serializers.ModelSerializer):
    """
    Serializer para RutinaCuidado (Sección F)
    Rutina de cuidado recomendada (diurna y nocturna)
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    creado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = RutinaCuidado
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'rutina_diurna_pasos',
            'rutina_diurna_productos',
            'rutina_nocturna_pasos',
            'rutina_nocturna_productos',
            'activa',
            'creado_por',
            'creado_por_nombre',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_por', 'creado_en', 'actualizado_en']

    def get_creado_por_nombre(self, obj):
        """
        Obtener el nombre del creador, usando username como fallback
        """
        if obj.creado_por:
            full_name = obj.creado_por.get_full_name()
            return full_name.strip() if full_name.strip() else obj.creado_por.username
        return None

    def create(self, validated_data):
        """
        Asignar automáticamente el usuario que crea la rutina
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['creado_por'] = request.user
        return super().create(validated_data)


class NotaClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para NotaCliente (Sección G)
    Registro de notas del paciente con visibilidad configurable
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    autor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = NotaCliente
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'tipo_nota',
            'contenido',
            'visible_para',
            'destacada',
            'autor',
            'autor_nombre',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['id', 'autor', 'creado_en', 'actualizado_en']

    def get_autor_nombre(self, obj):
        """
        Obtener el nombre del autor, usando username como fallback
        si no tiene first_name y last_name configurados
        """
        if obj.autor:
            full_name = obj.autor.get_full_name()
            return full_name.strip() if full_name.strip() else obj.autor.username
        return None

    def create(self, validated_data):
        """
        Asignar automáticamente el usuario que crea la nota
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['autor'] = request.user
        return super().create(validated_data)

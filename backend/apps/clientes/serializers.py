from rest_framework import serializers
from .models import (
    Cliente, HistorialCliente, PlanTratamiento, RutinaCuidado, RutinaItem,
    NotaCliente, SegmentoApp
)


class SegmentoAppSerializer(serializers.ModelSerializer):
    """Segmentos de la app y su descuento. El centro sale del usuario, nunca del body."""
    cantidad_clientes = serializers.SerializerMethodField()

    class Meta:
        model = SegmentoApp
        fields = [
            'id', 'nombre', 'porcentaje_descuento', 'es_predeterminado',
            'activo', 'cantidad_clientes', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en', 'cantidad_clientes']

    def get_cantidad_clientes(self, obj):
        """Cuántas fichas lo tienen asignado a mano. El general suma 0 y está bien:
        las que caen en él es por no tener ninguno."""
        return obj.clientes.count()

    def validate_nombre(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El nombre no puede estar vacío')
        return value


class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para Cliente
    Aplica principios SOLID:
    - SRP: Solo serializa datos de Cliente
    - OCP: Extensible via Meta.fields
    - DIP: Depende de abstracciones (ModelSerializer)
    """
    nombre_completo = serializers.ReadOnlyField()
    segmento_app_nombre = serializers.CharField(
        source='segmento_app.nombre', read_only=True, default=None
    )
    # El descuento que le corresponde de verdad, contando la caída al general.
    # Es el mismo número que la app le muestra y el que se va a cobrar.
    descuento_app = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )

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
            # App
            'segmento_app',
            'segmento_app_nombre',
            'descuento_app',
            # Estado
            'activo',
            'creado_en',
            'actualizado_en',
            'ultima_visita',
        ]
        read_only_fields = [
            'id', 'centro_estetica', 'creado_en', 'actualizado_en',
            'nombre_completo', 'segmento_app_nombre', 'descuento_app',
        ]

    def validate_segmento_app(self, value):
        """Un segmento de otro centro sería una fuga de datos entre inquilinos."""
        if value is None:
            return value
        request = self.context.get('request')
        centro = getattr(getattr(request, 'user', None), 'centro_estetica', None)
        if centro and value.centro_estetica_id != centro.id:
            raise serializers.ValidationError('El segmento pertenece a otro centro de estética')
        return value

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


class RutinaItemStaffSerializer(serializers.ModelSerializer):
    """Paso estructurado de la rutina, editable por el staff (producto opcional)."""
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = RutinaItem
        fields = [
            'id', 'momento', 'orden', 'paso',
            'producto', 'producto_nombre', 'producto_texto', 'nota',
        ]
        extra_kwargs = {'producto': {'required': False, 'allow_null': True}}


class RutinaCuidadoSerializer(serializers.ModelSerializer):
    """
    Serializer para RutinaCuidado (Sección F)
    Rutina de cuidado recomendada (diurna y nocturna), con items estructurados.
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    creado_por_nombre = serializers.SerializerMethodField()
    items = RutinaItemStaffSerializer(many=True, required=False)

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
            'items',
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

    def _sync_items(self, rutina, items_data):
        """Reemplaza los items de la rutina (replace-all)."""
        rutina.items.all().delete()
        RutinaItem.objects.bulk_create([
            RutinaItem(rutina=rutina, **item) for item in items_data
        ])

    def create(self, validated_data):
        """Crea la rutina, sus items y asigna el usuario creador."""
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['creado_por'] = request.user
        rutina = RutinaCuidado.objects.create(**validated_data)
        self._sync_items(rutina, items_data)
        return rutina

    def update(self, instance, validated_data):
        """
        Actualiza la rutina; solo reemplaza items si vienen en el payload
        (un PATCH sin 'items' —ej: togglear ``activa``— los preserva).
        """
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items_data is not None:
            self._sync_items(instance, items_data)
        return instance


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


class ClienteDuplicadoSerializer(serializers.ModelSerializer):
    """Resumen de una ficha para la vista de duplicados: datos + señales para decidir cuál conservar."""
    nombre_completo = serializers.CharField(read_only=True)
    tiene_cuenta_app = serializers.SerializerMethodField()
    historial_count = serializers.SerializerMethodField()
    turnos_count = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = [
            'id', 'nombre_completo', 'nombre', 'apellido',
            'telefono', 'email', 'creado_en', 'activo',
            'tiene_cuenta_app', 'historial_count', 'turnos_count',
        ]

    def get_tiene_cuenta_app(self, obj):
        return obj.vinculaciones.exists()

    def get_historial_count(self, obj):
        return obj.historial.count()

    def get_turnos_count(self, obj):
        return obj.turnos.count()

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

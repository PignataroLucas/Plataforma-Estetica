from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.clientes.models import (
    Cliente,
    CodigoInvitacion,
    CodigoRecuperacion,
    PlanTratamiento,
    RutinaCuidado,
    RutinaItem,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.clientes.utils import normalizar_telefono
from apps.empleados.models import CentroEstetica
from apps.notificaciones.eventos import Categoria
from apps.notificaciones.models import DispositivoPush
from apps.public_api.serializers import ProductoPublicoSerializer, ServicioPublicoSerializer
from apps.servicios.models import Servicio
from apps.turnos.models import Turno
from apps.turnos.services import (
    DIAS_MAXIMOS_A_FUTURO,
    dias_reserva_de,
    motivo_fecha_no_reservable,
    puede_cancelar,
)

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
            'email_verificado', 'creado_en',
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

            # Guard de duplicados: si ya existe una ficha del centro con el MISMO
            # teléfono normalizado + email, vinculamos a esa ficha en vez de crear
            # una nueva. Requerimos AMBOS a propósito: con solo el teléfono no
            # auto-vinculamos (familiares comparten número / evitar que alguien
            # reclame la ficha de otro) — ese caso lo levanta el detector del CRM.
            tel_norm = normalizar_telefono(attrs.get('telefono', ''))
            if tel_norm and attrs.get('email'):
                ficha = Cliente.objects.filter(
                    centro_estetica=centro,
                    telefono_normalizado=tel_norm,
                    email__iexact=attrs['email'],
                ).first()
                if ficha is not None:
                    attrs['_ficha_match'] = ficha

        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PushTokenSerializer(serializers.Serializer):
    """Alta o baja de un dispositivo para push."""
    push_token = serializers.CharField(max_length=255)
    plataforma = serializers.ChoiceField(
        choices=DispositivoPush.Plataforma.choices,
        required=False,
        default=DispositivoPush.Plataforma.DESCONOCIDA,
    )

    def validate_push_token(self, value):
        # Expo entrega siempre este formato. Validarlo acá evita guardar basura
        # que después falla recién en el envío, lejos de donde se originó.
        token = value.strip()
        if not (token.startswith('ExponentPushToken[') and token.endswith(']')):
            raise serializers.ValidationError(
                'No parece un Expo push token (ExponentPushToken[...]).'
            )
        return token


class PreferenciasNotificacionSerializer(serializers.Serializer):
    """
    Preferencias como un diccionario ``categoria -> bool``.

    La app no necesita saber que por debajo son filas que solo existen cuando se
    apaga algo: pide el mapa completo y manda el mapa completo.
    """

    def to_representation(self, usuario_cliente):
        apagadas = set(
            usuario_cliente.preferencias_notificacion
            .filter(habilitada=False)
            .values_list('categoria', flat=True)
        )
        return {
            categoria: categoria not in apagadas
            for categoria, _ in Categoria.choices
        }

    def to_internal_value(self, data):
        # Los errores van en un dict: al levantarlos desde `to_internal_value`
        # con una lista suelta, DRF no puede armar su ReturnDict y el 400 se
        # convierte en un 500.
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                {'detail': 'Se espera un objeto de categorías.'}
            )

        validas = {categoria for categoria, _ in Categoria.choices}
        desconocidas = set(data) - validas
        if desconocidas:
            raise serializers.ValidationError(
                {'detail': f"Categorías desconocidas: {', '.join(sorted(desconocidas))}."}
            )
        if not all(isinstance(valor, bool) for valor in data.values()):
            raise serializers.ValidationError(
                {'detail': 'Cada categoría tiene que ser true o false.'}
            )
        return data


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


# ------------------------------------------------------------------ #
# "Mi rutina" — data de la ficha, curada para el cliente
# ------------------------------------------------------------------ #

class RutinaItemAppSerializer(serializers.ModelSerializer):
    """Paso de rutina para la app; incluye el producto del catálogo si está linkeado."""
    producto = ProductoPublicoSerializer(read_only=True)

    class Meta:
        model = RutinaItem
        fields = ['id', 'momento', 'orden', 'paso', 'producto', 'producto_texto', 'nota']


class RutinaAppSerializer(serializers.ModelSerializer):
    """Rutina de cuidado curada: items estructurados + fallback de texto legacy."""
    items = RutinaItemAppSerializer(many=True, read_only=True)

    class Meta:
        model = RutinaCuidado
        fields = [
            'id', 'activa', 'actualizado_en',
            'rutina_diurna_pasos', 'rutina_diurna_productos',
            'rutina_nocturna_pasos', 'rutina_nocturna_productos',
            'items',
        ]


class PlanAppSerializer(serializers.ModelSerializer):
    """Plan de tratamiento curado para el cliente (sin campos internos de auditoría)."""

    class Meta:
        model = PlanTratamiento
        fields = [
            'id', 'tratamiento_sugerido', 'frecuencia',
            'sesiones_estimadas', 'indicaciones', 'proximo_turno', 'actualizado_en',
        ]


# ------------------------------------------------------------------ #
# Turnos — vista del cliente (curada: nada de comisiones ni auditoría)
# ------------------------------------------------------------------ #

class TurnoAppSerializer(serializers.ModelSerializer):
    """
    Turno tal como lo ve el cliente en la app.

    Deliberadamente NO reusa los serializers del staff: no expone ``creado_por``,
    la ficha clínica del cliente ni los datos internos del servicio (comisión,
    máquina alquilada, costos).
    """
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    estado_pago_display = serializers.CharField(source='get_estado_pago_display', read_only=True)
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    duracion_minutos = serializers.IntegerField(source='servicio.duracion_minutos', read_only=True)
    profesional_nombre = serializers.SerializerMethodField()
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    sucursal_direccion = serializers.CharField(source='sucursal.direccion', read_only=True)
    centro_nombre = serializers.CharField(source='sucursal.centro_estetica.nombre', read_only=True)
    puede_cancelar = serializers.SerializerMethodField()

    class Meta:
        model = Turno
        fields = [
            'id', 'fecha_hora_inicio', 'fecha_hora_fin',
            'estado', 'estado_display', 'estado_pago', 'estado_pago_display',
            'servicio', 'servicio_nombre', 'duracion_minutos',
            'profesional_nombre',
            'sucursal_nombre', 'sucursal_direccion', 'centro_nombre',
            'monto_total', 'notas', 'puede_cancelar',
        ]

    def get_profesional_nombre(self, obj):
        # Solo el nombre real; nunca el username interno del empleado.
        if not obj.profesional:
            return None
        return obj.profesional.get_full_name().strip() or None

    def get_puede_cancelar(self, obj):
        return puede_cancelar(obj)


class ServicioReservableSerializer(ServicioPublicoSerializer):
    """
    Tratamiento que el cliente puede reservar desde la app.

    Agrega ``dias_reserva`` YA RESUELTO (los propios del servicio o los generales)
    para poder mostrar "Lun · Mar · Mié · Jue" sin reimplementar la regla. Las
    fechas concretas del calendario vienen del padre (``fechas_disponibles``), que
    ya contempla los dos modos; ``dias_reserva`` solo aplica al modo ``'dias'``.
    """
    dias_reserva = serializers.SerializerMethodField()

    class Meta(ServicioPublicoSerializer.Meta):
        fields = ServicioPublicoSerializer.Meta.fields + ['dias_reserva']

    def get_dias_reserva(self, obj):
        return dias_reserva_de(obj)


class ReservaSerializer(serializers.Serializer):
    """
    Entrada de ``POST /api/client/turnos/``.

    El servicio se valida contra el centro donde el usuario está vinculado (via
    ``context['centro_id']``), así una cuenta no puede reservar en otro centro.
    """
    servicio = serializers.IntegerField()
    fecha_hora_inicio = serializers.DateTimeField()
    notas = serializers.CharField(
        required=False, allow_blank=True, max_length=500, default=''
    )

    def validate_servicio(self, value):
        try:
            return Servicio.objects.select_related('sucursal').get(
                pk=value,
                activo=True,
                sucursal__centro_estetica_id=self.context['centro_id'],
            )
        except Servicio.DoesNotExist:
            raise serializers.ValidationError('Ese tratamiento no está disponible en tu centro')

    def validate_fecha_hora_inicio(self, value):
        ahora = timezone.now()
        if value <= ahora:
            raise serializers.ValidationError('Elegí un horario futuro')
        if (value - ahora).days > DIAS_MAXIMOS_A_FUTURO:
            raise serializers.ValidationError(
                f'Solo se puede reservar hasta {DIAS_MAXIMOS_A_FUTURO} días a futuro'
            )
        return value

    def validate(self, attrs):
        """
        Política de reserva desde la app: servicio habilitado, con la anticipación
        mínima y en un día permitido. Se valida acá y no solo en el calendario,
        porque el POST puede llegar con cualquier fecha.
        """
        servicio = attrs.get('servicio')
        inicio = attrs.get('fecha_hora_inicio')
        if servicio and inicio:
            motivo = motivo_fecha_no_reservable(servicio, timezone.localtime(inicio).date())
            if motivo:
                raise serializers.ValidationError({'fecha_hora_inicio': motivo})
        return attrs


class ItemCompraSerializer(serializers.Serializer):
    """Una línea del carrito que manda la app."""
    producto = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1, max_value=20)


class CompraSerializer(serializers.Serializer):
    """
    El carrito completo.

    El tope de 20 líneas no es una regla de negocio: es lo que evita que un
    carrito absurdo dispare 20 POST contra Tienda Nube (uno por producto, ver
    apps/integraciones/compra.py).
    """
    items = ItemCompraSerializer(many=True, allow_empty=False, max_length=20)


# ------------------------------------------------------------------ #
# Recuperación de contraseña
# ------------------------------------------------------------------ #

class OlvideMiClaveSerializer(serializers.Serializer):
    """
    Pide un código de recuperación.

    **No valida que la cuenta exista, y es a propósito.** Si respondiera distinto
    para un email registrado que para uno que no, cualquiera podría averiguar
    quién es clienta del centro probando direcciones. La vista contesta siempre
    lo mismo; que exista o no lo decide ella en silencio.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class RestablecerClaveSerializer(serializers.Serializer):
    """
    Consume el código y cambia la contraseña.

    Los errores son deliberadamente vagos —"código inválido o vencido"— por lo
    mismo que el serializer de arriba: distinguir "ese código no es" de "esa
    cuenta no existe" convierte el endpoint en un detector de clientas.
    """
    email = serializers.EmailField()
    codigo = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_email(self, value):
        return value.strip().lower()

    def validate_codigo(self, value):
        return value.strip()

    def validate(self, attrs):
        generico = 'El código es inválido o venció. Pedí uno nuevo.'

        try:
            usuario = UsuarioCliente.objects.get(email=attrs['email'])
        except UsuarioCliente.DoesNotExist:
            raise serializers.ValidationError({'codigo': generico})

        vigente = (
            CodigoRecuperacion.objects
            .filter(usuario_cliente=usuario, usado_en__isnull=True)
            .order_by('-creado_en')
            .first()
        )
        if vigente is None or not vigente.verificar(attrs['codigo']):
            raise serializers.ValidationError({'codigo': generico})

        attrs['_usuario'] = usuario
        attrs['_codigo'] = vigente
        return attrs

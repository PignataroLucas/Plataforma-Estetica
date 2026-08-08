from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.clientes.models import (
    Cliente,
    PlanTratamiento,
    RutinaCuidado,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.notificaciones.models import DispositivoPush, PreferenciaNotificacion
from apps.servicios.models import Servicio
from apps.turnos.models import Turno
from apps.turnos.services import (
    DIAS_MAXIMOS_A_FUTURO,
    ESTADOS_QUE_OCUPAN,
    HORAS_MINIMAS_CANCELACION,
    TurnoNoDisponible,
    motivo_fecha_no_reservable,
    primera_fecha_reservable,
    puede_cancelar,
    reservar_turno,
    slots_agregados,
)

from .authentication import ClienteJWTAuthentication
from .serializers import (
    ClienteTokenRefreshSerializer,
    LoginSerializer,
    PerfilSerializer,
    PerfilUpdateSerializer,
    PlanAppSerializer,
    PreferenciasNotificacionSerializer,
    PushTokenSerializer,
    RegistroSerializer,
    ReservaSerializer,
    RutinaAppSerializer,
    ServicioReservableSerializer,
    TurnoAppSerializer,
)
from .tokens import tokens_para_usuario_cliente

# Cantidad de turnos pasados que devuelve el historial de la app.
LIMITE_HISTORICO = 30


class ClienteScopeMixin:
    """
    Base de los endpoints autenticados de la app.

    El scope SIEMPRE sale de ``request.user.vinculaciones``: la ficha ``Cliente``
    nunca se toma de un id de la URL o del body. Con ``?centro=<id>`` se elige la
    vinculación de ese centro (cuentas multi-centro); sin el parámetro, la primera.
    """
    authentication_classes = [ClienteJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_vinculaciones(self, request):
        vinculaciones = request.user.vinculaciones.select_related('cliente__centro_estetica')
        centro_id = request.query_params.get('centro')
        if centro_id:
            vinculaciones = vinculaciones.filter(cliente__centro_estetica_id=centro_id)
        return vinculaciones

    def get_vinculacion(self, request):
        return self.get_vinculaciones(request).first()

    @staticmethod
    def sin_vinculacion():
        return Response(
            {'detail': 'No hay una cuenta vinculada para este centro'},
            status=status.HTTP_404_NOT_FOUND,
        )


class RegistroView(APIView):
    """POST /api/client/auth/registro/ — crea una cuenta de app y su vinculación."""
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'cliente_registro'

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            usuario = UsuarioCliente.objects.create_user(
                email=data['email'],
                password=data['password'],
                nombre=data.get('nombre', ''),
                apellido=data.get('apellido', ''),
            )

            invitacion = data.get('_invitacion')
            if invitacion is not None:
                cliente = invitacion.cliente
                VinculacionCliente.objects.create(
                    usuario_cliente=usuario,
                    cliente=cliente,
                    metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
                )
                invitacion.marcar_usado(usuario)
                # Completar nombre desde la ficha si el registro no lo trajo
                if not usuario.nombre and (cliente.nombre or cliente.apellido):
                    usuario.nombre = cliente.nombre
                    usuario.apellido = cliente.apellido
                    usuario.save(update_fields=['nombre', 'apellido'])
            elif data.get('_ficha_match') is not None:
                # El guard detectó una ficha existente (teléfono + email) → vincular
                VinculacionCliente.objects.create(
                    usuario_cliente=usuario,
                    cliente=data['_ficha_match'],
                    metodo_vinculacion=VinculacionCliente.Metodo.AUTO_MATCH,
                )
            else:
                centro = data['_centro']
                cliente = Cliente.objects.create(
                    centro_estetica=centro,
                    nombre=data['nombre'],
                    apellido=data['apellido'],
                    email=data['email'],
                    telefono=data.get('telefono', ''),
                )
                VinculacionCliente.objects.create(
                    usuario_cliente=usuario,
                    cliente=cliente,
                    metodo_vinculacion=VinculacionCliente.Metodo.REGISTRO_NUEVO,
                )

        tokens = tokens_para_usuario_cliente(usuario)
        return Response(
            {**tokens, 'usuario': PerfilSerializer(usuario).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/client/auth/login/ — autentica contra UsuarioCliente."""
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'cliente_auth'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        password = serializer.validated_data['password']

        credenciales_invalidas = Response(
            {'detail': 'Email o contraseña incorrectos'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

        try:
            usuario = UsuarioCliente.objects.get(email=email)
        except UsuarioCliente.DoesNotExist:
            return credenciales_invalidas

        if not usuario.check_password(password):
            return credenciales_invalidas

        if not usuario.activo:
            return Response({'detail': 'Cuenta inactiva'}, status=status.HTTP_403_FORBIDDEN)

        usuario.last_login = timezone.now()
        usuario.save(update_fields=['last_login'])

        tokens = tokens_para_usuario_cliente(usuario)
        return Response({**tokens, 'usuario': PerfilSerializer(usuario).data})


class ClienteTokenRefreshView(TokenRefreshView):
    """POST /api/client/auth/refresh/ — solo acepta refresh tokens de cliente."""
    serializer_class = ClienteTokenRefreshSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'cliente_auth'


class PerfilView(ClienteScopeMixin, APIView):
    """GET/PATCH /api/client/perfil/ — perfil de la cuenta autenticada."""

    def get_queryset(self):
        return UsuarioCliente.objects.prefetch_related(
            'vinculaciones__cliente__centro_estetica'
        )

    def get(self, request):
        usuario = self.get_queryset().get(pk=request.user.pk)
        return Response(PerfilSerializer(usuario).data)

    def patch(self, request):
        serializer = PerfilUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        usuario = self.get_queryset().get(pk=request.user.pk)
        return Response(PerfilSerializer(usuario).data)


class MiRutinaView(ClienteScopeMixin, APIView):
    """GET /api/client/mi-rutina/ — rutina activa + plan del cliente vinculado."""

    def get(self, request):
        vinc = self.get_vinculacion(request)
        if vinc is None:
            return self.sin_vinculacion()

        cliente = vinc.cliente
        rutina = (
            RutinaCuidado.objects
            .filter(cliente=cliente, activa=True)
            .prefetch_related('items__producto__categoria')
            .order_by('-creado_en')
            .first()
        )
        plan = (
            PlanTratamiento.objects
            .filter(cliente=cliente)
            .order_by('-creado_en')
            .first()
        )

        return Response({
            'centro': {
                'id': cliente.centro_estetica_id,
                'nombre': cliente.centro_estetica.nombre,
            },
            'cliente': {'id': cliente.id, 'nombre': cliente.nombre_completo},
            'rutina': RutinaAppSerializer(rutina).data if rutina else None,
            'plan': PlanAppSerializer(plan).data if plan else None,
        })


class PushRegisterView(ClienteScopeMixin, APIView):
    """
    POST   /api/client/push/register/ — registra este teléfono para recibir push.
    DELETE /api/client/push/register/ — lo da de baja (al cerrar sesión).

    El token es único a nivel sistema, así que registrar uno que ya estaba a
    nombre de otra cuenta lo **reasigna** en vez de duplicarlo. Es el caso del
    teléfono prestado o de la clienta que cierra sesión y entra con otra cuenta:
    sin esta reasignación, el aparato seguiría recibiendo los turnos de la cuenta
    anterior.
    """

    def post(self, request):
        serializer = PushTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        dispositivo, creado = DispositivoPush.objects.update_or_create(
            token=datos['push_token'],
            defaults={
                'usuario_cliente': request.user,
                'plataforma': datos['plataforma'],
                'activo': True,
                'motivo_baja': '',
            },
        )
        return Response(
            {'status': 'ok', 'creado': creado},
            status=status.HTTP_201_CREATED if creado else status.HTTP_200_OK,
        )

    def delete(self, request):
        serializer = PushTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Solo se da de baja un dispositivo propio: el token de otra cuenta no se
        # toca aunque se conozca la cadena.
        actualizados = DispositivoPush.objects.filter(
            token=serializer.validated_data['push_token'],
            usuario_cliente=request.user,
        ).update(
            activo=False,
            motivo_baja=DispositivoPush.MotivoBaja.SESION_CERRADA,
        )
        return Response({'status': 'ok', 'dado_de_baja': bool(actualizados)})


class PreferenciasNotificacionView(ClienteScopeMixin, APIView):
    """
    GET   /api/client/notificaciones/preferencias/ — qué recibe hoy.
    PATCH /api/client/notificaciones/preferencias/ — encender o apagar categorías.

    Se guardan solo las categorías apagadas, así que sumar una categoría nueva al
    catálogo no exige migrar a nadie: quien no la apagó, la recibe.
    """

    def get(self, request):
        return Response(PreferenciasNotificacionSerializer().to_representation(request.user))

    def patch(self, request):
        serializer = PreferenciasNotificacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for categoria, habilitada in serializer.validated_data.items():
            if habilitada:
                # Encender es borrar la excepción, no guardar un True.
                PreferenciaNotificacion.objects.filter(
                    usuario_cliente=request.user, categoria=categoria
                ).delete()
            else:
                PreferenciaNotificacion.objects.update_or_create(
                    usuario_cliente=request.user,
                    categoria=categoria,
                    defaults={'habilitada': False},
                )

        return Response(PreferenciasNotificacionSerializer().to_representation(request.user))


# ------------------------------------------------------------------ #
# Turnos — listado, disponibilidad, reserva y cancelación
# ------------------------------------------------------------------ #

class TurnosView(ClienteScopeMixin, APIView):
    """
    GET  /api/client/turnos/ — turnos del cliente (próximos + historial).
    POST /api/client/turnos/ — reserva un turno.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'cliente_reserva'

    def get_throttles(self):
        # El listado no se limita; el límite aplica solo a la reserva.
        return super().get_throttles() if self.request.method == 'POST' else []

    def get(self, request):
        cliente_ids = list(self.get_vinculaciones(request).values_list('cliente_id', flat=True))
        if not cliente_ids:
            return self.sin_vinculacion()

        turnos = Turno.objects.filter(cliente_id__in=cliente_ids).select_related(
            'servicio', 'profesional', 'sucursal__centro_estetica'
        )
        ahora = timezone.now()

        vigentes = Q(fecha_hora_inicio__gte=ahora) & Q(estado__in=ESTADOS_QUE_OCUPAN)
        proximos = turnos.filter(vigentes).order_by('fecha_hora_inicio')
        historicos = turnos.exclude(vigentes).order_by('-fecha_hora_inicio')[:LIMITE_HISTORICO]

        return Response({
            'proximos': TurnoAppSerializer(proximos, many=True).data,
            'historicos': TurnoAppSerializer(historicos, many=True).data,
        })

    def post(self, request):
        vinc = self.get_vinculacion(request)
        if vinc is None:
            return self.sin_vinculacion()

        serializer = ReservaSerializer(
            data=request.data,
            context={'centro_id': vinc.cliente.centro_estetica_id},
        )
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            turno = reservar_turno(
                cliente=vinc.cliente,
                servicio=datos['servicio'],
                inicio=datos['fecha_hora_inicio'],
                notas=datos.get('notas', ''),
                estado=Turno.Estado.PENDIENTE,
            )
        except TurnoNoDisponible as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TurnoAppSerializer(turno).data, status=status.HTTP_201_CREATED)


class DisponibilidadView(ClienteScopeMixin, APIView):
    """
    GET /api/client/turnos/disponibilidad/?servicio=<id>&fecha=YYYY-MM-DD

    Horarios libres para reservar ese servicio ese día, combinando la agenda de
    todos los profesionales de la sucursal. El cliente elige la hora; el sistema
    resuelve con qué profesional (no se expone la agenda individual).
    """

    def get(self, request):
        vinc = self.get_vinculacion(request)
        if vinc is None:
            return self.sin_vinculacion()

        fecha_str = request.query_params.get('fecha')
        servicio_id = request.query_params.get('servicio')
        if not fecha_str or not servicio_id:
            return Response(
                {'detail': 'Se requieren los parámetros "servicio" y "fecha"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'detail': 'Formato de fecha inválido. Usá YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hoy = timezone.localdate()
        if fecha < hoy or (fecha - hoy).days > DIAS_MAXIMOS_A_FUTURO:
            return Response({'fecha': fecha_str, 'slots': []})

        try:
            servicio = Servicio.objects.select_related('sucursal').get(
                pk=servicio_id,
                activo=True,
                sucursal__centro_estetica_id=vinc.cliente.centro_estetica_id,
            )
        except (Servicio.DoesNotExist, ValueError):
            return Response(
                {'detail': 'Ese tratamiento no está disponible en tu centro'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Política de reserva de la app (día permitido, anticipación mínima).
        # Se responde 200 con el motivo para que el calendario lo pueda explicar.
        motivo = motivo_fecha_no_reservable(servicio, fecha)
        if motivo:
            return Response({'fecha': fecha_str, 'slots': [], 'motivo': motivo})

        slots = slots_agregados(servicio, fecha, no_antes_de=timezone.now())

        return Response({
            'fecha': fecha_str,
            'servicio': {
                'id': servicio.id,
                'nombre': servicio.nombre,
                'duracion_minutos': servicio.duracion_minutos,
                # str: mismo formato que los DecimalField de DRF (no float)
                'precio': str(servicio.precio),
            },
            'slots': [
                {
                    'inicio': slot['inicio'],
                    'fin': slot['fin'],
                    'hora': timezone.localtime(slot['inicio']).strftime('%H:%M'),
                    'profesional_nombre': (
                        slot['profesional'].get_full_name().strip() or None
                    ),
                }
                for slot in slots
            ],
        })


class ServiciosReservablesView(ClienteScopeMixin, APIView):
    """
    GET /api/client/turnos/servicios/ — tratamientos que el cliente puede reservar.

    Es un subconjunto del catálogo público: solo los que el centro marcó como
    ``reservable_por_cliente``. El resto se sigue mostrando en el catálogo, pero
    se coordina directamente con el centro.
    """

    def get(self, request):
        vinc = self.get_vinculacion(request)
        if vinc is None:
            return self.sin_vinculacion()

        servicios = (
            Servicio.objects
            .filter(
                sucursal__centro_estetica_id=vinc.cliente.centro_estetica_id,
                activo=True,
                reservable_por_cliente=True,
            )
            .select_related('categoria', 'sucursal')
            .order_by('nombre')
        )

        return Response({
            # La app arma el calendario desde acá y no repite la regla.
            'primera_fecha': primera_fecha_reservable(),
            'results': ServicioReservableSerializer(servicios, many=True).data,
        })


class CancelarTurnoView(ClienteScopeMixin, APIView):
    """POST /api/client/turnos/<pk>/cancelar/ — cancela un turno propio."""

    def post(self, request, pk):
        cliente_ids = list(self.get_vinculaciones(request).values_list('cliente_id', flat=True))
        turno = (
            Turno.objects
            .filter(pk=pk, cliente_id__in=cliente_ids)
            .select_related('servicio', 'profesional', 'sucursal__centro_estetica')
            .first()
        )
        if turno is None:
            return Response({'detail': 'Turno no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if turno.estado not in ESTADOS_QUE_OCUPAN:
            return Response(
                {'detail': 'Este turno ya no se puede cancelar'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not puede_cancelar(turno):
            return Response(
                {
                    'detail': (
                        f'Los turnos se cancelan hasta {HORAS_MINIMAS_CANCELACION} horas antes. '
                        'Comunicate con el centro para reprogramarlo.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        turno.estado = Turno.Estado.CANCELADO
        turno.save()

        return Response(TurnoAppSerializer(turno).data)

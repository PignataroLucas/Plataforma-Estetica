from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.clientes.models import Cliente, UsuarioCliente, VinculacionCliente

from .authentication import ClienteJWTAuthentication
from .serializers import (
    ClienteTokenRefreshSerializer,
    LoginSerializer,
    PerfilSerializer,
    PerfilUpdateSerializer,
    PushTokenSerializer,
    RegistroSerializer,
)
from .tokens import tokens_para_usuario_cliente


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


class PerfilView(APIView):
    """GET/PATCH /api/client/perfil/ — perfil de la cuenta autenticada."""
    authentication_classes = [ClienteJWTAuthentication]
    permission_classes = [IsAuthenticated]

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


class PushRegisterView(APIView):
    """POST /api/client/push/register/ — guarda el Expo push token."""
    authentication_classes = [ClienteJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PushTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.push_token = serializer.validated_data['push_token']
        request.user.save(update_fields=['push_token'])
        return Response({'status': 'ok'})

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Usuario, CentroEstetica, Sucursal
from .serializers import (
    UsuarioSerializer,
    UsuarioListSerializer,
    UsuarioDetailSerializer,
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
    CentroEsteticaSerializer,
    SucursalSerializer,
    CustomTokenObtainPairSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener JWT tokens junto con los datos del usuario
    """
    serializer_class = CustomTokenObtainPairSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de empleados/usuarios
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rol', 'activo', 'sucursal']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'especialidades']
    ordering_fields = ['last_name', 'first_name', 'fecha_ingreso', 'creado_en']
    ordering = ['last_name', 'first_name']

    def get_queryset(self):
        """
        Filtrar usuarios por centro estética
        """
        user = self.request.user
        if hasattr(user, 'centro_estetica') and user.centro_estetica:
            return Usuario.objects.filter(
                centro_estetica=user.centro_estetica
            ).select_related('sucursal')
        return Usuario.objects.none()

    def get_serializer_class(self):
        """
        Usar diferentes serializers según la acción
        """
        if self.action == 'retrieve':
            return UsuarioDetailSerializer
        elif self.action == 'create':
            return UsuarioCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UsuarioUpdateSerializer
        elif self.action == 'me':
            return UsuarioDetailSerializer
        return UsuarioListSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Endpoint para obtener los datos del usuario actual
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def profesionales(self, request):
        """
        Obtener solo usuarios que sean profesionales (activos)
        Útil para selects de profesionales en turnos
        """
        profesionales = self.get_queryset().filter(activo=True)
        serializer = UsuarioListSerializer(profesionales, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Activar/desactivar un empleado
        """
        usuario = self.get_object()
        nuevo_estado = request.data.get('activo')

        if nuevo_estado is None:
            return Response(
                {'error': 'Se requiere el campo "activo"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario.activo = nuevo_estado
        usuario.save()

        serializer = self.get_serializer(usuario)
        return Response(serializer.data)


class CentroEsteticaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo CentroEstetica
    """
    queryset = CentroEstetica.objects.all()
    serializer_class = CentroEsteticaSerializer
    permission_classes = [IsAuthenticated]


class SucursalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Sucursal
    """
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer
    permission_classes = [IsAuthenticated]

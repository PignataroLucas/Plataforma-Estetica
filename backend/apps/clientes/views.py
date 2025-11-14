from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cliente, HistorialCliente
from .serializers import ClienteSerializer, HistorialClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Cliente - CRUD completo
    Aplica principios SOLID:
    - SRP: Solo maneja operaciones CRUD de clientes
    - OCP: Extensible via queryset filters y permissions
    - DIP: Depende de abstracciones (ModelViewSet, serializers)

    Endpoints:
    - GET /api/clientes/ - Listar todos los clientes
    - POST /api/clientes/ - Crear nuevo cliente
    - GET /api/clientes/{id}/ - Obtener un cliente
    - PATCH /api/clientes/{id}/ - Actualizar parcialmente un cliente
    - PUT /api/clientes/{id}/ - Actualizar completamente un cliente
    - DELETE /api/clientes/{id}/ - Eliminar un cliente

    Features:
    - Búsqueda: ?search=nombre
    - Filtros: ?activo=true&acepta_whatsapp=true
    - Ordenamiento: ?ordering=apellido,-creado_en
    """
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Búsqueda por nombre, apellido, email, teléfono, documento
    search_fields = ['nombre', 'apellido', 'email', 'telefono', 'numero_documento']

    # Filtros disponibles
    filterset_fields = ['activo', 'acepta_promociones', 'acepta_whatsapp', 'tipo_documento']

    # Campos por los que se puede ordenar
    ordering_fields = ['apellido', 'nombre', 'creado_en', 'ultima_visita']
    ordering = ['apellido', 'nombre']

    def get_queryset(self):
        """
        Filtrar clientes por centro_estetica del usuario (Multi-tenancy)
        IMPORTANTE: Garantiza aislamiento de datos entre centros
        """
        user = self.request.user
        if hasattr(user, 'centro_estetica') and user.centro_estetica:
            return Cliente.objects.filter(centro_estetica=user.centro_estetica)
        return Cliente.objects.none()

    def perform_create(self, serializer):
        """
        Asignar automáticamente el centro_estetica del usuario actual
        """
        if hasattr(self.request.user, 'centro_estetica'):
            serializer.save(centro_estetica=self.request.user.centro_estetica)
        else:
            serializer.save()


class HistorialClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para HistorialCliente - Gestión de historial de tratamientos
    """
    serializer_class = HistorialClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['cliente', 'servicio', 'profesional']
    ordering_fields = ['fecha', 'creado_en']
    ordering = ['-fecha']

    def get_queryset(self):
        """
        Filtrar historial por clientes del centro del usuario (Multi-tenancy)
        """
        user = self.request.user
        if hasattr(user, 'centro_estetica') and user.centro_estetica:
            return HistorialCliente.objects.filter(
                cliente__centro_estetica=user.centro_estetica
            )
        return HistorialCliente.objects.none()

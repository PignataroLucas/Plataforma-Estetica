from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Servicio, CategoriaServicio
from .serializers import ServicioSerializer, CategoriaServicioSerializer


class ServicioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Servicio - CRUD completo
    Aplica principios SOLID:
    - SRP: Solo maneja operaciones CRUD de servicios
    - OCP: Extensible via queryset filters y permissions
    - DIP: Depende de abstracciones (ModelViewSet, serializers)

    Endpoints:
    - GET /api/servicios/servicios/ - Listar todos los servicios
    - POST /api/servicios/servicios/ - Crear nuevo servicio
    - GET /api/servicios/servicios/{id}/ - Obtener un servicio
    - PATCH /api/servicios/servicios/{id}/ - Actualizar parcialmente un servicio
    - PUT /api/servicios/servicios/{id}/ - Actualizar completamente un servicio
    - DELETE /api/servicios/servicios/{id}/ - Eliminar un servicio

    Features:
    - Búsqueda: ?search=nombre
    - Filtros: ?activo=true&categoria=1
    - Ordenamiento: ?ordering=nombre,-precio
    """
    serializer_class = ServicioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Búsqueda por nombre, descripción, código
    search_fields = ['nombre', 'descripcion', 'codigo']

    # Filtros disponibles
    filterset_fields = ['activo', 'categoria', 'requiere_profesional']

    # Campos por los que se puede ordenar
    ordering_fields = ['nombre', 'precio', 'duracion_minutos', 'creado_en']
    ordering = ['nombre']

    def get_queryset(self):
        """
        Filtrar servicios por sucursal del usuario (Multi-tenancy)
        IMPORTANTE: Garantiza aislamiento de datos entre sucursales
        """
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return Servicio.objects.filter(sucursal=user.sucursal)
        return Servicio.objects.none()

    def perform_create(self, serializer):
        """
        Asignar automáticamente la sucursal del usuario actual
        """
        if hasattr(self.request.user, 'sucursal'):
            serializer.save(sucursal=self.request.user.sucursal)
        else:
            serializer.save()


class CategoriaServicioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CategoriaServicio - Gestión de categorías
    """
    serializer_class = CategoriaServicioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    filterset_fields = ['activa']
    ordering_fields = ['nombre', 'creado_en']
    ordering = ['nombre']

    def get_queryset(self):
        """
        Filtrar categorías por sucursal del usuario (Multi-tenancy)
        """
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return CategoriaServicio.objects.filter(sucursal=user.sucursal)
        return CategoriaServicio.objects.none()

    def perform_create(self, serializer):
        """
        Asignar automáticamente la sucursal del usuario actual
        """
        if hasattr(self.request.user, 'sucursal'):
            serializer.save(sucursal=self.request.user.sucursal)
        else:
            serializer.save()

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Servicio, CategoriaServicio, MaquinaAlquilada
from .serializers import ServicioSerializer, CategoriaServicioSerializer, MaquinaAlquiladaSerializer


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

        Por defecto solo muestra servicios activos.
        Use ?activo=false para ver servicios inactivos
        """
        user = self.request.user
        queryset = Servicio.objects.none()

        if hasattr(user, 'sucursal') and user.sucursal:
            queryset = Servicio.objects.filter(sucursal=user.sucursal)

        # Por defecto solo mostrar activos, a menos que se especifique activo=false
        if self.request.query_params.get('activo') != 'false':
            queryset = queryset.filter(activo=True)

        return queryset

    def perform_create(self, serializer):
        """
        Asignar automáticamente la sucursal del usuario actual
        """
        if hasattr(self.request.user, 'sucursal'):
            serializer.save(sucursal=self.request.user.sucursal)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """
        Soft delete: Mark service as inactive instead of deleting.
        This prevents errors when services have associated appointments.
        """
        instance.activo = False
        instance.save()


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


class MaquinaAlquiladaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para MaquinaAlquilada - Gestión de máquinas/equipos alquilados

    Las máquinas tienen un costo diario y se asocian a servicios para calcular profit.
    """
    serializer_class = MaquinaAlquiladaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion', 'proveedor']
    filterset_fields = ['activa']
    ordering_fields = ['nombre', 'costo_diario', 'creado_en']
    ordering = ['nombre']

    def get_queryset(self):
        """
        Filtrar máquinas por sucursal del usuario (Multi-tenancy)
        """
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return MaquinaAlquilada.objects.filter(sucursal=user.sucursal)
        return MaquinaAlquilada.objects.none()

    def perform_create(self, serializer):
        """
        Asignar automáticamente la sucursal del usuario actual
        """
        if hasattr(self.request.user, 'sucursal'):
            serializer.save(sucursal=self.request.user.sucursal)
        else:
            serializer.save()

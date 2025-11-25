from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cliente, HistorialCliente, PlanTratamiento, RutinaCuidado, NotaCliente
from .serializers import (
    ClienteSerializer,
    HistorialClienteSerializer,
    PlanTratamientoSerializer,
    RutinaCuidadoSerializer,
    NotaClienteSerializer
)


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


class PlanTratamientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para PlanTratamiento - Gestión de planes de tratamiento

    Endpoints:
    - GET /api/planes-tratamiento/ - Listar todos los planes
    - POST /api/planes-tratamiento/ - Crear nuevo plan
    - GET /api/planes-tratamiento/{id}/ - Obtener un plan
    - PATCH /api/planes-tratamiento/{id}/ - Actualizar parcialmente un plan
    - PUT /api/planes-tratamiento/{id}/ - Actualizar completamente un plan
    - DELETE /api/planes-tratamiento/{id}/ - Eliminar un plan

    Features:
    - Filtros: ?cliente=1
    - Ordenamiento: ?ordering=-creado_en
    """
    serializer_class = PlanTratamientoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['cliente']
    ordering_fields = ['creado_en', 'proximo_turno']
    ordering = ['-creado_en']

    def get_queryset(self):
        """
        Filtrar planes por clientes del centro del usuario (Multi-tenancy)
        """
        user = self.request.user
        if hasattr(user, 'centro_estetica') and user.centro_estetica:
            return PlanTratamiento.objects.filter(
                cliente__centro_estetica=user.centro_estetica
            ).select_related('cliente', 'creado_por')
        return PlanTratamiento.objects.none()


class RutinaCuidadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para RutinaCuidado - Gestión de rutinas de cuidado

    Endpoints:
    - GET /api/rutinas-cuidado/ - Listar todas las rutinas
    - POST /api/rutinas-cuidado/ - Crear nueva rutina
    - GET /api/rutinas-cuidado/{id}/ - Obtener una rutina
    - PATCH /api/rutinas-cuidado/{id}/ - Actualizar parcialmente una rutina
    - PUT /api/rutinas-cuidado/{id}/ - Actualizar completamente una rutina
    - DELETE /api/rutinas-cuidado/{id}/ - Eliminar una rutina

    Features:
    - Filtros: ?cliente=1&activa=true
    - Ordenamiento: ?ordering=-creado_en
    """
    serializer_class = RutinaCuidadoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['cliente', 'activa']
    ordering_fields = ['creado_en']
    ordering = ['-creado_en']

    def get_queryset(self):
        """
        Filtrar rutinas por clientes del centro del usuario (Multi-tenancy)
        """
        user = self.request.user
        if hasattr(user, 'centro_estetica') and user.centro_estetica:
            return RutinaCuidado.objects.filter(
                cliente__centro_estetica=user.centro_estetica
            ).select_related('cliente', 'creado_por')
        return RutinaCuidado.objects.none()


class NotaClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para NotaCliente - Gestión de notas de pacientes

    Endpoints:
    - GET /api/notas-cliente/ - Listar todas las notas
    - POST /api/notas-cliente/ - Crear nueva nota
    - GET /api/notas-cliente/{id}/ - Obtener una nota
    - PATCH /api/notas-cliente/{id}/ - Actualizar parcialmente una nota
    - PUT /api/notas-cliente/{id}/ - Actualizar completamente una nota
    - DELETE /api/notas-cliente/{id}/ - Eliminar una nota

    Features:
    - Filtros: ?cliente=1&tipo_nota=IMPORTANTE&destacada=true
    - Ordenamiento: ?ordering=-destacada,-creado_en (por defecto)
    """
    serializer_class = NotaClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['cliente', 'tipo_nota', 'destacada', 'visible_para']
    ordering_fields = ['creado_en', 'destacada']
    ordering = ['-destacada', '-creado_en']  # Destacadas primero, luego más recientes

    def get_queryset(self):
        """
        Filtrar notas por clientes del centro del usuario (Multi-tenancy)
        Aplica reglas de visibilidad según el usuario
        """
        user = self.request.user
        if hasattr(user, 'centro_estetica') and user.centro_estetica:
            queryset = NotaCliente.objects.filter(
                cliente__centro_estetica=user.centro_estetica
            ).select_related('cliente', 'autor')

            # Aplicar filtros de visibilidad
            # Admin ve todas las notas
            if user.rol == 'ADMIN':
                return queryset

            # Empleados ven: TODOS + Solo autor (si es el autor)
            return queryset.filter(
                visible_para__in=['TODOS']
            ) | queryset.filter(
                visible_para='SOLO_AUTOR',
                autor=user
            )

        return NotaCliente.objects.none()

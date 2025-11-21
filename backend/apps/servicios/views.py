from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Servicio, CategoriaServicio, MaquinaAlquilada, AlquilerMaquina
from .serializers import ServicioSerializer, CategoriaServicioSerializer, MaquinaAlquiladaSerializer, AlquilerMaquinaSerializer


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


class AlquilerMaquinaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para AlquilerMaquina - Programación de alquileres

    Permite registrar alquileres antes del día para tener control sobre
    cuándo realmente se alquila la máquina.
    """
    serializer_class = AlquilerMaquinaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['maquina', 'fecha', 'estado']
    ordering_fields = ['fecha', 'creado_en']
    ordering = ['-fecha']

    def get_queryset(self):
        """
        Filtrar alquileres por sucursal del usuario
        """
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return AlquilerMaquina.objects.filter(sucursal=user.sucursal).select_related(
                'maquina', 'transaccion_gasto', 'creado_por'
            )
        return AlquilerMaquina.objects.none()

    def perform_create(self, serializer):
        """
        Asignar automáticamente la sucursal y usuario actual
        """
        if hasattr(self.request.user, 'sucursal'):
            serializer.save(
                sucursal=self.request.user.sucursal,
                creado_por=self.request.user
            )
        else:
            serializer.save(creado_por=self.request.user)

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Get rentals that need confirmation (have appointments but not confirmed)
        """
        from apps.turnos.models import Turno
        from django.utils import timezone
        from django.db.models import Q, Count

        queryset = self.get_queryset()
        
        # Get dates with appointments using machines
        fechas_con_turnos = Turno.objects.filter(
            servicio__maquina_alquilada__isnull=False,
            sucursal=request.user.sucursal,
            fecha_hora_inicio__date__gte=timezone.now().date()
        ).values(
            'servicio__maquina_alquilada',
            'fecha_hora_inicio__date'
        ).annotate(
            cantidad_turnos=Count('id')
        )

        pendientes = []
        for item in fechas_con_turnos:
            maquina_id = item['servicio__maquina_alquilada']
            fecha = item['fecha_hora_inicio__date']
            
            # Check if rental exists and is confirmed
            alquiler = queryset.filter(
                maquina_id=maquina_id,
                fecha=fecha
            ).first()

            if not alquiler or alquiler.estado == AlquilerMaquina.Estado.PROGRAMADO:
                maquina = MaquinaAlquilada.objects.get(pk=maquina_id)
                pendientes.append({
                    'maquina_id': maquina_id,
                    'maquina_nombre': maquina.nombre,
                    'fecha': fecha,
                    'cantidad_turnos': item['cantidad_turnos'],
                    'costo_diario': maquina.costo_diario,
                    'alquiler_id': alquiler.id if alquiler else None,
                    'estado': alquiler.estado if alquiler else None
                })

        return Response(pendientes)

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """
        Confirm a rental
        """
        alquiler = self.get_object()
        
        if alquiler.estado == AlquilerMaquina.Estado.COBRADO:
            return Response(
                {'error': 'Este alquiler ya fue cobrado y no se puede modificar'},
                status=status.HTTP_400_BAD_REQUEST
            )

        alquiler.estado = AlquilerMaquina.Estado.CONFIRMADO
        alquiler.save()

        return Response({
            'message': 'Alquiler confirmado',
            'alquiler': AlquilerMaquinaSerializer(alquiler).data
        })

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancel a rental
        """
        alquiler = self.get_object()
        
        if alquiler.estado == AlquilerMaquina.Estado.COBRADO:
            return Response(
                {'error': 'Este alquiler ya fue cobrado. Elimina la transacción de gasto manualmente en Finanzas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        alquiler.estado = AlquilerMaquina.Estado.CANCELADO
        alquiler.save()

        return Response({
            'message': 'Alquiler cancelado',
            'alquiler': AlquilerMaquinaSerializer(alquiler).data
        })

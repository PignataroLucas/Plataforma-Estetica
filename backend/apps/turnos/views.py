from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from datetime import timedelta
from .models import Turno
from .serializers import (
    TurnoListSerializer,
    TurnoDetailSerializer,
    TurnoCreateUpdateSerializer
)
from apps.notificaciones.tasks import (
    enviar_confirmacion_turno_task,
    enviar_cancelacion_turno_task
)


class TurnoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de turnos con prevención de double-booking
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'estado_pago', 'profesional', 'cliente', 'servicio']
    search_fields = ['cliente__nombre', 'cliente__apellido', 'servicio__nombre', 'notas']
    ordering_fields = ['fecha_hora_inicio', 'creado_en', 'monto_total']
    ordering = ['fecha_hora_inicio']

    def get_queryset(self):
        """
        Filtrar turnos por sucursal del usuario
        """
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            queryset = Turno.objects.filter(sucursal=user.sucursal).select_related(
                'cliente', 'servicio', 'profesional', 'creado_por'
            )

            # Filtros adicionales por query params
            fecha_desde = self.request.query_params.get('fecha_desde', None)
            fecha_hasta = self.request.query_params.get('fecha_hasta', None)

            if fecha_desde:
                queryset = queryset.filter(fecha_hora_inicio__gte=fecha_desde)
            if fecha_hasta:
                queryset = queryset.filter(fecha_hora_inicio__lte=fecha_hasta)

            return queryset
        return Turno.objects.none()

    def get_serializer_class(self):
        """
        Usar diferentes serializers según la acción
        """
        if self.action == 'retrieve':
            return TurnoDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TurnoCreateUpdateSerializer
        return TurnoListSerializer

    def perform_create(self, serializer):
        """
        Al crear un turno, enviar notificación de confirmación
        """
        turno = serializer.save(creado_por=self.request.user)

        # Enviar confirmación de turno por WhatsApp de forma asíncrona
        enviar_confirmacion_turno_task.delay(turno.id)

        return turno

    @action(detail=False, methods=['get'])
    def hoy(self, request):
        """
        Obtener turnos del día de hoy
        """
        hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoy_fin = hoy_inicio + timedelta(days=1)

        turnos = self.get_queryset().filter(
            fecha_hora_inicio__gte=hoy_inicio,
            fecha_hora_inicio__lt=hoy_fin
        )

        serializer = self.get_serializer(turnos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """
        Obtener próximos turnos (próximos 7 días)
        """
        ahora = timezone.now()
        en_7_dias = ahora + timedelta(days=7)

        turnos = self.get_queryset().filter(
            fecha_hora_inicio__gte=ahora,
            fecha_hora_inicio__lte=en_7_dias,
            estado__in=[Turno.Estado.PENDIENTE, Turno.Estado.CONFIRMADO]
        )

        serializer = self.get_serializer(turnos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def verificar_disponibilidad(self, request):
        """
        Verificar si un horario está disponible sin crear el turno
        """
        profesional_id = request.data.get('profesional')
        fecha_hora_inicio = request.data.get('fecha_hora_inicio')
        fecha_hora_fin = request.data.get('fecha_hora_fin')
        turno_id = request.data.get('turno_id', None)  # Para excluir al actualizar

        if not all([profesional_id, fecha_hora_inicio, fecha_hora_fin]):
            return Response(
                {'error': 'Se requieren profesional, fecha_hora_inicio y fecha_hora_fin'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.empleados.models import Usuario
        try:
            profesional = Usuario.objects.get(id=profesional_id)
        except Usuario.DoesNotExist:
            return Response(
                {'error': 'Profesional no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Crear objeto temporal para verificar disponibilidad
        turno_temp = Turno(
            profesional=profesional,
            sucursal=request.user.sucursal,
            fecha_hora_inicio=fecha_hora_inicio,
            fecha_hora_fin=fecha_hora_fin,
        )

        if turno_id:
            turno_temp.pk = turno_id

        disponible, conflictos = turno_temp.verificar_disponibilidad()

        if disponible:
            return Response({'disponible': True})
        else:
            conflicto_data = []
            for conflicto in conflictos:
                conflicto_data.append({
                    'id': conflicto.id,
                    'fecha_hora_inicio': conflicto.fecha_hora_inicio,
                    'fecha_hora_fin': conflicto.fecha_hora_fin,
                    'cliente': conflicto.cliente.nombre_completo,
                    'servicio': conflicto.servicio.nombre,
                })

            return Response({
                'disponible': False,
                'conflictos': conflicto_data
            })

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Cambiar el estado de un turno
        """
        turno = self.get_object()
        estado_anterior = turno.estado
        nuevo_estado = request.data.get('estado')

        if nuevo_estado not in dict(Turno.Estado.choices):
            return Response(
                {'error': 'Estado inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        turno.estado = nuevo_estado
        turno.save()

        # Si se cancela un turno, enviar notificación
        if nuevo_estado == Turno.Estado.CANCELADO and estado_anterior != Turno.Estado.CANCELADO:
            enviar_cancelacion_turno_task.delay(turno.id)

        serializer = self.get_serializer(turno)
        return Response(serializer.data)

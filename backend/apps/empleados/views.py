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
from .permissions import IsAdminOrManager


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener JWT tokens junto con los datos del usuario
    """
    serializer_class = CustomTokenObtainPairSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de empleados/usuarios
    IMPORTANTE: Requiere rol ADMIN o MANAGER para CRUD
    Los endpoints 'me' y 'profesionales' son accesibles por todos los autenticados
    """
    permission_classes = [IsAdminOrManager]
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Endpoint para obtener los datos del usuario actual
        Accesible por todos los usuarios autenticados
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profesionales(self, request):
        """
        Obtener solo usuarios que sean profesionales (activos)
        Útil para selects de profesionales en turnos
        Accesible por todos los usuarios autenticados
        """
        profesionales = self.get_queryset().filter(activo=True)
        serializer = UsuarioListSerializer(profesionales, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def horarios_disponibles(self, request, pk=None):
        """
        Obtener horarios disponibles para un profesional en una fecha específica
        Requiere query params: fecha (YYYY-MM-DD), servicio_id
        Retorna array de slots disponibles considerando:
        - Horario laboral del profesional
        - Días laborales
        - Turnos ya agendados
        - Duración del servicio
        """
        from datetime import datetime, timedelta, time
        from django.utils import timezone
        from apps.servicios.models import Servicio
        from apps.turnos.models import Turno

        # Validar parámetros requeridos
        fecha_str = request.query_params.get('fecha')
        servicio_id = request.query_params.get('servicio_id')

        if not fecha_str or not servicio_id:
            return Response(
                {'error': 'Se requieren los parámetros "fecha" y "servicio_id"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parsear fecha
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener servicio
        try:
            servicio = Servicio.objects.get(id=servicio_id)
        except Servicio.DoesNotExist:
            return Response(
                {'error': 'Servicio no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener profesional
        profesional = self.get_object()

        # Verificar si el profesional tiene horario configurado
        if not profesional.horario_inicio or not profesional.horario_fin:
            # Si no tiene horario configurado, usar horario por defecto (8:00 - 19:00)
            horario_inicio = time(8, 0)
            horario_fin = time(19, 0)
        else:
            horario_inicio = profesional.horario_inicio
            horario_fin = profesional.horario_fin

        # Verificar día laboral
        dias_semana = {
            0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves',
            4: 'viernes', 5: 'sabado', 6: 'domingo'
        }
        dia_semana = dias_semana[fecha.weekday()]

        # Si tiene días laborales configurados, verificar
        if profesional.dias_laborales and dia_semana not in profesional.dias_laborales:
            return Response({
                'disponible': False,
                'mensaje': f'El profesional no trabaja los {dia_semana}s',
                'slots': []
            })

        # Obtener turnos existentes del profesional en esa fecha
        turnos_existentes = Turno.objects.filter(
            profesional=profesional,
            fecha_hora_inicio__date=fecha,
            estado__in=['PENDIENTE', 'CONFIRMADO']
        ).order_by('fecha_hora_inicio')

        # Generar slots disponibles
        duracion_servicio = servicio.duracion_minutos
        intervalo = profesional.intervalo_minutos

        # Crear lista de slots (usar timezone-aware datetimes)
        slots_disponibles = []

        # Crear datetime naive y luego convertir a aware usando el timezone configurado
        hora_actual_naive = datetime.combine(fecha, horario_inicio)
        hora_fin_naive = datetime.combine(fecha, horario_fin)

        # Hacer timezone-aware usando el timezone actual (que usa Django settings)
        # Esto garantiza que las comparaciones con turnos de la DB sean correctas
        hora_actual = timezone.make_aware(hora_actual_naive)
        hora_fin = timezone.make_aware(hora_fin_naive)

        while hora_actual + timedelta(minutes=duracion_servicio) <= hora_fin:
            # Verificar si este slot está disponible
            slot_fin = hora_actual + timedelta(minutes=duracion_servicio)

            # Verificar conflictos con turnos existentes
            tiene_conflicto = False
            for turno in turnos_existentes:
                turno_inicio = turno.fecha_hora_inicio
                turno_fin = turno.fecha_hora_fin

                # Verificar overlap (ambos datetime son ahora aware)
                if (hora_actual < turno_fin and slot_fin > turno_inicio):
                    tiene_conflicto = True
                    break

            if not tiene_conflicto:
                # Guardar solo la hora local (sin timezone info para el frontend)
                slots_disponibles.append({
                    'hora': hora_actual.strftime('%H:%M'),
                    'hora_fin': slot_fin.strftime('%H:%M'),
                    'disponible': True
                })

            # Avanzar al siguiente slot
            hora_actual += timedelta(minutes=intervalo)

        return Response({
            'disponible': True,
            'fecha': fecha_str,
            'profesional': {
                'id': profesional.id,
                'nombre': profesional.get_full_name()
            },
            'servicio': {
                'id': servicio.id,
                'nombre': servicio.nombre,
                'duracion_minutos': duracion_servicio
            },
            'horario_laboral': {
                'inicio': horario_inicio.strftime('%H:%M'),
                'fin': horario_fin.strftime('%H:%M')
            },
            'slots': slots_disponibles
        })

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

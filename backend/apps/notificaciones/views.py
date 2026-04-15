from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from django.db.models import Count, Q
import logging

from .models import Notificacion, MensajeTemplate
from .serializers import (
    NotificacionSerializer,
    NotificacionListSerializer,
    EnviarNotificacionManualSerializer,
    MensajeTemplateSerializer,
    MensajeTemplateListSerializer
)
from .tasks import enviar_confirmacion_turno_task
from .services import whatsapp_service
from apps.clientes.models import Cliente
from apps.turnos.models import Turno


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Notificaciones WhatsApp

    Endpoints:
    - GET /api/notificaciones/ - Listar todas las notificaciones
    - GET /api/notificaciones/{id}/ - Obtener una notificación
    - POST /api/notificaciones/enviar_manual/ - Enviar mensaje manual
    - GET /api/notificaciones/historial_cliente/?cliente_id=X - Historial de un cliente
    - GET /api/notificaciones/estadisticas/ - Estadísticas de envíos

    Features:
    - Búsqueda: ?search=mensaje
    - Filtros: ?estado=ENVIADO&tipo=CONFIRMACION_TURNO&cliente=123
    - Ordenamiento: ?ordering=-creado_en
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Búsqueda por mensaje
    search_fields = ['mensaje', 'telefono_destino', 'cliente__nombre', 'cliente__apellido']

    # Filtros disponibles
    filterset_fields = ['estado', 'tipo', 'cliente', 'turno', 'sucursal']

    # Campos por los que se puede ordenar
    ordering_fields = ['creado_en', 'enviado_en', 'estado', 'tipo']
    ordering = ['-creado_en']

    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return NotificacionListSerializer
        return NotificacionSerializer

    def get_queryset(self):
        """
        Filtrar notificaciones por sucursal del usuario (Multi-tenancy)
        IMPORTANTE: Garantiza aislamiento de datos entre centros
        """
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return Notificacion.objects.filter(
                sucursal=user.sucursal
            ).select_related('cliente', 'turno', 'sucursal')
        return Notificacion.objects.none()

    @action(detail=False, methods=['post'])
    def enviar_manual(self, request):
        """
        Enviar notificación manual de WhatsApp

        POST /api/notificaciones/enviar_manual/
        Body: {
            "cliente_id": 123,
            "tipo": "PROMOCION",
            "mensaje": "Texto del mensaje...",
            "turno_id": 456  // opcional
        }
        """
        serializer = EnviarNotificacionManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Obtener datos validados
        cliente_id = serializer.validated_data['cliente_id']
        tipo = serializer.validated_data['tipo']
        mensaje = serializer.validated_data['mensaje']
        turno_id = serializer.validated_data.get('turno_id')

        # Validar que el cliente pertenece al centro del usuario
        try:
            cliente = Cliente.objects.get(
                id=cliente_id,
                centro_estetica=request.user.centro_estetica
            )
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado o no pertenece a tu centro'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar turno si fue proporcionado
        turno = None
        if turno_id:
            try:
                turno = Turno.objects.get(
                    id=turno_id,
                    sucursal=request.user.sucursal
                )
            except Turno.DoesNotExist:
                return Response(
                    {'error': 'Turno no encontrado o no pertenece a tu sucursal'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Validar que el cliente acepta WhatsApp
        if not cliente.acepta_whatsapp:
            return Response(
                {'error': 'El cliente no acepta notificaciones por WhatsApp'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Enviar mensaje
        notificacion = whatsapp_service.enviar_mensaje(
            telefono=cliente.telefono,
            mensaje=mensaje,
            tipo_notificacion=tipo,
            cliente=cliente,
            turno=turno,
            sucursal=request.user.sucursal
        )

        # Serializar y retornar
        response_serializer = NotificacionSerializer(notificacion)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def historial_cliente(self, request):
        """
        Obtener historial de notificaciones de un cliente

        GET /api/notificaciones/historial_cliente/?cliente_id=123
        """
        cliente_id = request.query_params.get('cliente_id')

        if not cliente_id:
            return Response(
                {'error': 'Se requiere el parámetro cliente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que el cliente pertenece al centro del usuario
        try:
            cliente = Cliente.objects.get(
                id=cliente_id,
                centro_estetica=request.user.centro_estetica
            )
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado o no pertenece a tu centro'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener notificaciones del cliente
        notificaciones = self.get_queryset().filter(cliente=cliente)

        # Paginación
        page = self.paginate_queryset(notificaciones)
        if page is not None:
            serializer = NotificacionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotificacionListSerializer(notificaciones, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de notificaciones

        GET /api/notificaciones/estadisticas/?periodo=30

        Params:
        - periodo: días hacia atrás (default: 30)
        """
        # Obtener parámetro de período (días)
        periodo_dias = int(request.query_params.get('periodo', 30))
        fecha_desde = timezone.now() - timedelta(days=periodo_dias)

        # Filtrar notificaciones del período
        notificaciones = self.get_queryset().filter(
            creado_en__gte=fecha_desde
        )

        # Estadísticas generales
        total = notificaciones.count()

        # Por estado
        por_estado = notificaciones.values('estado').annotate(
            total=Count('id')
        ).order_by('-total')

        # Por tipo
        por_tipo = notificaciones.values('tipo').annotate(
            total=Count('id')
        ).order_by('-total')

        # Tasa de éxito
        exitosos = notificaciones.filter(
            estado__in=['ENVIADO', 'ENTREGADO', 'LEIDO']
        ).count()
        fallidos = notificaciones.filter(estado='FALLIDO').count()
        tasa_exito = round((exitosos / total * 100), 2) if total > 0 else 0

        # Últimas 24 horas
        ultimas_24h = notificaciones.filter(
            creado_en__gte=timezone.now() - timedelta(hours=24)
        ).count()

        return Response({
            'periodo_dias': periodo_dias,
            'total_notificaciones': total,
            'exitosos': exitosos,
            'fallidos': fallidos,
            'tasa_exito': tasa_exito,
            'ultimas_24h': ultimas_24h,
            'por_estado': list(por_estado),
            'por_tipo': list(por_tipo)
        })

    @action(detail=False, methods=['post'])
    def reenviar(self, request):
        """
        Reenviar una notificación fallida

        POST /api/notificaciones/reenviar/
        Body: {"notificacion_id": 123}
        """
        notificacion_id = request.data.get('notificacion_id')

        if not notificacion_id:
            return Response(
                {'error': 'Se requiere el campo notificacion_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener notificación
        try:
            notificacion_original = self.get_queryset().get(id=notificacion_id)
        except Notificacion.DoesNotExist:
            return Response(
                {'error': 'Notificación no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar que sea una notificación fallida
        if notificacion_original.estado != 'FALLIDO':
            return Response(
                {'error': 'Solo se pueden reenviar notificaciones fallidas'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reenviar
        nueva_notificacion = whatsapp_service.enviar_mensaje(
            telefono=notificacion_original.telefono_destino,
            mensaje=notificacion_original.mensaje,
            tipo_notificacion=notificacion_original.tipo,
            cliente=notificacion_original.cliente,
            turno=notificacion_original.turno,
            sucursal=notificacion_original.sucursal
        )

        serializer = NotificacionSerializer(nueva_notificacion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MensajeTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar plantillas de mensajes WhatsApp

    Endpoints:
    - GET /api/mensajes-templates/ - Listar templates de la sucursal
    - GET /api/mensajes-templates/{id}/ - Obtener un template
    - POST /api/mensajes-templates/ - Crear template (ADMIN only)
    - PUT /api/mensajes-templates/{id}/ - Actualizar template (ADMIN only)
    - DELETE /api/mensajes-templates/{id}/ - Eliminar template (ADMIN only)
    - POST /api/mensajes-templates/reset_defaults/ - Restaurar templates por defecto (ADMIN only)
    - GET /api/mensajes-templates/variables_disponibles/ - Listar variables disponibles

    Permisos: Solo ADMIN puede crear/editar/eliminar templates
    """
    permission_classes = [IsAuthenticated]
    pagination_class = None  # No necesitamos paginación para 6 templates
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'activo']
    ordering_fields = ['tipo', 'actualizado_en']
    ordering = ['tipo']

    def get_serializer_class(self):
        if self.action == 'list':
            return MensajeTemplateListSerializer
        return MensajeTemplateSerializer

    def get_queryset(self):
        """Filtrar por sucursal del usuario"""
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return MensajeTemplate.objects.filter(sucursal=user.sucursal)
        return MensajeTemplate.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Listar templates, creando los defaults automáticamente si no existen
        """
        # Crear templates por defecto si no existen
        if hasattr(request.user, 'sucursal') and request.user.sucursal:
            self._asegurar_templates_default(request.user.sucursal)

        return super().list(request, *args, **kwargs)

    def _asegurar_templates_default(self, sucursal):
        """Crear templates por defecto si no existen para esta sucursal"""
        defaults = {
            'CONFIRMACION': """¡Hola {nombre_cliente}!

Tu turno ha sido confirmado ✅

📅 Fecha: {fecha}
🕐 Hora: {hora}
💆 Servicio: {servicio}
👤 Profesional: {profesional}
📍 Sucursal: {sucursal_nombre}

Te enviaremos recordatorios antes de tu turno.

¡Te esperamos!""",

            'RECORDATORIO_24H': """Hola {nombre_cliente} 👋

Te recordamos tu turno para mañana:

🕐 {hora} - {servicio}
👤 {profesional}
📍 {sucursal_nombre}

Si necesitas cancelar o reprogramar, contáctanos.

¡Te esperamos!""",

            'RECORDATORIO_2H': """¡Tu turno es en 2 horas! ⏰

🕐 {hora} - {servicio}
📍 {sucursal_direccion}

¡Te esperamos!""",

            'CANCELACION': """Hola {nombre_cliente},

Tu turno del {fecha} a las {hora} ha sido cancelado.

Si deseas reprogramar, contáctanos.

Saludos!""",

            'MODIFICACION': """Hola {nombre_cliente},

Tu turno ha sido modificado ✏️

Nueva fecha y hora:
📅 {fecha}
🕐 {hora}
💆 Servicio: {servicio}
👤 Profesional: {profesional}

¡Nos vemos pronto!""",

            'PROMOCION': """¡Hola {nombre_cliente}! 🎁

Tenemos una promoción especial para ti.

Contáctanos para más información.

📍 {sucursal_nombre}
📞 {sucursal_telefono}"""
        }

        for tipo, mensaje in defaults.items():
            MensajeTemplate.objects.get_or_create(
                sucursal=sucursal,
                tipo=tipo,
                defaults={'mensaje': mensaje, 'activo': True}
            )

    def perform_create(self, serializer):
        """Guardar con sucursal y usuario actual"""
        serializer.save(
            sucursal=self.request.user.sucursal,
            actualizado_por=self.request.user
        )

    def perform_update(self, serializer):
        """Registrar quién actualizó el template"""
        serializer.save(actualizado_por=self.request.user)

    def create(self, request, *args, **kwargs):
        """Solo ADMIN puede crear templates"""
        if not (hasattr(request.user, 'role') and request.user.role == 'ADMIN'):
            return Response(
                {'error': 'Solo los administradores pueden crear templates de mensajes'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Solo ADMIN puede editar templates"""
        if not (hasattr(request.user, 'role') and request.user.role == 'ADMIN'):
            return Response(
                {'error': 'Solo los administradores pueden editar templates de mensajes'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Solo ADMIN puede eliminar templates"""
        if not (hasattr(request.user, 'role') and request.user.role == 'ADMIN'):
            return Response(
                {'error': 'Solo los administradores pueden eliminar templates de mensajes'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def reset_defaults(self, request):
        """
        Restaurar templates por defecto

        POST /api/mensajes-templates/reset_defaults/
        Body: {"tipo": "CONFIRMACION"} // Opcional, si no se envía resetea todos
        """
        if not (hasattr(request.user, 'role') and request.user.role == 'ADMIN'):
            return Response(
                {'error': 'Solo los administradores pueden restaurar templates'},
                status=status.HTTP_403_FORBIDDEN
            )

        tipo = request.data.get('tipo')
        sucursal = request.user.sucursal

        # Templates por defecto (los actuales de services.py)
        defaults = {
            'CONFIRMACION': """¡Hola {nombre_cliente}!

Tu turno ha sido confirmado ✅

📅 Fecha: {fecha}
🕐 Hora: {hora}
💆 Servicio: {servicio}
👤 Profesional: {profesional}
📍 Sucursal: {sucursal_nombre}

Te enviaremos recordatorios antes de tu turno.

¡Te esperamos!""",

            'RECORDATORIO_24H': """Hola {nombre_cliente} 👋

Te recordamos tu turno para mañana:

🕐 {hora} - {servicio}
👤 {profesional}
📍 {sucursal_nombre}

Si necesitas cancelar o reprogramar, contactanos.

¡Te esperamos!""",

            'RECORDATORIO_2H': """¡Tu turno es en 2 horas! ⏰

🕐 {hora} - {servicio}
📍 {sucursal_direccion}

¡Te esperamos!""",

            'CANCELACION': """Hola {nombre_cliente},

Tu turno del {fecha} a las {hora} ha sido cancelado.

Si deseas reprogramar, contactanos.

Saludos!"""
        }

        if tipo:
            # Resetear solo un tipo
            if tipo not in defaults:
                return Response(
                    {'error': f'Tipo {tipo} no válido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            template, created = MensajeTemplate.objects.update_or_create(
                sucursal=sucursal,
                tipo=tipo,
                defaults={
                    'mensaje': defaults[tipo],
                    'activo': True,
                    'actualizado_por': request.user
                }
            )

            return Response({
                'message': f'Template {tipo} restaurado',
                'template': MensajeTemplateSerializer(template).data
            })

        else:
            # Resetear todos los tipos
            templates_creados = []
            for tipo_key, mensaje_default in defaults.items():
                template, created = MensajeTemplate.objects.update_or_create(
                    sucursal=sucursal,
                    tipo=tipo_key,
                    defaults={
                        'mensaje': mensaje_default,
                        'activo': True,
                        'actualizado_por': request.user
                    }
                )
                templates_creados.append(template)

            return Response({
                'message': f'{len(templates_creados)} templates restaurados',
                'templates': MensajeTemplateListSerializer(templates_creados, many=True).data
            })

    @action(detail=False, methods=['get'])
    def variables_disponibles(self, request):
        """
        Listar variables disponibles para usar en templates

        GET /api/mensajes-templates/variables_disponibles/
        """
        variables = {
            'generales': [
                {'variable': '{nombre_cliente}', 'descripcion': 'Nombre del cliente'},
                {'variable': '{sucursal_nombre}', 'descripcion': 'Nombre de la sucursal'},
                {'variable': '{sucursal_direccion}', 'descripcion': 'Dirección de la sucursal'},
                {'variable': '{sucursal_telefono}', 'descripcion': 'Teléfono de la sucursal'},
            ],
            'turnos': [
                {'variable': '{fecha}', 'descripcion': 'Fecha del turno (ej: 25/12/2024)'},
                {'variable': '{hora}', 'descripcion': 'Hora del turno (ej: 14:30)'},
                {'variable': '{servicio}', 'descripcion': 'Nombre del servicio'},
                {'variable': '{profesional}', 'descripcion': 'Nombre del profesional'},
                {'variable': '{duracion}', 'descripcion': 'Duración del servicio'},
                {'variable': '{precio}', 'descripcion': 'Precio del servicio'},
            ]
        }

        return Response(variables)


logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def twilio_status_webhook(request):
    """
    Webhook para recibir actualizaciones de estado de mensajes de Twilio.

    Twilio envía POST con estos campos:
    - MessageSid: ID único del mensaje
    - MessageStatus: sent, delivered, read, failed, undelivered
    - ErrorCode: código de error (si falló)
    - ErrorMessage: descripción del error

    Configurar en Twilio Console:
    POST https://tu-dominio.com/api/notificaciones/webhook/status/
    """
    # Validar firma de Twilio (IMPORTANTE para producción)
    # La validación de firma requiere el paquete twilio y el token
    try:
        from twilio.request_validator import RequestValidator

        auth_token = settings.TWILIO_AUTH_TOKEN
        if auth_token:
            validator = RequestValidator(auth_token)

            # Obtener la URL completa y la firma
            request_url = request.build_absolute_uri()
            signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')

            # Validar
            if not validator.validate(request_url, request.data, signature):
                logger.warning("Twilio webhook: firma inválida")
                return Response(
                    {'error': 'Firma inválida'},
                    status=status.HTTP_403_FORBIDDEN
                )
    except ImportError:
        logger.warning("twilio package no instalado, omitiendo validación de firma")
    except Exception as e:
        logger.error(f"Error validando firma Twilio: {e}")

    # Extraer datos del webhook
    message_sid = request.data.get('MessageSid') or request.data.get('SmsSid')
    message_status = request.data.get('MessageStatus') or request.data.get('SmsStatus')
    error_code = request.data.get('ErrorCode')
    error_message = request.data.get('ErrorMessage')

    if not message_sid:
        return Response(
            {'error': 'MessageSid requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    logger.info(f"Twilio webhook: SID={message_sid}, Status={message_status}")

    # Buscar la notificación por el SID externo
    try:
        notificacion = Notificacion.objects.get(mensaje_id_externo=message_sid)
    except Notificacion.DoesNotExist:
        logger.warning(f"Notificación no encontrada para SID: {message_sid}")
        # Responder 200 para que Twilio no reintente
        return Response({'status': 'not_found'})

    # Mapear estados de Twilio a nuestros estados
    status_mapping = {
        'queued': 'PENDIENTE',
        'sending': 'PENDIENTE',
        'sent': 'ENVIADO',
        'delivered': 'ENTREGADO',
        'read': 'LEIDO',
        'failed': 'FALLIDO',
        'undelivered': 'FALLIDO',
    }

    nuevo_estado = status_mapping.get(message_status, notificacion.estado)

    # Actualizar estado y timestamps
    notificacion.estado = nuevo_estado

    if message_status == 'sent' and not notificacion.enviado_en:
        notificacion.enviado_en = timezone.now()
    elif message_status == 'delivered' and not notificacion.entregado_en:
        notificacion.entregado_en = timezone.now()
    elif message_status == 'read' and not notificacion.leido_en:
        notificacion.leido_en = timezone.now()
    elif message_status in ('failed', 'undelivered'):
        error_info = f"Code: {error_code}" if error_code else ""
        if error_message:
            error_info += f" - {error_message}"
        notificacion.error_mensaje = error_info or "Error de entrega"

    notificacion.save()

    logger.info(f"Notificación {notificacion.id} actualizada a estado: {nuevo_estado}")

    # Twilio espera respuesta 200 vacía o con TwiML
    return Response({'status': 'ok'})

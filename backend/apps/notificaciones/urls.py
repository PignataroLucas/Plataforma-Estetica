from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificacionViewSet, MensajeTemplateViewSet, twilio_status_webhook

router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')
router.register(r'mensajes-templates', MensajeTemplateViewSet, basename='mensajes-templates')

urlpatterns = [
    path('', include(router.urls)),
    # Webhook de Twilio para status callbacks (NO requiere autenticación)
    path('notificaciones/webhook/status/', twilio_status_webhook, name='twilio-status-webhook'),
]

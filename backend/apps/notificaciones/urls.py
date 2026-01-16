from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificacionViewSet, MensajeTemplateViewSet

router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')
router.register(r'mensajes-templates', MensajeTemplateViewSet, basename='mensajes-templates')

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, HistorialClienteViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'historial', HistorialClienteViewSet, basename='historial-cliente')

urlpatterns = [
    path('', include(router.urls)),
]

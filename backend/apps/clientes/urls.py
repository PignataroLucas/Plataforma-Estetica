from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClienteViewSet,
    HistorialClienteViewSet,
    PlanTratamientoViewSet,
    RutinaCuidadoViewSet,
    NotaClienteViewSet,
    SegmentoAppViewSet
)

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'historial', HistorialClienteViewSet, basename='historial-cliente')
router.register(r'planes-tratamiento', PlanTratamientoViewSet, basename='plan-tratamiento')
router.register(r'rutinas-cuidado', RutinaCuidadoViewSet, basename='rutina-cuidado')
router.register(r'notas-cliente', NotaClienteViewSet, basename='nota-cliente')
router.register(r'segmentos-app', SegmentoAppViewSet, basename='segmento-app')

urlpatterns = [
    path('', include(router.urls)),
]

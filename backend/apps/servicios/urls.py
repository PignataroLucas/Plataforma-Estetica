from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServicioViewSet, CategoriaServicioViewSet, MaquinaAlquiladaViewSet, AlquilerMaquinaViewSet

router = DefaultRouter()
router.register(r'servicios', ServicioViewSet, basename='servicio')
router.register(r'categorias', CategoriaServicioViewSet, basename='categoria-servicio')
router.register(r'maquinas', MaquinaAlquiladaViewSet, basename='maquina-alquilada')
router.register(r'alquileres', AlquilerMaquinaViewSet, basename='alquiler-maquina')

urlpatterns = [
    path('', include(router.urls)),
]

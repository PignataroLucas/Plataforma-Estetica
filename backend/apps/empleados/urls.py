from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
router.register(r'centros', views.CentroEsteticaViewSet, basename='centro')
router.register(r'sucursales', views.SucursalViewSet, basename='sucursal')

urlpatterns = [
    path('', include(router.urls)),
]

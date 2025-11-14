from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TurnoViewSet

router = DefaultRouter()
router.register(r'turnos', TurnoViewSet, basename='turno')

urlpatterns = [
    path('', include(router.urls)),
]

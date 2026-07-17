from django.urls import path

from .views import (
    CentroInfoView,
    ProductosPublicosView,
    ServiciosPublicosView,
)

urlpatterns = [
    path('centros/<int:centro_id>/info/', CentroInfoView.as_view(), name='public-centro-info'),
    path('centros/<int:centro_id>/servicios/', ServiciosPublicosView.as_view(), name='public-centro-servicios'),
    path('centros/<int:centro_id>/productos/', ProductosPublicosView.as_view(), name='public-centro-productos'),
]

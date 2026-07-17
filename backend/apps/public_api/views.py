from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from apps.empleados.models import CentroEstetica
from apps.inventario.models import Producto
from apps.servicios.models import Servicio

from .serializers import (
    CentroPublicoSerializer,
    ProductoPublicoSerializer,
    ServicioPublicoSerializer,
)


class PublicoBase:
    """Config común a todos los endpoints públicos: sin auth, con rate limit anónimo."""
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_api'

    def get_centro(self):
        return get_object_or_404(
            CentroEstetica, pk=self.kwargs['centro_id'], activo=True
        )


class CentroInfoView(PublicoBase, RetrieveAPIView):
    """GET /api/public/centros/<id>/info/"""
    serializer_class = CentroPublicoSerializer
    queryset = CentroEstetica.objects.filter(activo=True)
    lookup_url_kwarg = 'centro_id'


class ServiciosPublicosView(PublicoBase, ListAPIView):
    """GET /api/public/centros/<id>/servicios/ — servicios activos del centro."""
    serializer_class = ServicioPublicoSerializer

    def get_queryset(self):
        centro = self.get_centro()
        return (
            Servicio.objects
            .filter(sucursal__centro_estetica=centro, activo=True)
            .select_related('categoria', 'sucursal')
            .order_by('nombre')
        )


class ProductosPublicosView(PublicoBase, ListAPIView):
    """GET /api/public/centros/<id>/productos/ — solo productos de REVENTA activos."""
    serializer_class = ProductoPublicoSerializer

    def get_queryset(self):
        centro = self.get_centro()
        return (
            Producto.objects
            .filter(
                sucursal__centro_estetica=centro,
                tipo=Producto.TipoProducto.REVENTA,
                activo=True,
            )
            .select_related('categoria', 'sucursal')
            .order_by('nombre')
        )

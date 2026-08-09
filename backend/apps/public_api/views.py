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


def productos_del_catalogo(centro):
    """
    Los productos que la app puede mostrar de un centro.

    Vive suelto porque el listado y la ficha tienen que coincidir exactamente:
    si divergieran, un producto que no aparece en la grilla podría abrirse por
    id, que es la forma sutil de filtrar el catálogo interno.
    """
    return (
        Producto.objects
        .filter(
            sucursal__centro_estetica=centro,
            tipo=Producto.TipoProducto.REVENTA,
            activo=True,
        )
        .select_related('categoria', 'sucursal')
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


class ServicioPublicoDetalleView(PublicoBase, RetrieveAPIView):
    """
    GET /api/public/centros/<id>/servicios/<pk>/ — ficha de un tratamiento.

    Mismo scope que el listado: solo servicios activos del centro pedido, así un
    id de otro centro (o un servicio dado de baja) devuelve 404 en vez de filtrar.
    """
    serializer_class = ServicioPublicoSerializer

    def get_queryset(self):
        centro = self.get_centro()
        return (
            Servicio.objects
            .filter(sucursal__centro_estetica=centro, activo=True)
            .select_related('categoria', 'sucursal')
        )


class ProductosPublicosView(PublicoBase, ListAPIView):
    """GET /api/public/centros/<id>/productos/ — solo productos de REVENTA activos."""
    serializer_class = ProductoPublicoSerializer

    def get_queryset(self):
        return productos_del_catalogo(self.get_centro()).order_by('nombre')


class ProductoPublicoDetalleView(PublicoBase, RetrieveAPIView):
    """
    GET /api/public/centros/<id>/productos/<pk>/ — ficha de un producto.

    Mismo scope que el listado: solo productos de reventa activos del centro
    pedido, así un id de otro centro (o de un producto de uso interno) devuelve
    404 en vez de filtrar el catálogo interno.
    """
    serializer_class = ProductoPublicoSerializer

    def get_queryset(self):
        return productos_del_catalogo(self.get_centro())

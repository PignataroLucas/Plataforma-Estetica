"""
Endpoint de las ventas que vinieron de la app (COMPRA_EN_APP_SPEC.md §5.7).

Aparte de `views.py` a propósito: ese archivo ya pasa las mil líneas y esto es
un módulo con su propia pregunta.
"""
from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import ventas_app
from .permissions import IsAdminOrManager

VENTANA_POR_DEFECTO = timedelta(days=30)


class VentasDeLaAppView(APIView):
    """
    GET /api/analytics/dashboard/ventas-app/

    Cuánto vendió la app, qué productos, a qué clientas y con cuánto descuento.

    Query params:
    - start_date, end_date (por defecto, los últimos 30 días)
    - sucursal_id
    - limit: cuántos productos y clientas devolver (default 10)
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    # **Sin `cache_page`, a diferencia del resto del dashboard.** Ese decorador
    # cachea por URL y no por usuario, y acá el centro sale del usuario: la URL
    # es idéntica para todos, así que el primero en pedirla le dejaría sus
    # números cacheados al siguiente, fuera cual fuera su centro. Verificado con
    # los tests de este módulo, que se pisaban entre sí hasta que se sacó.
    #
    # Las consultas son agregados sobre columnas indexadas y el volumen es
    # chico. Si algún día hace falta cachear, la clave tiene que incluir el
    # centro.
    def get(self, request):
        centro = request.user.centro_estetica
        if centro is None:
            return Response({'detail': 'Tu usuario no tiene centro asignado.'},
                            status=400)

        try:
            desde, hasta = self._periodo(request)
        except ValueError:
            return Response(
                {'detail': 'Las fechas van en formato AAAA-MM-DD.'}, status=400
            )

        # El centro sale del usuario y la sucursal se valida contra él: un id de
        # otra sucursal es la línea entre los datos de dos inquilinos, no un
        # error de tipeo inocente.
        sucursal_id = request.query_params.get('sucursal_id')
        if sucursal_id:
            if not centro.sucursales.filter(pk=sucursal_id).exists():
                return Response(
                    {'detail': 'Esa sucursal no es de tu centro.'}, status=404
                )
            sucursal_id = int(sucursal_id)

        limite = min(int(request.query_params.get('limit', 10)), 50)

        return Response({
            'periodo': {'desde': desde.isoformat(), 'hasta': hasta.isoformat()},
            'resumen': ventas_app.resumen(centro, desde, hasta, sucursal_id),
            'productos': ventas_app.productos(
                centro, desde, hasta, sucursal_id, limite
            ),
            'clientas': ventas_app.clientas(
                centro, desde, hasta, sucursal_id, limite
            ),
            'cupones': ventas_app.cupones(centro, desde, hasta),
        })

    @staticmethod
    def _periodo(request):
        hasta = request.query_params.get('end_date')
        desde = request.query_params.get('start_date')

        hasta = (
            datetime.strptime(hasta, '%Y-%m-%d').date() if hasta
            else timezone.localdate()
        )
        desde = (
            datetime.strptime(desde, '%Y-%m-%d').date() if desde
            else hasta - VENTANA_POR_DEFECTO
        )
        return desde, hasta

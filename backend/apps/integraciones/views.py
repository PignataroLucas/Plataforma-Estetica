"""
API for configuring and monitoring the Conto integration.

Admin-only. Every queryset is scoped to the requesting user's center: the view
layer is where multi-tenancy is enforced in this project, and an integration is
exactly the kind of record where a leak would be expensive.
"""
import logging
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ContoIntegration, ContoSale
from .permissions import IsIntegrationAdmin
from .serializers import (
    ContoIntegrationCreateSerializer,
    ContoIntegrationSerializer,
    ContoSaleDetailSerializer,
    ContoSaleSerializer,
)
from .services import ContoClient, ContoError
from .sync import SalesImporter, StockSynchronizer

logger = logging.getLogger(__name__)

# The sales task runs every 15 minutes. Silence well past that means something
# is wrong, and a dead integration that fails quietly is the expensive case.
STALE_AFTER = timedelta(hours=2)


class ContoIntegrationViewSet(viewsets.ModelViewSet):
    """
    Endpoints:
    - GET    /api/integraciones/conto/                      Listar (0 o 1)
    - POST   /api/integraciones/conto/                      Crear
    - PATCH  /api/integraciones/conto/{id}/                 Editar
    - DELETE /api/integraciones/conto/{id}/                 Borrar
    - POST   /api/integraciones/conto/{id}/verificar/       Verificar vinculación
    - GET    /api/integraciones/conto/{id}/estado/          Estado y alertas
    - POST   /api/integraciones/conto/{id}/sincronizar/     Disparar sync manual
    """
    permission_classes = [IsAuthenticated, IsIntegrationAdmin]
    serializer_class = ContoIntegrationSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.centro_estetica_id:
            return ContoIntegration.objects.none()
        return ContoIntegration.objects.filter(
            center=user.centro_estetica
        ).select_related('center', 'branch')

    def get_serializer_class(self):
        if self.action == 'create':
            return ContoIntegrationCreateSerializer
        return ContoIntegrationSerializer

    def perform_create(self, serializer):
        """The tenant comes from the user, never from the payload."""
        serializer.save(center=self.request.user.centro_estetica)

    # -- linking ----------------------------------------------------------- #

    @action(detail=True, methods=['post'])
    def verificar(self, request, pk=None):
        """
        Ask Conto which account this token belongs to, and store the answer.

        The link is established from Conto's response, not from anything typed
        into the form. Everything downstream compares against what is stored
        here, so this is the only place it may be written.
        """
        integration = self.get_object()

        try:
            account = ContoClient(integration).get_account()
        except ContoError as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

        received_id = account.get('cuenta_id')
        if not received_id:
            return Response(
                {'success': False,
                 'error': "Conto no devolvió 'cuenta_id'. Revisá el contrato de la API."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Re-linking to a different account is the exact scenario the isolation
        # rules exist to prevent, so it needs an explicit confirmation.
        previous_id = integration.conto_account_id
        if previous_id and previous_id != received_id:
            if not request.data.get('confirmar_cambio_de_cuenta'):
                return Response(
                    {
                        'success': False,
                        'requiere_confirmacion': True,
                        'error': (
                            f"Esta integración está vinculada a la cuenta "
                            f"{previous_id!r} y el token actual resuelve a "
                            f"{received_id!r}. Cambiar de cuenta puede mezclar "
                            f"datos de dos negocios distintos."
                        ),
                        'cuenta_actual': previous_id,
                        'cuenta_nueva': received_id,
                    },
                    status=status.HTTP_409_CONFLICT
                )
            logger.warning(
                "Integración %s recambiada de la cuenta %s a %s",
                integration.pk, previous_id, received_id,
            )

        integration.conto_account_id = received_id
        integration.conto_account_name = account.get('nombre') or ''
        integration.link_verified_at = timezone.now()
        integration.save(update_fields=[
            'conto_account_id', 'conto_account_name', 'link_verified_at', 'updated_at'
        ])

        return Response({
            'success': True,
            'cuenta_id': received_id,
            'cuenta_nombre': integration.conto_account_name,
            'cuenta_activa': account.get('activa', True),
            'mensaje': (
                f"Vinculado a: {integration.conto_account_name or received_id}. "
                f"Confirmá que sea la cuenta correcta antes de activar."
            ),
        })

    # -- monitoring -------------------------------------------------------- #

    @action(detail=True, methods=['get'])
    def estado(self, request, pk=None):
        """
        Health of the integration, with the alerts that must not stay silent.
        """
        integration = self.get_object()

        counts = dict(
            ContoSale.objects
            .filter(integration=integration)
            .values_list('status')
            .annotate(total=Count('id'))
        )

        failed = ContoSale.objects.filter(
            integration=integration, status=ContoSale.Status.ERROR
        ).order_by('-updated_at')[:10]

        return Response({
            'integracion': ContoIntegrationSerializer(
                integration, context={'request': request}
            ).data,
            'vouchers': {
                'procesados': counts.get(ContoSale.Status.PROCESSED, 0),
                'pendientes': counts.get(ContoSale.Status.PENDING, 0),
                'omitidos': counts.get(ContoSale.Status.SKIPPED, 0),
                'con_error': counts.get(ContoSale.Status.ERROR, 0),
            },
            'ultimos_errores': ContoSaleSerializer(failed, many=True).data,
            'alertas': self._build_alerts(integration, counts),
        })

    def _build_alerts(self, integration, counts):
        """
        Anything that would otherwise make the integration fail quietly.

        Ordered by severity so the UI can show the first one prominently.
        """
        alerts = []

        if not integration.is_linked:
            alerts.append({
                'nivel': 'error',
                'codigo': 'SIN_VINCULAR',
                'mensaje': 'La vinculación con Conto no fue verificada.',
            })

        if not integration.is_active:
            alerts.append({
                'nivel': 'aviso',
                'codigo': 'INACTIVA',
                'mensaje': 'La integración está desactivada: no sincroniza.',
            })

        if not integration.import_from and not integration.last_sales_sync:
            alerts.append({
                'nivel': 'error',
                'codigo': 'SIN_FECHA_DE_INICIO',
                'mensaje': (
                    'Falta definir desde qué fecha importar ventas. '
                    'Sin eso la primera sincronización no corre.'
                ),
            })

        errors = counts.get(ContoSale.Status.ERROR, 0)
        if errors:
            alerts.append({
                'nivel': 'error',
                'codigo': 'VOUCHERS_CON_ERROR',
                'mensaje': (
                    f'{errors} venta(s) no se pudieron importar. '
                    f'Revisalas y reprocesalas.'
                ),
            })

        # Imported, but our breakdown does not add up to what Conto says the
        # customer paid. The money is recorded; how it was split is suspect.
        descuadres = ContoSale.objects.filter(
            integration=integration, total_discrepancy__isnull=False
        ).count()
        if descuadres:
            alerts.append({
                'nivel': 'error',
                'codigo': 'VOUCHERS_CON_DESCUADRE',
                'mensaje': (
                    f'{descuadres} venta(s) se importaron con un monto que no '
                    f'coincide con el total informado por Conto. El ingreso está '
                    f'registrado, pero el desglose puede estar mal.'
                ),
            })

        if integration.can_sync:
            if not integration.last_sales_sync:
                alerts.append({
                    'nivel': 'aviso',
                    'codigo': 'NUNCA_SINCRONIZADA',
                    'mensaje': 'Todavía no se importó ninguna venta.',
                })
            elif timezone.now() - integration.last_sales_sync > STALE_AFTER:
                hours = int(
                    (timezone.now() - integration.last_sales_sync).total_seconds() // 3600
                )
                alerts.append({
                    'nivel': 'error',
                    'codigo': 'SINCRONIZACION_DETENIDA',
                    'mensaje': (
                        f'Hace {hours} h que no se importan ventas, y debería '
                        f'pasar cada 15 minutos. Puede que el token haya sido '
                        f'revocado o que Conto no responda.'
                    ),
                })

        return alerts

    # -- manual trigger ---------------------------------------------------- #

    @action(detail=True, methods=['post'])
    def sincronizar(self, request, pk=None):
        """
        Run a sync now instead of waiting for the schedule.

        Runs inline rather than dispatching to a queue. There is no Celery
        worker deployed, and adding one just for this would mean a worker, a
        beat process and a broker for what amounts to a handful of HTTP calls.
        Running inline also lets the response carry the actual result instead of
        making the UI poll.

        If a first import ever grows large enough to hit the request timeout,
        use the `sincronizar_conto` management command for the initial load.
        """
        integration = self.get_object()

        if not integration.can_sync:
            return Response(
                {'success': False,
                 'error': 'La integración tiene que estar vinculada y activa'},
                status=status.HTTP_400_BAD_REQUEST
            )

        what = request.data.get('que', 'ventas')
        if what not in ('ventas', 'stock', 'todo'):
            return Response(
                {'success': False, 'error': "Usá 'ventas', 'stock' o 'todo'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        resultados = {}
        try:
            if what in ('stock', 'todo'):
                resultados['stock'] = StockSynchronizer(integration).run().summary
            if what in ('ventas', 'todo'):
                resultados['ventas'] = SalesImporter(integration).run().summary
        except ContoError as exc:
            return Response(
                {'success': False, 'error': str(exc), 'resultados': resultados},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'success': True, 'resultados': resultados})


class ContoSaleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoints:
    - GET  /api/integraciones/conto-ventas/                   Listar vouchers
    - GET  /api/integraciones/conto-ventas/{id}/              Detalle con payload
    - POST /api/integraciones/conto-ventas/{id}/reprocesar/   Reprocesar
    """
    permission_classes = [IsAuthenticated, IsIntegrationAdmin]
    serializer_class = ContoSaleSerializer
    # DjangoFilterBackend is not in the project defaults, so it goes here.
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'type', 'channel']
    search_fields = ['voucher_id', 'external_order_id']
    ordering_fields = ['date', 'created_at', 'updated_at']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.centro_estetica_id:
            return ContoSale.objects.none()
        return ContoSale.objects.filter(
            integration__center=user.centro_estetica
        ).select_related('integration').prefetch_related('transactions')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ContoSaleDetailSerializer
        return ContoSaleSerializer

    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        """
        Re-run this voucher from its stored payload, without querying Conto.

        For use after fixing whatever made it fail — creating the missing
        product, correcting a SKU. Idempotent: a voucher already processed is
        left alone.
        """
        sale = self.get_object()

        if sale.status == ContoSale.Status.PROCESSED:
            return Response({
                'success': True,
                'mensaje': 'El voucher ya estaba procesado, no se hizo nada.',
                'venta': ContoSaleSerializer(sale).data,
            })

        importer = SalesImporter(sale.integration)
        result = importer.reprocess(sale)
        sale.refresh_from_db()

        return Response({
            'success': not result.errors,
            'resultado': result.summary,
            'errores': result.errors,
            'venta': ContoSaleSerializer(sale).data,
        })

"""
URL routing for the integrations module.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .tiendanube_views import (
    CustomersDataRequestView,
    CustomersRedactView,
    OAuthCallbackView,
    StoreRedactView,
)
from .views import ContoIntegrationViewSet, ContoSaleViewSet

router = DefaultRouter()
router.register(r'conto', ContoIntegrationViewSet, basename='conto-integration')
router.register(r'conto-ventas', ContoSaleViewSet, basename='conto-sale')

urlpatterns = [
    # Tienda Nube va antes del router: son rutas fijas y públicas, y no tienen
    # que competir con el prefijo de ningún viewset.
    # Esta es la URL que hay que cargar como «URL de redirección» en el panel
    # de partners. Cambiarla rompe la instalación.
    path('tiendanube/oauth/callback/',
         OAuthCallbackView.as_view(), name='tiendanube-oauth-callback'),

    path('tiendanube/webhooks/store-redact/',
         StoreRedactView.as_view(), name='tiendanube-webhook-store-redact'),
    path('tiendanube/webhooks/customers-redact/',
         CustomersRedactView.as_view(), name='tiendanube-webhook-customers-redact'),
    path('tiendanube/webhooks/customers-data-request/',
         CustomersDataRequestView.as_view(), name='tiendanube-webhook-customers-data-request'),

    path('', include(router.urls)),
]

"""
Available API Endpoints (todos requieren rol ADMIN):

Integración:
- GET    /api/integraciones/conto/                       - Listar (0 o 1 por centro)
- POST   /api/integraciones/conto/                       - Crear
- GET    /api/integraciones/conto/{id}/                  - Detalle
- PATCH  /api/integraciones/conto/{id}/                  - Editar
- DELETE /api/integraciones/conto/{id}/                  - Borrar
- POST   /api/integraciones/conto/{id}/verificar/        - Verificar vinculación
- GET    /api/integraciones/conto/{id}/estado/           - Estado, contadores y alertas
- POST   /api/integraciones/conto/{id}/sincronizar/      - Disparar sync ('ventas'|'stock'|'todo')

Vouchers importados:
- GET    /api/integraciones/conto-ventas/                - Listar
- GET    /api/integraciones/conto-ventas/{id}/           - Detalle con payload crudo
- POST   /api/integraciones/conto-ventas/{id}/reprocesar/ - Reprocesar desde el payload

Filtros: ?status=ERROR&type=SALE&channel=tiendanube
Búsqueda: ?search=TN-12345

Tienda Nube (públicos: los abre el navegador del comerciante o Tienda Nube):
- GET    /api/integraciones/tiendanube/oauth/callback/   - Vuelta de Tienda Nube con el code
- POST   /api/integraciones/tiendanube/webhooks/store-redact/
- POST   /api/integraciones/tiendanube/webhooks/customers-redact/
- POST   /api/integraciones/tiendanube/webhooks/customers-data-request/

Los tres webhooks validan HMAC-SHA256 del cuerpo crudo contra el client_secret.
"""

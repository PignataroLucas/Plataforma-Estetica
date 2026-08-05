"""
URL routing for the integrations module.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContoIntegrationViewSet, ContoSaleViewSet

router = DefaultRouter()
router.register(r'conto', ContoIntegrationViewSet, basename='conto-integration')
router.register(r'conto-ventas', ContoSaleViewSet, basename='conto-sale')

urlpatterns = [
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
"""

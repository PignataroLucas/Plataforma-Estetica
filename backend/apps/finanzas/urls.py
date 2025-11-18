"""
URL routing for Financial module API endpoints
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionCategoryViewSet,
    TransactionViewSet,
    AccountReceivableViewSet
)

# Create router and register viewsets
router = DefaultRouter()

# Register viewsets with their base names
router.register(
    r'categories',
    TransactionCategoryViewSet,
    basename='transaction-category'
)
router.register(
    r'transactions',
    TransactionViewSet,
    basename='transaction'
)
router.register(
    r'accounts-receivable',
    AccountReceivableViewSet,
    basename='account-receivable'
)

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

"""
Available API Endpoints:

Transaction Categories:
- GET    /api/finanzas/categories/                      - List all categories
- POST   /api/finanzas/categories/                      - Create new category
- GET    /api/finanzas/categories/{id}/                 - Get category details
- PUT    /api/finanzas/categories/{id}/                 - Update category (full)
- PATCH  /api/finanzas/categories/{id}/                 - Update category (partial)
- DELETE /api/finanzas/categories/{id}/                 - Delete category
- GET    /api/finanzas/categories/tree/                 - Get hierarchical tree view
- GET    /api/finanzas/categories/by_type/              - Get categories grouped by type

Transactions:
- GET    /api/finanzas/transactions/                    - List all transactions
- POST   /api/finanzas/transactions/                    - Create new transaction
- GET    /api/finanzas/transactions/{id}/               - Get transaction details
- PUT    /api/finanzas/transactions/{id}/               - Update transaction (full)
- PATCH  /api/finanzas/transactions/{id}/               - Update transaction (partial)
- DELETE /api/finanzas/transactions/{id}/               - Delete transaction
- GET    /api/finanzas/transactions/summary/            - Get financial summary
- GET    /api/finanzas/transactions/by_category/        - Breakdown by category
- GET    /api/finanzas/transactions/by_payment_method/  - Breakdown by payment method
- GET    /api/finanzas/transactions/recent/             - Get last 10 transactions

Accounts Receivable:
- GET    /api/finanzas/accounts-receivable/             - List all accounts receivable
- POST   /api/finanzas/accounts-receivable/             - Create new account
- GET    /api/finanzas/accounts-receivable/{id}/        - Get account details
- PUT    /api/finanzas/accounts-receivable/{id}/        - Update account (full)
- PATCH  /api/finanzas/accounts-receivable/{id}/        - Update account (partial)
- DELETE /api/finanzas/accounts-receivable/{id}/        - Delete account
- GET    /api/finanzas/accounts-receivable/overdue/     - Get overdue accounts
- GET    /api/finanzas/accounts-receivable/summary/     - Get summary statistics

Query Parameters (common across endpoints):
- Filtering: Use filterset fields (e.g., ?date_from=2024-01-01&date_to=2024-12-31)
- Ordering: ?ordering=date or ?ordering=-amount
- Search: ?search=keyword
- Pagination: ?page=1&page_size=20

Examples:
- GET /api/finanzas/transactions/?date_from=2024-01-01&date_to=2024-12-31&is_income=true
- GET /api/finanzas/categories/?type=EXPENSE&is_active=true
- GET /api/finanzas/accounts-receivable/?is_overdue=true&client_id=5
"""

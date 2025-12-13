"""
URLs para el módulo de Analytics
"""

from django.urls import path
from .views import (
    # Dashboard Global
    DashboardSummaryView,
    RevenueAnalyticsView,
    ServiceAnalyticsView,
    ProductAnalyticsView,
    EmployeePerformanceView,
    ClientAnalyticsView,
    OccupancyAnalyticsView,
    NoShowAnalyticsView,

    # Cliente Individual
    ClientSummaryView,
    ClientSpendingView,
    ClientPatternsView,
    ClientAlertsView,
)

urlpatterns = [
    # ========== ANALYTICS GLOBAL - DASHBOARD ==========
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('dashboard/revenue/', RevenueAnalyticsView.as_view(), name='dashboard-revenue'),
    path('dashboard/services/', ServiceAnalyticsView.as_view(), name='dashboard-services'),
    path('dashboard/products/', ProductAnalyticsView.as_view(), name='dashboard-products'),
    path('dashboard/employees/', EmployeePerformanceView.as_view(), name='dashboard-employees'),
    path('dashboard/clients/', ClientAnalyticsView.as_view(), name='dashboard-clients'),
    path('dashboard/ocupacion/', OccupancyAnalyticsView.as_view(), name='dashboard-ocupacion'),
    path('dashboard/no-shows/', NoShowAnalyticsView.as_view(), name='dashboard-no-shows'),

    # ========== ANALYTICS DE CLIENTE INDIVIDUAL ==========
    path('client/<int:cliente_id>/summary/', ClientSummaryView.as_view(), name='client-summary'),
    path('client/<int:cliente_id>/spending/', ClientSpendingView.as_view(), name='client-spending'),
    path('client/<int:cliente_id>/patterns/', ClientPatternsView.as_view(), name='client-patterns'),
    path('client/<int:cliente_id>/alerts/', ClientAlertsView.as_view(), name='client-alerts'),
]

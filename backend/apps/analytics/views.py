"""
Views para Analytics
Endpoints para dashboard global y analytics de cliente individual
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .utils import AnalyticsCalculator
from .permissions import IsAdminOrManager, CanViewClientAnalytics


# ========== ANALYTICS GLOBAL - DASHBOARD ==========

class DashboardSummaryView(APIView):
    """
    GET /api/analytics/dashboard/summary/

    Resumen general del dashboard con KPIs principales
    Query params:
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - sucursal_id: (opcional)
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 5))  # Cache 5 minutos
    def get(self, request):
        # Obtener parámetros
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        sucursal_id = request.query_params.get('sucursal_id')

        # Validar y parsear fechas
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            # Default: últimos 30 días
            start_date = end_date - timedelta(days=30)

        # Convertir sucursal_id a int si existe
        if sucursal_id:
            try:
                sucursal_id = int(sucursal_id)
            except ValueError:
                sucursal_id = None

        # Calcular summary
        summary = AnalyticsCalculator.get_dashboard_summary(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date
        )

        return Response(summary)


class RevenueAnalyticsView(APIView):
    """
    GET /api/analytics/dashboard/revenue/

    Analytics de ingresos: evolución, comparativas, métodos de pago
    Query params:
    - start_date, end_date, sucursal_id
    - granularity: day | week | month (default: day)
    - compare: true | false (incluir período anterior)
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 5))
    def get(self, request):
        # Parsear parámetros
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        sucursal_id = request.query_params.get('sucursal_id')
        granularity = request.query_params.get('granularity', 'day')
        compare = request.query_params.get('compare', 'false').lower() == 'true'

        # Validar fechas
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        if sucursal_id:
            sucursal_id = int(sucursal_id)

        # Obtener evolución
        evolution = AnalyticsCalculator.get_revenue_evolution(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )

        # Obtener distribución por método de pago
        by_payment_method = AnalyticsCalculator.get_revenue_by_payment_method(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date
        )

        response_data = {
            'evolution': evolution,
            'by_payment_method': by_payment_method
        }

        # Si se requiere comparación, calcular período anterior
        if compare:
            period_duration = (end_date - start_date).days
            previous_start = start_date - timedelta(days=period_duration)
            previous_end = start_date - timedelta(days=1)

            current_total = sum(item['total_revenue'] for item in evolution)

            previous_evolution = AnalyticsCalculator.get_revenue_evolution(
                sucursal_id=sucursal_id,
                start_date=previous_start,
                end_date=previous_end,
                granularity=granularity
            )
            previous_total = sum(item['total_revenue'] for item in previous_evolution)

            response_data['comparison'] = {
                'current': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'total': current_total
                },
                'previous': {
                    'start': previous_start.isoformat(),
                    'end': previous_end.isoformat(),
                    'total': previous_total
                },
                'change': round(((current_total - previous_total) / previous_total * 100), 2) if previous_total > 0 else 0
            }

        return Response(response_data)


class ServiceAnalyticsView(APIView):
    """
    GET /api/analytics/dashboard/services/

    Analytics de servicios: top servicios, rentabilidad
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 10))
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        sucursal_id = request.query_params.get('sucursal_id')
        limit = int(request.query_params.get('limit', 10))
        granularity = request.query_params.get('granularity', 'day')

        # Parsear fechas
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        if sucursal_id:
            sucursal_id = int(sucursal_id)

        # Obtener top servicios
        top_services = AnalyticsCalculator.get_top_services(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        # Obtener rentabilidad
        profitability = AnalyticsCalculator.get_service_profitability(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date
        )

        # Obtener evolución de servicios
        evolution = AnalyticsCalculator.get_service_evolution(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )

        return Response({
            'top_services': top_services,
            'profitability': profitability,
            'evolution': evolution
        })


class ProductAnalyticsView(APIView):
    """
    GET /api/analytics/dashboard/products/

    Analytics de productos: top productos
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 10))
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        sucursal_id = request.query_params.get('sucursal_id')
        limit = int(request.query_params.get('limit', 10))

        # Parsear fechas
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        if sucursal_id:
            sucursal_id = int(sucursal_id)

        # Obtener top productos
        top_products = AnalyticsCalculator.get_top_products(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        # Obtener rotación de inventario
        days = int(request.query_params.get('rotation_days', 90))
        inventory_rotation = AnalyticsCalculator.get_inventory_rotation(
            sucursal_id=sucursal_id,
            days=days
        )

        return Response({
            'top_products': top_products,
            'inventory_rotation': inventory_rotation
        })


class EmployeePerformanceView(APIView):
    """
    GET /api/analytics/dashboard/employees/

    Performance de empleados
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 10))
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        sucursal_id = request.query_params.get('sucursal_id')

        # Parsear fechas
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        if sucursal_id:
            sucursal_id = int(sucursal_id)

        group_by = request.query_params.get('group_by', 'weekday')

        # Obtener performance
        performance = AnalyticsCalculator.get_employee_performance(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date
        )

        # Obtener distribución de carga de trabajo
        workload_distribution = AnalyticsCalculator.get_workload_distribution(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )

        return Response({
            'employee_performance': performance,
            'workload_distribution': workload_distribution
        })


class ClientAnalyticsView(APIView):
    """
    GET /api/analytics/dashboard/clients/

    Analytics de clientes: segmentación, top clientes
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        sucursal_id = request.query_params.get('sucursal_id')

        if sucursal_id:
            sucursal_id = int(sucursal_id)

        limit = int(request.query_params.get('limit', 20))

        # Obtener segmentación
        segmentation = AnalyticsCalculator.get_client_segmentation(
            sucursal_id=sucursal_id
        )

        # Obtener top clientes
        top_clients = AnalyticsCalculator.get_top_clients(
            sucursal_id=sucursal_id,
            limit=limit
        )

        # Obtener distribución de LTV
        ltv_distribution = AnalyticsCalculator.get_ltv_distribution(
            sucursal_id=sucursal_id
        )

        return Response({
            'segmentation': segmentation,
            'top_clients': top_clients,
            'ltv_distribution': ltv_distribution
        })


class OccupancyAnalyticsView(APIView):
    """
    GET /api/analytics/dashboard/ocupacion/

    Analytics de ocupación: por día de semana, horarios
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 10))
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        sucursal_id = request.query_params.get('sucursal_id')

        # Parsear fechas
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        if sucursal_id:
            sucursal_id = int(sucursal_id)

        # Obtener ocupación por día de semana
        by_weekday = AnalyticsCalculator.get_occupancy_by_day_of_week(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date
        )

        # Obtener heatmap de ocupación
        heatmap = AnalyticsCalculator.get_occupancy_heatmap(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date
        )

        return Response({
            'by_weekday': by_weekday,
            'heatmap': heatmap
        })


class SeasonalTrendsView(APIView):
    """
    GET /api/analytics/dashboard/seasonal-trends/

    Tendencias estacionales por mes y trimestre
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        sucursal_id = request.query_params.get('sucursal_id')
        year = request.query_params.get('year')

        if sucursal_id:
            sucursal_id = int(sucursal_id)

        if year:
            year = int(year)

        trends = AnalyticsCalculator.get_seasonal_trends(
            sucursal_id=sucursal_id,
            year=year
        )

        return Response(trends)


class NoShowAnalyticsView(APIView):
    """
    GET /api/analytics/dashboard/no-shows/

    Analytics de no-shows y cancelaciones
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @method_decorator(cache_page(60 * 10))
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        sucursal_id = request.query_params.get('sucursal_id')

        # Parsear fechas
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        if sucursal_id:
            sucursal_id = int(sucursal_id)

        # Obtener stats
        stats = AnalyticsCalculator.get_no_show_stats(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date
        )

        return Response(stats)


# ========== ANALYTICS DE CLIENTE INDIVIDUAL ==========

class ClientSummaryView(APIView):
    """
    GET /api/analytics/client/<cliente_id>/summary/

    Resumen general del cliente
    """
    permission_classes = [IsAuthenticated, CanViewClientAnalytics]

    def get(self, request, cliente_id):
        from apps.clientes.models import Cliente
        from apps.turnos.models import Turno

        # Obtener cliente
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calcular métricas
        ltv = AnalyticsCalculator.get_client_lifetime_value(cliente_id)
        frequency = AnalyticsCalculator.get_client_frequency(cliente_id)
        client_status = AnalyticsCalculator.get_client_status(cliente_id)

        # Obtener primera y última visita
        first_visit = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).order_by('fecha_hora_inicio').first()

        last_visit = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).order_by('-fecha_hora_inicio').first()

        # Total de visitas
        total_visits = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).count()

        # Días desde última visita
        days_since_last = None
        if last_visit:
            days_since_last = (timezone.now().date() - last_visit.fecha_hora_inicio.date()).days

        # Ticket promedio
        avg_ticket = ltv / total_visits if total_visits > 0 else 0

        # Color según estado
        status_colors = {
            'VIP': 'green',
            'ACTIVE': 'blue',
            'AT_RISK': 'yellow',
            'INACTIVE': 'gray'
        }

        summary = {
            'client_info': {
                'id': cliente.id,
                'name': f"{cliente.nombre} {cliente.apellido}",
                'email': cliente.email,
                'phone': cliente.telefono
            },
            'summary': {
                'lifetime_value': ltv,
                'total_visits': total_visits,
                'first_visit': first_visit.fecha_hora_inicio.date().isoformat() if first_visit else None,
                'last_visit': last_visit.fecha_hora_inicio.date().isoformat() if last_visit else None,
                'days_since_last_visit': days_since_last,
                'average_frequency_days': frequency,
                'average_ticket': round(avg_ticket, 2),
                'status': client_status,
                'status_color': status_colors.get(client_status, 'gray')
            }
        }

        return Response(summary)


class ClientSpendingView(APIView):
    """
    GET /api/analytics/client/<cliente_id>/spending/

    Analytics de gasto del cliente
    """
    permission_classes = [IsAuthenticated, CanViewClientAnalytics]

    def get(self, request, cliente_id):
        from apps.finanzas.models import Transaction
        from django.db.models.functions import TruncMonth

        # Gasto mensual últimos 12 meses
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)

        monthly_spending = Transaction.objects.filter(
            client_id=cliente_id,
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT'],
            date__gte=start_date,
            date__lte=end_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            amount=Sum('amount'),
            visits=Count('id')
        ).order_by('month')

        # Formatear resultados
        monthly_data = []
        for item in monthly_spending:
            monthly_data.append({
                'month': item['month'].strftime('%Y-%m'),
                'amount': float(item['amount']),
                'visits': item['visits']
            })

        # Calcular promedio mensual
        total_amount = sum(item['amount'] for item in monthly_data)
        average_monthly = total_amount / len(monthly_data) if monthly_data else 0

        # Distribución servicios vs productos
        distribution = Transaction.objects.filter(
            client_id=cliente_id,
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT']
        ).values('type').annotate(
            amount=Sum('amount')
        )

        services_amount = 0
        products_amount = 0
        for item in distribution:
            if item['type'] == 'INCOME_SERVICE':
                services_amount = float(item['amount'])
            elif item['type'] == 'INCOME_PRODUCT':
                products_amount = float(item['amount'])

        total_distribution = services_amount + products_amount
        spending_distribution = {
            'services': {
                'amount': services_amount,
                'percentage': round((services_amount / total_distribution * 100), 2) if total_distribution > 0 else 0
            },
            'products': {
                'amount': products_amount,
                'percentage': round((products_amount / total_distribution * 100), 2) if total_distribution > 0 else 0
            }
        }

        return Response({
            'monthly_spending_12m': monthly_data,
            'average_monthly': round(average_monthly, 2),
            'spending_distribution': spending_distribution
        })


class ClientPatternsView(APIView):
    """
    GET /api/analytics/client/<cliente_id>/patterns/

    Patrones de comportamiento del cliente
    """
    permission_classes = [IsAuthenticated, CanViewClientAnalytics]

    def get(self, request, cliente_id):
        from apps.turnos.models import Turno
        from django.db.models.functions import ExtractWeekDay, ExtractHour
        from django.db.models import Count

        # Días preferidos
        preferred_days = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).annotate(
            weekday=ExtractWeekDay('fecha_hora_inicio')
        ).values('weekday').annotate(
            count=Count('id')
        )

        days_map = {
            1: 'Sunday',
            2: 'Monday',
            3: 'Tuesday',
            4: 'Wednesday',
            5: 'Thursday',
            6: 'Friday',
            7: 'Saturday'
        }

        preferred_days_data = {day: 0 for day in days_map.values()}
        for item in preferred_days:
            day_name = days_map.get(item['weekday'], 'Unknown')
            preferred_days_data[day_name] = item['count']

        # Horarios preferidos (franjas)
        turnos_with_hour = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).annotate(
            hour=ExtractHour('fecha_hora_inicio')
        ).values_list('hour', flat=True)

        time_slots = {'morning': 0, 'afternoon': 0, 'evening': 0}
        for hour in turnos_with_hour:
            if hour is not None:
                if 9 <= hour < 13:
                    time_slots['morning'] += 1
                elif 13 <= hour < 18:
                    time_slots['afternoon'] += 1
                elif 18 <= hour < 21:
                    time_slots['evening'] += 1

        return Response({
            'preferred_days': preferred_days_data,
            'preferred_time_slots': time_slots
        })


class ClientAlertsView(APIView):
    """
    GET /api/analytics/client/<cliente_id>/alerts/

    Alertas e insights automáticos del cliente
    """
    permission_classes = [IsAuthenticated, CanViewClientAnalytics]

    def get(self, request, cliente_id):
        from apps.turnos.models import Turno
        from apps.clientes.models import Cliente

        # Obtener datos del cliente
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        ltv = AnalyticsCalculator.get_client_lifetime_value(cliente_id)
        frequency = AnalyticsCalculator.get_client_frequency(cliente_id)
        client_status = AnalyticsCalculator.get_client_status(cliente_id)

        # Última visita
        last_visit = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).order_by('-fecha_hora_inicio').first()

        days_since_last = None
        if last_visit:
            days_since_last = (timezone.now().date() - last_visit.fecha_hora_inicio.date()).days

        alerts = []
        insights = []
        recommendations = []

        # ALERTAS DE RIESGO
        if client_status == 'AT_RISK' and frequency and days_since_last:
            alerts.append({
                'type': 'risk',
                'severity': 'high',
                'icon': '🚨',
                'title': 'Cliente en riesgo',
                'message': f'Sin visita hace {days_since_last} días (su promedio es {frequency} días)',
                'action': 'send_reminder'
            })

        if client_status == 'INACTIVE':
            alerts.append({
                'type': 'risk',
                'severity': 'high',
                'icon': '🚨',
                'title': 'Cliente inactivo',
                'message': f'Sin visita hace {days_since_last} días',
                'action': 'send_reengagement'
            })

        # ALERTAS DE OPORTUNIDAD
        if client_status == 'VIP':
            alerts.append({
                'type': 'opportunity',
                'severity': 'medium',
                'icon': '💚',
                'title': 'Cliente VIP',
                'message': 'En top 20% de gasto total',
                'action': 'vip_treatment'
            })

        # INSIGHTS
        if frequency:
            insights.append({
                'icon': '💡',
                'message': f'Frecuencia promedio: cada {frequency} días'
            })

        # RECOMENDACIONES
        if days_since_last and frequency and days_since_last >= frequency:
            recommendations.append({
                'icon': '✅',
                'message': f'Enviar recordatorio - Hace {days_since_last} días de su última visita',
                'action': 'send_whatsapp'
            })

        return Response({
            'alerts': alerts,
            'insights': insights,
            'recommendations': recommendations
        })


class ClientProductsView(APIView):
    """
    GET /api/analytics/client/<cliente_id>/products/

    Historial de productos comprados por el cliente
    """
    permission_classes = [IsAuthenticated, CanViewClientAnalytics]

    def get(self, request, cliente_id):
        from apps.finanzas.models import Transaction
        from apps.inventario.models import Producto

        # Verificar que el cliente existe
        from apps.clientes.models import Cliente
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=404)

        # Obtener transacciones de productos del cliente
        product_transactions = Transaction.objects.filter(
            client_id=cliente_id,
            type='INCOME_PRODUCT',
            product__isnull=False
        ).select_related('product').order_by('-date')

        # Si no hay compras de productos
        if not product_transactions.exists():
            return Response({
                'has_purchases': False,
                'message': 'Este cliente aún no ha comprado productos',
                'top_products': [],
                'recent_purchases': [],
                'total_spent': 0,
                'total_products': 0
            })

        # Top productos más comprados (por cantidad de transacciones)
        top_products_data = Transaction.objects.filter(
            client_id=cliente_id,
            type='INCOME_PRODUCT',
            product__isnull=False
        ).values(
            'product_id',
            'product__nombre'
        ).annotate(
            quantity=Count('id'),
            total_spent=Sum('amount')
        ).order_by('-quantity')[:5]

        top_products = []
        for item in top_products_data:
            top_products.append({
                'product_id': item['product_id'],
                'product_name': item['product__nombre'],
                'quantity': item['quantity'],
                'total_spent': float(item['total_spent'])
            })

        # Historial reciente (últimas 10 compras)
        recent_purchases = []
        for transaction in product_transactions[:10]:
            recent_purchases.append({
                'date': transaction.date.isoformat(),
                'product_id': transaction.product.id,
                'product_name': transaction.product.nombre,
                'amount': float(transaction.amount),
                'payment_method': transaction.payment_method
            })

        # Total gastado en productos
        total_spent = product_transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Total de compras de productos
        total_products = product_transactions.count()

        return Response({
            'has_purchases': True,
            'top_products': top_products,
            'recent_purchases': recent_purchases,
            'total_spent': float(total_spent),
            'total_products': total_products
        })

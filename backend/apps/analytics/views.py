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
from dateutil.relativedelta import relativedelta
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

        # Desglose mensual de servicios vs productos (últimos 12 meses)
        # Reutilizar las mismas fechas de monthly_spending_12m
        monthly_by_type = Transaction.objects.filter(
            client_id=cliente_id,
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT'],
            date__gte=start_date,
            date__lte=end_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month', 'type').annotate(
            amount=Sum('amount')
        ).order_by('month')

        # Crear diccionario para acceso rápido
        monthly_dict = {}
        for item in monthly_by_type:
            month_key = item['month'].strftime('%Y-%m')
            if month_key not in monthly_dict:
                monthly_dict[month_key] = {'services': 0, 'products': 0}

            if item['type'] == 'INCOME_SERVICE':
                monthly_dict[month_key]['services'] = float(item['amount'])
            elif item['type'] == 'INCOME_PRODUCT':
                monthly_dict[month_key]['products'] = float(item['amount'])

        # Generar array con todos los meses
        products_vs_services_monthly = []
        current_date = start_date.replace(day=1)

        for _ in range(12):
            month_key = current_date.strftime('%Y-%m')
            month_data = monthly_dict.get(month_key, {'services': 0, 'products': 0})

            total_month = month_data['services'] + month_data['products']

            products_vs_services_monthly.append({
                'month': month_key,
                'month_name': current_date.strftime('%b %Y'),
                'services': month_data['services'],
                'products': month_data['products'],
                'total': total_month,
                'services_percentage': round((month_data['services'] / total_month * 100), 2) if total_month > 0 else 0,
                'products_percentage': round((month_data['products'] / total_month * 100), 2) if total_month > 0 else 0
            })

            current_date += relativedelta(months=1)

        # Calcular totales de 12 meses
        total_services_12m = sum(item['services'] for item in products_vs_services_monthly)
        total_products_12m = sum(item['products'] for item in products_vs_services_monthly)
        total_12m = total_services_12m + total_products_12m

        return Response({
            'monthly_spending_12m': monthly_data,
            'average_monthly': round(average_monthly, 2),
            'spending_distribution': spending_distribution,
            'products_vs_services_monthly': {
                'data': products_vs_services_monthly,
                'totals_12m': {
                    'services': total_services_12m,
                    'products': total_products_12m,
                    'total': total_12m,
                    'services_percentage': round((total_services_12m / total_12m * 100), 2) if total_12m > 0 else 0,
                    'products_percentage': round((total_products_12m / total_12m * 100), 2) if total_12m > 0 else 0
                }
            }
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

        # Servicios favoritos
        from django.db.models import Sum, Max
        favorite_services = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).values(
            'servicio__id',
            'servicio__nombre'
        ).annotate(
            count=Count('id'),
            total_spent=Sum('monto_total'),
            last_visit=Max('fecha_hora_inicio')
        ).order_by('-count')[:10]

        # Calcular total de visitas para porcentajes
        total_visits = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).count()

        favorite_services_data = []
        for service in favorite_services:
            favorite_services_data.append({
                'service_id': service['servicio__id'],
                'service_name': service['servicio__nombre'],
                'count': service['count'],
                'total_spent': float(service['total_spent'] or 0),
                'percentage': round((service['count'] / total_visits * 100), 2) if total_visits > 0 else 0,
                'last_visit': service['last_visit'].isoformat() if service['last_visit'] else None
            })

        # Servicios por mes (últimos 12 meses)
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        from django.db.models.functions import TruncMonth

        end_date = timezone.now().date()
        start_date = end_date - relativedelta(months=11)

        monthly_services = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO',
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        ).annotate(
            month=TruncMonth('fecha_hora_inicio')
        ).values('month').annotate(
            count=Count('id'),
            total_amount=Sum('monto_total')
        ).order_by('month')

        # Crear estructura con todos los meses
        monthly_services_data = []
        current_date = start_date.replace(day=1)

        # Convertir resultados a diccionario para fácil acceso
        monthly_dict = {}
        for item in monthly_services:
            month_key = item['month'].strftime('%Y-%m')
            monthly_dict[month_key] = {
                'count': item['count'],
                'total_amount': float(item['total_amount'] or 0)
            }

        # Generar datos para todos los meses
        for _ in range(12):
            month_key = current_date.strftime('%Y-%m')
            month_data = monthly_dict.get(month_key, {'count': 0, 'total_amount': 0})

            monthly_services_data.append({
                'month': current_date.strftime('%Y-%m'),
                'month_name': current_date.strftime('%b %Y'),
                'count': month_data['count'],
                'total_amount': month_data['total_amount']
            })

            current_date += relativedelta(months=1)

        # Patrón anual de actividad (promedio histórico por mes del año)
        from django.db.models.functions import ExtractMonth

        # Obtener todos los turnos completados del cliente (histórico completo)
        all_turnos = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        )

        # Agrupar por mes del año (1-12) independiente del año
        monthly_pattern = all_turnos.annotate(
            month_number=ExtractMonth('fecha_hora_inicio')
        ).values('month_number').annotate(
            total_visits=Count('id')
        ).order_by('month_number')

        # Crear diccionario de visitas por mes
        visits_by_month = {}
        for item in monthly_pattern:
            visits_by_month[item['month_number']] = item['total_visits']

        # Calcular cuántos años de historia tiene el cliente
        if all_turnos.exists():
            first_turno = all_turnos.order_by('fecha_hora_inicio').first()
            last_turno = all_turnos.order_by('-fecha_hora_inicio').first()

            years_span = (last_turno.fecha_hora_inicio.year - first_turno.fecha_hora_inicio.year) + 1
            # Mínimo 1 año para evitar división por 0
            years_span = max(years_span, 1)
        else:
            years_span = 1

        # Nombres de meses en español
        month_names = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]

        # Generar array con promedio para cada mes
        monthly_activity_pattern = []
        max_avg = 0
        min_avg = float('inf')
        peak_month = None
        low_month = None

        for month_num in range(1, 13):
            total_visits = visits_by_month.get(month_num, 0)
            avg_visits = total_visits / years_span

            if avg_visits > max_avg:
                max_avg = avg_visits
                peak_month = month_names[month_num - 1]

            if total_visits > 0 and avg_visits < min_avg:  # Solo considerar meses con visitas
                min_avg = avg_visits
                low_month = month_names[month_num - 1]

            monthly_activity_pattern.append({
                'month': month_num,
                'month_name': month_names[month_num - 1],
                'total_visits': total_visits,
                'average_visits': round(avg_visits, 2),
                'years_counted': years_span
            })

        # Determinar interpretación (temporada preferida)
        # Verano: Dic, Ene, Feb (meses 12, 1, 2)
        # Otoño: Mar, Abr, May (meses 3, 4, 5)
        # Invierno: Jun, Jul, Ago (meses 6, 7, 8)
        # Primavera: Sep, Oct, Nov (meses 9, 10, 11)
        season_totals = {
            'Verano': sum(visits_by_month.get(m, 0) for m in [12, 1, 2]),
            'Otoño': sum(visits_by_month.get(m, 0) for m in [3, 4, 5]),
            'Invierno': sum(visits_by_month.get(m, 0) for m in [6, 7, 8]),
            'Primavera': sum(visits_by_month.get(m, 0) for m in [9, 10, 11])
        }

        preferred_season = max(season_totals, key=season_totals.get) if any(season_totals.values()) else None

        return Response({
            'preferred_days': preferred_days_data,
            'preferred_time_slots': time_slots,
            'favorite_services': favorite_services_data,
            'monthly_services': monthly_services_data,
            'monthly_activity_pattern': {
                'data': monthly_activity_pattern,
                'peak_month': peak_month,
                'low_month': low_month,
                'preferred_season': preferred_season,
                'years_analyzed': years_span
            }
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


class ClientServicesView(APIView):
    """
    GET /api/analytics/client/<cliente_id>/services/

    Timeline completo de servicios del cliente con paginación y filtros
    """
    permission_classes = [IsAuthenticated, CanViewClientAnalytics]

    def get(self, request, cliente_id):
        from apps.turnos.models import Turno
        from apps.clientes.models import Cliente
        from django.core.paginator import Paginator, EmptyPage

        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=404)

        # Obtener parámetros de paginación y filtros
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        servicio_id = request.query_params.get('servicio_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Query base - solo servicios completados
        turnos_qs = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).select_related(
            'servicio',
            'profesional',
            'sucursal'
        ).order_by('-fecha_hora_inicio')

        # Aplicar filtros opcionales
        if servicio_id:
            turnos_qs = turnos_qs.filter(servicio_id=int(servicio_id))

        if start_date:
            start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
            turnos_qs = turnos_qs.filter(fecha_hora_inicio__date__gte=start_date_parsed)

        if end_date:
            end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date()
            turnos_qs = turnos_qs.filter(fecha_hora_inicio__date__lte=end_date_parsed)

        # Paginación
        paginator = Paginator(turnos_qs, page_size)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # Serializar servicios
        services_history = []
        for turno in page_obj:
            # Buscar el método de pago en la transacción asociada
            payment_method = 'No especificado'
            try:
                from apps.finanzas.models import Transaction
                transaction = Transaction.objects.filter(
                    turno_id=turno.id,
                    type='INCOME_SERVICE'
                ).first()
                if transaction:
                    payment_method = transaction.payment_method
            except:
                pass

            services_history.append({
                'id': turno.id,
                'date': turno.fecha_hora_inicio.date().isoformat(),
                'time': turno.fecha_hora_inicio.strftime('%H:%M'),
                'service_id': turno.servicio.id if turno.servicio else None,
                'service_name': turno.servicio.nombre if turno.servicio else 'Servicio no especificado',
                'professional_id': turno.profesional.id if turno.profesional else None,
                'professional_name': f"{turno.profesional.first_name} {turno.profesional.last_name}" if turno.profesional else 'No asignado',
                'amount': float(turno.monto_total) if turno.monto_total else 0,
                'payment_method': payment_method,
                'payment_status': turno.estado_pago,
                'notes': turno.notas or ''
            })

        # Calcular estadísticas del período filtrado
        total_spent = sum(float(t.monto_total or 0) for t in turnos_qs)
        avg_ticket = total_spent / turnos_qs.count() if turnos_qs.count() > 0 else 0

        return Response({
            'services_history': services_history,
            'pagination': {
                'total_count': paginator.count,
                'page': page_obj.number,
                'total_pages': paginator.num_pages,
                'page_size': page_size,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'statistics': {
                'total_services': paginator.count,
                'total_spent': total_spent,
                'average_ticket': round(avg_ticket, 2)
            }
        })


class ClientBehaviorView(APIView):
    """
    GET /api/analytics/client/<cliente_id>/behavior/

    Análisis de comportamiento del cliente con loyalty score

    El loyalty score es un valor de 0-100 calculado en base a:
    - Frecuencia de visitas (30 puntos)
    - Recencia de visitas (20 puntos)
    - Valor monetario / LTV (25 puntos)
    - Consistencia de visitas (15 puntos)
    - Engagement / variedad de servicios (10 puntos)
    """
    permission_classes = [IsAuthenticated, CanViewClientAnalytics]

    def get(self, request, cliente_id):
        from apps.turnos.models import Turno
        from apps.clientes.models import Cliente
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        from django.db.models import Count, Avg, StdDev
        from datetime import timedelta

        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=404)

        # Obtener todos los turnos completados
        turnos = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).order_by('fecha_hora_inicio')

        if not turnos.exists():
            return Response({
                'loyalty_score': 0,
                'score_breakdown': {
                    'frequency_score': 0,
                    'recency_score': 0,
                    'monetary_score': 0,
                    'consistency_score': 0,
                    'engagement_score': 0
                },
                'interpretation': 'Sin datos',
                'message': 'El cliente no tiene servicios completados'
            })

        total_visits = turnos.count()
        first_visit = turnos.first().fecha_hora_inicio.date()
        last_visit = turnos.last().fecha_hora_inicio.date()
        today = timezone.now().date()

        # Calcular LTV
        ltv = AnalyticsCalculator.get_client_lifetime_value(cliente_id)

        # ========== 1. FREQUENCY SCORE (30 puntos) ==========
        # Basado en número total de visitas
        frequency_score = 0
        if total_visits >= 50:
            frequency_score = 30
        elif total_visits >= 30:
            frequency_score = 25
        elif total_visits >= 15:
            frequency_score = 20
        elif total_visits >= 8:
            frequency_score = 15
        elif total_visits >= 4:
            frequency_score = 10
        elif total_visits >= 2:
            frequency_score = 5
        else:  # 1 visita
            frequency_score = 2

        # ========== 2. RECENCY SCORE (20 puntos) ==========
        # Basado en días desde última visita
        days_since_last = (today - last_visit).days
        recency_score = 0
        if days_since_last <= 7:
            recency_score = 20  # Visitó esta semana
        elif days_since_last <= 14:
            recency_score = 18  # Visitó hace 1-2 semanas
        elif days_since_last <= 30:
            recency_score = 15  # Visitó este mes
        elif days_since_last <= 60:
            recency_score = 10  # Visitó hace 1-2 meses
        elif days_since_last <= 90:
            recency_score = 5   # Visitó hace 2-3 meses
        else:
            recency_score = 0   # Más de 3 meses sin visitar

        # ========== 3. MONETARY SCORE (25 puntos) ==========
        # Basado en LTV (Lifetime Value)
        monetary_score = 0
        if ltv >= 100000:
            monetary_score = 25
        elif ltv >= 50000:
            monetary_score = 22
        elif ltv >= 30000:
            monetary_score = 18
        elif ltv >= 15000:
            monetary_score = 14
        elif ltv >= 8000:
            monetary_score = 10
        elif ltv >= 3000:
            monetary_score = 6
        elif ltv >= 1000:
            monetary_score = 3
        else:
            monetary_score = 1

        # ========== 4. CONSISTENCY SCORE (15 puntos) ==========
        # Basado en regularidad de visitas (desviación estándar de días entre visitas)
        if total_visits >= 2:
            # Calcular días entre cada visita
            visit_dates = [t.fecha_hora_inicio.date() for t in turnos]
            days_between_visits = []
            for i in range(1, len(visit_dates)):
                days_diff = (visit_dates[i] - visit_dates[i-1]).days
                days_between_visits.append(days_diff)

            if days_between_visits:
                avg_days_between = sum(days_between_visits) / len(days_between_visits)

                # Calcular desviación estándar manualmente
                variance = sum((x - avg_days_between) ** 2 for x in days_between_visits) / len(days_between_visits)
                std_dev = variance ** 0.5

                # Coefficient of variation (CV = std_dev / mean)
                # Menor CV = más consistente
                if avg_days_between > 0:
                    cv = std_dev / avg_days_between

                    # Asignar puntos basado en consistencia
                    if cv <= 0.3:  # Muy consistente
                        consistency_score = 15
                    elif cv <= 0.5:
                        consistency_score = 12
                    elif cv <= 0.8:
                        consistency_score = 9
                    elif cv <= 1.2:
                        consistency_score = 6
                    else:  # Muy inconsistente
                        consistency_score = 3
                else:
                    consistency_score = 5
            else:
                consistency_score = 5
        else:
            consistency_score = 0  # Solo 1 visita

        # ========== 5. ENGAGEMENT SCORE (10 puntos) ==========
        # Basado en variedad de servicios utilizados
        unique_services = turnos.values('servicio').distinct().count()
        engagement_score = 0
        if unique_services >= 10:
            engagement_score = 10
        elif unique_services >= 7:
            engagement_score = 8
        elif unique_services >= 5:
            engagement_score = 6
        elif unique_services >= 3:
            engagement_score = 4
        elif unique_services >= 2:
            engagement_score = 2
        else:  # Solo 1 servicio
            engagement_score = 1

        # ========== TOTAL SCORE ==========
        total_score = (
            frequency_score +
            recency_score +
            monetary_score +
            consistency_score +
            engagement_score
        )

        # Interpretación del score
        if total_score >= 85:
            interpretation = 'VIP'
            level = 'Excelente'
        elif total_score >= 70:
            interpretation = 'Leal'
            level = 'Muy Bueno'
        elif total_score >= 55:
            interpretation = 'Comprometido'
            level = 'Bueno'
        elif total_score >= 40:
            interpretation = 'Regular'
            level = 'Regular'
        elif total_score >= 25:
            interpretation = 'En Riesgo'
            level = 'Bajo'
        else:
            interpretation = 'Inactivo'
            level = 'Muy Bajo'

        # ========== ACTIVITY HEATMAP (365 días) ==========
        # Crear mapa de actividad para los últimos 365 días
        activity_end_date = today
        activity_start_date = today - timedelta(days=365)

        # Obtener todos los turnos en el rango
        activity_turnos = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO',
            fecha_hora_inicio__date__gte=activity_start_date,
            fecha_hora_inicio__date__lte=activity_end_date
        ).values('fecha_hora_inicio__date').annotate(
            count=Count('id')
        )

        # Crear diccionario de actividad por día
        activity_by_day = {}
        for item in activity_turnos:
            date_str = item['fecha_hora_inicio__date'].isoformat()
            activity_by_day[date_str] = item['count']

        # Generar array con todos los días (365 días)
        activity_heatmap = []
        current_day = activity_start_date
        max_activity = 0

        while current_day <= activity_end_date:
            date_str = current_day.isoformat()
            count = activity_by_day.get(date_str, 0)
            if count > max_activity:
                max_activity = count

            activity_heatmap.append({
                'date': date_str,
                'count': count,
                'day_of_week': current_day.weekday(),  # 0=Monday, 6=Sunday
                'week_of_year': current_day.isocalendar()[1]
            })

            current_day += timedelta(days=1)

        # ========== BEHAVIOR METRICS ==========
        # Obtener todos los turnos del cliente (no solo completados)
        all_appointments = Turno.objects.filter(cliente_id=cliente_id)
        total_appointments = all_appointments.count()

        # Calcular tasa de no-show
        no_show_count = all_appointments.filter(estado='NO_SHOW').count()
        no_show_rate = round((no_show_count / total_appointments * 100), 2) if total_appointments > 0 else 0

        # Calcular tasa de cancelación
        cancelled_count = all_appointments.filter(estado='CANCELADO').count()
        cancellation_rate = round((cancelled_count / total_appointments * 100), 2) if total_appointments > 0 else 0

        # Calcular tiempo promedio entre visitas (usar días entre visitas calculado arriba)
        avg_interval_days = 0
        if total_visits >= 2:
            visit_dates = [t.fecha_hora_inicio.date() for t in turnos]
            days_between = []
            for i in range(1, len(visit_dates)):
                days_between.append((visit_dates[i] - visit_dates[i-1]).days)

            if days_between:
                avg_interval_days = round(sum(days_between) / len(days_between), 1)

        # Calcular puntuación de puntualidad (placeholder - podría mejorarse con datos de llegada real)
        # Por ahora, basado en tasa de completitud vs cancelaciones/no-shows
        completed_count = turnos.count()
        punctuality_score = 0
        if total_appointments > 0:
            completion_rate = (completed_count / total_appointments) * 100
            # Score de 0-100 basado en tasa de completitud
            punctuality_score = round(completion_rate, 1)

        return Response({
            'loyalty_score': total_score,
            'score_breakdown': {
                'frequency_score': frequency_score,
                'frequency_max': 30,
                'recency_score': recency_score,
                'recency_max': 20,
                'monetary_score': monetary_score,
                'monetary_max': 25,
                'consistency_score': consistency_score,
                'consistency_max': 15,
                'engagement_score': engagement_score,
                'engagement_max': 10
            },
            'interpretation': interpretation,
            'level': level,
            'metrics': {
                'total_visits': total_visits,
                'lifetime_value': round(ltv, 2),
                'days_since_last_visit': days_since_last,
                'unique_services': unique_services,
                'first_visit': first_visit.isoformat(),
                'last_visit': last_visit.isoformat(),
                'customer_lifetime_days': (today - first_visit).days
            },
            'activity_heatmap': {
                'data': activity_heatmap,
                'max_activity': max_activity,
                'total_days': len(activity_heatmap),
                'active_days': sum(1 for item in activity_heatmap if item['count'] > 0)
            },
            'behavior_metrics': {
                'no_show_rate': no_show_rate,
                'cancellation_rate': cancellation_rate,
                'average_interval_days': avg_interval_days,
                'punctuality_score': punctuality_score,
                'total_appointments': total_appointments,
                'completed_appointments': completed_count,
                'no_show_count': no_show_count,
                'cancelled_count': cancelled_count
            }
        })

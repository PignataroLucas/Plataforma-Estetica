"""
Utilidades para cálculos de analytics
Contiene funciones para agregaciones SQL optimizadas y cálculos de métricas
"""

from django.db.models import Sum, Count, Avg, Q, F, FloatField, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, ExtractWeekDay, ExtractHour
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from apps.turnos.models import Turno
from apps.finanzas.models import Transaction
from apps.clientes.models import Cliente
from apps.servicios.models import Servicio
from apps.inventario.models import Producto, MovimientoInventario
from apps.empleados.models import Usuario


class AnalyticsCalculator:
    """
    Clase con métodos estáticos para cálculos de analytics
    Optimizada con agregaciones SQL para mejor performance
    """

    # ========== DASHBOARD SUMMARY ==========

    @staticmethod
    def get_dashboard_summary(sucursal_id=None, start_date=None, end_date=None):
        """
        Calcula el resumen completo para el dashboard principal
        Incluye KPIs comparados con período anterior
        """
        if not start_date or not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)

        # Calcular período anterior (misma duración)
        period_duration = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_duration)
        previous_end = start_date - timedelta(days=1)

        # Métricas del período actual
        current_metrics = AnalyticsCalculator._get_period_metrics(
            sucursal_id, start_date, end_date
        )

        # Métricas del período anterior
        previous_metrics = AnalyticsCalculator._get_period_metrics(
            sucursal_id, previous_start, previous_end
        )

        # Calcular cambios porcentuales
        kpis = {
            'total_revenue': current_metrics['revenue'],
            'revenue_change': AnalyticsCalculator._calculate_change(
                current_metrics['revenue'],
                previous_metrics['revenue']
            ),
            'revenue_breakdown': {
                'services': current_metrics['services_revenue'],
                'products': current_metrics['products_revenue'],
                'other': current_metrics['other_revenue']
            },
            'total_appointments': current_metrics['appointments'],
            'appointments_change': AnalyticsCalculator._calculate_change(
                current_metrics['appointments'],
                previous_metrics['appointments']
            ),
            'completion_rate': current_metrics['completion_rate'],
            'active_clients': current_metrics['active_clients'],
            'new_clients': current_metrics['new_clients'],
            'retention_rate': current_metrics['retention_rate'],
            'average_ticket': current_metrics['avg_ticket'],
            'ticket_change': AnalyticsCalculator._calculate_change(
                current_metrics['avg_ticket'],
                previous_metrics['avg_ticket']
            )
        }

        return {
            'kpis': kpis,
            'period': {
                'start': start_date,
                'end': end_date,
                'previous_start': previous_start,
                'previous_end': previous_end
            }
        }

    @staticmethod
    def _get_period_metrics(sucursal_id, start_date, end_date):
        """
        Obtiene métricas para un período específico
        """
        # Filtro base de transacciones
        transactions_qs = Transaction.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        if sucursal_id:
            transactions_qs = transactions_qs.filter(branch_id=sucursal_id)

        # Ingresos por tipo
        revenue_data = transactions_qs.filter(
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT', 'INCOME_OTHER']
        ).aggregate(
            total=Sum('amount'),
            services=Sum('amount', filter=Q(type='INCOME_SERVICE')),
            products=Sum('amount', filter=Q(type='INCOME_PRODUCT')),
            other=Sum('amount', filter=Q(type='INCOME_OTHER')),
            count=Count('id')
        )

        # Filtro base de turnos
        turnos_qs = Turno.objects.filter(
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )
        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        # Métricas de turnos
        turnos_data = turnos_qs.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(estado='COMPLETADO')),
            canceled=Count('id', filter=Q(estado='CANCELADO')),
            no_show=Count('id', filter=Q(estado='NO_SHOW'))
        )

        total_turnos = turnos_data['total'] or 0
        completed_turnos = turnos_data['completed'] or 0
        completion_rate = (completed_turnos / total_turnos * 100) if total_turnos > 0 else 0

        # Clientes activos (con al menos 1 turno en el período)
        active_clients = turnos_qs.values('cliente_id').distinct().count()

        # Clientes nuevos (primera visita en este período)
        new_clients = Cliente.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        if sucursal_id:
            new_clients = new_clients.filter(sucursal__id=sucursal_id)
        new_clients_count = new_clients.count()

        # Tasa de retención (clientes que volvieron vs nuevos)
        returning_clients = active_clients - new_clients_count
        retention_rate = (returning_clients / active_clients * 100) if active_clients > 0 else 0

        # Ticket promedio
        revenue_count = revenue_data['count'] or 0
        avg_ticket = (revenue_data['total'] / revenue_count) if revenue_count > 0 else 0

        return {
            'revenue': revenue_data['total'] or 0,
            'services_revenue': revenue_data['services'] or 0,
            'products_revenue': revenue_data['products'] or 0,
            'other_revenue': revenue_data['other'] or 0,
            'appointments': completed_turnos,
            'completion_rate': round(completion_rate, 2),
            'active_clients': active_clients,
            'new_clients': new_clients_count,
            'retention_rate': round(retention_rate, 2),
            'avg_ticket': float(avg_ticket) if avg_ticket else 0
        }

    @staticmethod
    def _calculate_change(current, previous):
        """
        Calcula el cambio porcentual entre dos valores
        """
        if not previous or previous == 0:
            return 100.0 if current > 0 else 0.0

        change = ((current - previous) / previous) * 100
        return round(change, 2)

    # ========== REVENUE ANALYTICS ==========

    @staticmethod
    def get_revenue_evolution(sucursal_id=None, start_date=None, end_date=None, granularity='day'):
        """
        Obtiene la evolución de ingresos en el tiempo
        granularity: 'day', 'week', 'month'
        """
        transactions_qs = Transaction.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT', 'INCOME_OTHER']
        )

        if sucursal_id:
            transactions_qs = transactions_qs.filter(branch_id=sucursal_id)

        # Seleccionar función de truncado según granularidad
        if granularity == 'month':
            trunc_func = TruncMonth
            date_format = '%Y-%m'
        elif granularity == 'week':
            trunc_func = TruncWeek
            date_format = '%Y-W%U'
        else:  # day
            trunc_func = TruncDay
            date_format = '%Y-%m-%d'

        # Agrupar por período
        evolution = transactions_qs.annotate(
            period=trunc_func('fecha')
        ).values('period').annotate(
            services_revenue=Sum('amount', filter=Q(type='INCOME_SERVICE')),
            products_revenue=Sum('amount', filter=Q(type='INCOME_PRODUCT')),
            total_revenue=Sum('amount')
        ).order_by('period')

        # Formatear resultados
        result = []
        for item in evolution:
            result.append({
                'date': item['period'].strftime(date_format),
                'services_revenue': float(item['services_revenue'] or 0),
                'products_revenue': float(item['products_revenue'] or 0),
                'total_revenue': float(item['total_revenue'] or 0)
            })

        return result

    @staticmethod
    def get_revenue_by_payment_method(sucursal_id=None, start_date=None, end_date=None):
        """
        Obtiene distribución de ingresos por método de pago
        """
        transactions_qs = Transaction.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT', 'INCOME_OTHER']
        )

        if sucursal_id:
            transactions_qs = transactions_qs.filter(branch_id=sucursal_id)

        by_method = transactions_qs.values('payment_method').annotate(
            amount=Sum('amount'),
            count=Count('id')
        ).order_by('-amount')

        total_revenue = sum(item['amount'] for item in by_method if item['amount'])

        result = []
        for item in by_method:
            if item['amount']:
                result.append({
                    'method': item['payment_method'],
                    'amount': float(item['amount']),
                    'percentage': round((item['amount'] / total_revenue * 100), 2) if total_revenue > 0 else 0,
                    'count': item['count']
                })

        return result

    # ========== SERVICE ANALYTICS ==========

    @staticmethod
    def get_top_services(sucursal_id=None, start_date=None, end_date=None, limit=10):
        """
        Obtiene los servicios más vendidos
        """
        turnos_qs = Turno.objects.filter(
            estado='COMPLETADO',
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        top_services = turnos_qs.values(
            'servicio__id',
            'servicio__nombre'
        ).annotate(
            quantity_sold=Count('id'),
            revenue=Sum('precio_final')
        ).order_by('-quantity_sold')[:limit]

        result = []
        for item in top_services:
            avg_ticket = (item['revenue'] / item['quantity_sold']) if item['quantity_sold'] > 0 else 0
            result.append({
                'service_id': item['servicio__id'],
                'service_name': item['servicio__nombre'],
                'quantity_sold': item['quantity_sold'],
                'revenue': float(item['revenue'] or 0),
                'average_ticket': float(avg_ticket)
            })

        return result

    @staticmethod
    def get_service_profitability(sucursal_id=None, start_date=None, end_date=None):
        """
        Calcula la rentabilidad de cada servicio
        Considera costos de máquinas alquiladas si aplica
        """
        from apps.servicios.models import AlquilerMaquina

        turnos_qs = Turno.objects.filter(
            estado='COMPLETADO',
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        # Agrupar por servicio
        service_data = turnos_qs.values(
            'servicio__id',
            'servicio__nombre',
            'servicio__maquina_alquilada__id',
            'servicio__maquina_alquilada__costo_diario'
        ).annotate(
            quantity=Count('id'),
            revenue=Sum('precio_final')
        )

        result = []
        for item in service_data:
            revenue = float(item['revenue'] or 0)
            quantity = item['quantity']

            # Calcular costo si usa máquina alquilada
            cost = 0
            if item['servicio__maquina_alquilada__id']:
                # Obtener días únicos donde se usó el servicio
                days_used = turnos_qs.filter(
                    servicio__id=item['servicio__id']
                ).values('fecha').distinct().count()

                daily_cost = float(item['servicio__maquina_alquilada__costo_diario'] or 0)
                cost = daily_cost * days_used

            gross_margin = revenue - cost
            margin_percentage = (gross_margin / revenue * 100) if revenue > 0 else 0

            result.append({
                'service_id': item['servicio__id'],
                'service_name': item['servicio__nombre'],
                'quantity': quantity,
                'revenue': revenue,
                'cost': cost,
                'gross_margin': gross_margin,
                'margin_percentage': round(margin_percentage, 2)
            })

        # Ordenar por cantidad vendida
        result.sort(key=lambda x: x['quantity'], reverse=True)

        return result

    # ========== PRODUCT ANALYTICS ==========

    @staticmethod
    def get_top_products(sucursal_id=None, start_date=None, end_date=None, limit=10):
        """
        Obtiene los productos más vendidos
        """
        # Obtener movimientos de salida (ventas)
        movimientos_qs = MovimientoInventario.objects.filter(
            tipo='SALIDA',
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            movimientos_qs = movimientos_qs.filter(producto__sucursal_id=sucursal_id)

        top_products = movimientos_qs.values(
            'producto__id',
            'producto__nombre',
            'producto__precio_venta'
        ).annotate(
            quantity_sold=Sum('cantidad'),
            # Calcular revenue: cantidad * precio
        ).order_by('-quantity_sold')[:limit]

        result = []
        for item in top_products:
            revenue = item['quantity_sold'] * (item['producto__precio_venta'] or 0)
            result.append({
                'product_id': item['producto__id'],
                'product_name': item['producto__nombre'],
                'quantity_sold': item['quantity_sold'],
                'revenue': float(revenue),
                'unit_price': float(item['producto__precio_venta'] or 0)
            })

        return result

    # ========== CLIENT ANALYTICS ==========

    @staticmethod
    def get_client_lifetime_value(cliente_id):
        """
        Calcula el Lifetime Value total de un cliente
        """
        ltv = Transaction.objects.filter(
            client_id=cliente_id,
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT']
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        return float(ltv)

    @staticmethod
    def get_client_frequency(cliente_id):
        """
        Calcula la frecuencia promedio de visitas en días
        """
        visitas = list(Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).order_by('fecha_hora_inicio').values_list('fecha_hora_inicio', flat=True))

        if len(visitas) < 2:
            return None

        # Calcular intervalos entre visitas consecutivas
        intervals = []
        for i in range(1, len(visitas)):
            delta = (visitas[i] - visitas[i-1]).days
            if delta > 0:  # Ignorar visitas el mismo día
                intervals.append(delta)

        average_interval = sum(intervals) / len(intervals) if intervals else None
        return round(average_interval, 1) if average_interval else None

    @staticmethod
    def get_client_status(cliente_id):
        """
        Determina el estado del cliente: VIP, ACTIVE, AT_RISK, INACTIVE
        """
        # Obtener LTV del cliente
        ltv = AnalyticsCalculator.get_client_lifetime_value(cliente_id)

        # Obtener percentil 80 (top 20%) de LTV
        all_clients_ltv = Transaction.objects.filter(
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT']
        ).values('client_id').annotate(
            client_ltv=Sum('amount')
        ).order_by('-client_ltv')

        # Si hay suficientes clientes, calcular threshold VIP
        vip_threshold = 0
        if all_clients_ltv.count() > 5:
            threshold_index = int(all_clients_ltv.count() * 0.2)
            vip_clients = list(all_clients_ltv)[:threshold_index]
            if vip_clients:
                vip_threshold = min([c['client_ltv'] for c in vip_clients])

        # Check VIP
        if ltv >= vip_threshold and vip_threshold > 0:
            return 'VIP'

        # Obtener última visita
        last_visit = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).order_by('-fecha_hora_inicio').first()

        if not last_visit:
            return 'INACTIVE'

        days_since_last = (timezone.now().date() - last_visit.fecha_hora_inicio.date()).days

        # Determinar estado según días desde última visita
        if days_since_last <= 30:
            return 'ACTIVE'
        elif days_since_last <= 90:
            return 'AT_RISK'
        else:
            return 'INACTIVE'

    @staticmethod
    def get_client_segmentation(sucursal_id=None):
        """
        Segmenta todos los clientes por estado
        """
        clientes_qs = Cliente.objects.all()
        if sucursal_id:
            clientes_qs = clientes_qs.filter(centro_estetica__sucursales__id=sucursal_id)

        segmentation = {
            'VIP': 0,
            'ACTIVE': 0,
            'AT_RISK': 0,
            'INACTIVE': 0,
            'NEW': 0
        }

        # Esto puede ser lento con muchos clientes - considerar caché
        for cliente in clientes_qs:
            # Clientes nuevos (menos de 30 días)
            if cliente.created_at and (timezone.now().date() - cliente.created_at.date()).days <= 30:
                segmentation['NEW'] += 1
            else:
                status = AnalyticsCalculator.get_client_status(cliente.id)
                segmentation[status] += 1

        return segmentation

    # ========== EMPLOYEE ANALYTICS ==========

    @staticmethod
    def get_employee_performance(sucursal_id=None, start_date=None, end_date=None):
        """
        Obtiene performance de cada empleado
        """
        turnos_qs = Turno.objects.filter(
            estado='COMPLETADO',
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        performance = turnos_qs.values(
            'profesional__id',
            'profesional__first_name',
            'profesional__last_name'
        ).annotate(
            services_count=Count('id'),
            revenue=Sum('precio_final')
        ).order_by('-revenue')

        result = []
        for item in performance:
            avg_ticket = (item['revenue'] / item['services_count']) if item['services_count'] > 0 else 0

            # Obtener comisiones del empleado en el período
            from apps.empleados.models import Comision
            comisiones_total = Comision.objects.filter(
                empleado_id=item['profesional__id'],
                turno__fecha_hora_inicio__date__gte=start_date,
                turno__fecha_hora_inicio__date__lte=end_date
            ).aggregate(total=Sum('monto'))['total'] or 0

            result.append({
                'employee_id': item['profesional__id'],
                'employee_name': f"{item['profesional__first_name']} {item['profesional__last_name']}",
                'services_count': item['services_count'],
                'revenue_generated': float(item['revenue'] or 0),
                'average_ticket': float(avg_ticket),
                'commissions_earned': float(comisiones_total)
            })

        return result

    # ========== OCCUPANCY ANALYTICS ==========

    @staticmethod
    def get_occupancy_by_day_of_week(sucursal_id=None, start_date=None, end_date=None):
        """
        Calcula ocupación por día de la semana
        """
        turnos_qs = Turno.objects.filter(
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        # Contar turnos por día de semana
        by_weekday = turnos_qs.annotate(
            weekday=ExtractWeekDay('fecha')
        ).values('weekday').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(estado='COMPLETADO'))
        ).order_by('weekday')

        days_map = {
            1: 'Sunday',
            2: 'Monday',
            3: 'Tuesday',
            4: 'Wednesday',
            5: 'Thursday',
            6: 'Friday',
            7: 'Saturday'
        }

        result = {day: 0 for day in days_map.values()}

        for item in by_weekday:
            day_name = days_map.get(item['weekday'], 'Unknown')
            result[day_name] = item['completed']

        return result

    # ========== NO-SHOW ANALYTICS ==========

    @staticmethod
    def get_no_show_stats(sucursal_id=None, start_date=None, end_date=None):
        """
        Obtiene estadísticas de no-shows
        """
        turnos_qs = Turno.objects.filter(
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        stats = turnos_qs.aggregate(
            total=Count('id'),
            no_shows=Count('id', filter=Q(estado='NO_SHOW')),
            canceled=Count('id', filter=Q(estado='CANCELADO'))
        )

        total = stats['total'] or 0
        no_show_rate = (stats['no_shows'] / total * 100) if total > 0 else 0
        cancelation_rate = (stats['canceled'] / total * 100) if total > 0 else 0

        return {
            'total_appointments': total,
            'no_shows': stats['no_shows'],
            'no_show_rate': round(no_show_rate, 2),
            'cancelations': stats['canceled'],
            'cancelation_rate': round(cancelation_rate, 2)
        }

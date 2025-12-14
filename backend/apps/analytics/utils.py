"""
Utilidades para cálculos de analytics
Contiene funciones para agregaciones SQL optimizadas y cálculos de métricas
"""

from django.db.models import Sum, Count, Avg, Q, F, FloatField, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, ExtractWeekDay, ExtractHour, ExtractMonth
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
            creado_en__date__gte=start_date,
            creado_en__date__lte=end_date
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
            period=trunc_func('date')
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
            revenue=Sum('monto_total')
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
            revenue=Sum('monto_total')
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
                ).dates('fecha_hora_inicio', 'day').count()

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

    @staticmethod
    def get_service_evolution(sucursal_id=None, start_date=None, end_date=None, granularity='day'):
        """
        Obtiene la evolución temporal de los top 5 servicios
        """
        from datetime import datetime, timedelta
        from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

        # Primero obtener los top 5 servicios
        top_services = AnalyticsCalculator.get_top_services(
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            limit=5
        )

        if not top_services:
            return []

        top_service_ids = [s['service_id'] for s in top_services]

        # Filtrar turnos por los top servicios
        turnos_qs = Turno.objects.filter(
            servicio_id__in=top_service_ids,
            estado='COMPLETADO',
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        # Elegir función de truncamiento según granularidad
        if granularity == 'week':
            trunc_func = TruncWeek('fecha_hora_inicio')
        elif granularity == 'month':
            trunc_func = TruncMonth('fecha_hora_inicio')
        else:  # 'day'
            trunc_func = TruncDate('fecha_hora_inicio')

        # Agrupar por fecha y servicio
        evolution_data = turnos_qs.annotate(
            period=trunc_func
        ).values(
            'period', 'servicio__id', 'servicio__nombre'
        ).annotate(
            count=Count('id')
        ).order_by('period')

        # Organizar datos por período
        result_by_period = {}
        for item in evolution_data:
            period_str = item['period'].strftime('%Y-%m-%d')
            if period_str not in result_by_period:
                result_by_period[period_str] = {'date': period_str}

            service_name = item['servicio__nombre']
            result_by_period[period_str][service_name] = item['count']

        # Asegurar que todos los servicios estén presentes en todos los períodos
        service_names = [s['service_name'] for s in top_services]
        for period_data in result_by_period.values():
            for service_name in service_names:
                if service_name not in period_data:
                    period_data[service_name] = 0

        # Convertir a lista ordenada por fecha
        result = sorted(result_by_period.values(), key=lambda x: x['date'])

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
            creado_en__date__gte=start_date,
            creado_en__date__lte=end_date
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
            if cliente.creado_en and (timezone.now().date() - cliente.creado_en.date()).days <= 30:
                segmentation['NEW'] += 1
            else:
                status = AnalyticsCalculator.get_client_status(cliente.id)
                segmentation[status] += 1

        return segmentation

    @staticmethod
    def get_top_clients(sucursal_id=None, limit=20):
        """
        Obtiene los top clientes por LTV (Lifetime Value)
        """
        from apps.finanzas.models import Transaction

        # Obtener clientes
        clientes_qs = Cliente.objects.all()
        if sucursal_id:
            clientes_qs = clientes_qs.filter(centro_estetica__sucursales__id=sucursal_id)

        # Calcular LTV por cliente usando transacciones
        clients_data = []
        for cliente in clientes_qs:
            # Calcular LTV (total gastado)
            ltv = Transaction.objects.filter(
                client_id=cliente.id,
                type__in=['INCOME_SERVICE', 'INCOME_PRODUCT']
            ).aggregate(total=Sum('amount'))['total'] or 0

            # Contar visitas (turnos completados)
            visits_count = Turno.objects.filter(
                cliente_id=cliente.id,
                estado='COMPLETADO'
            ).count()

            # Última visita
            last_visit = Turno.objects.filter(
                cliente_id=cliente.id,
                estado='COMPLETADO'
            ).order_by('-fecha_hora_inicio').first()

            last_visit_date = last_visit.fecha_hora_inicio.date() if last_visit else None

            # Determinar estado
            status = AnalyticsCalculator.get_client_status(cliente.id)

            if ltv > 0 or visits_count > 0:  # Solo incluir clientes con actividad
                clients_data.append({
                    'client_id': cliente.id,
                    'client_name': f"{cliente.nombre} {cliente.apellido}",
                    'email': cliente.email or '',
                    'phone': cliente.telefono or '',
                    'ltv': float(ltv),
                    'visits_count': visits_count,
                    'last_visit': last_visit_date.isoformat() if last_visit_date else None,
                    'status': status
                })

        # Ordenar por LTV descendente y tomar top N
        clients_data.sort(key=lambda x: x['ltv'], reverse=True)
        return clients_data[:limit]

    @staticmethod
    def get_ltv_distribution(sucursal_id=None):
        """
        Obtiene la distribución de clientes por rangos de LTV
        """
        from apps.finanzas.models import Transaction

        # Definir rangos de LTV (max_value None significa infinito para el último rango)
        ranges = [
            {'label': '$0 - $5,000', 'min': 0, 'max': 5000},
            {'label': '$5,000 - $10,000', 'min': 5000, 'max': 10000},
            {'label': '$10,000 - $20,000', 'min': 10000, 'max': 20000},
            {'label': '$20,000 - $50,000', 'min': 20000, 'max': 50000},
            {'label': '$50,000+', 'min': 50000, 'max': None}  # None = sin límite superior
        ]

        # Obtener clientes
        clientes_qs = Cliente.objects.all()
        if sucursal_id:
            clientes_qs = clientes_qs.filter(centro_estetica__sucursales__id=sucursal_id)

        # Inicializar contadores
        distribution = {r['label']: 0 for r in ranges}

        # Calcular LTV para cada cliente y clasificar
        for cliente in clientes_qs:
            ltv = Transaction.objects.filter(
                client_id=cliente.id,
                type__in=['INCOME_SERVICE', 'INCOME_PRODUCT']
            ).aggregate(total=Sum('amount'))['total'] or 0

            # Clasificar en rango
            for range_def in ranges:
                max_val = range_def['max']
                if max_val is None:  # Último rango sin límite superior
                    if ltv >= range_def['min']:
                        distribution[range_def['label']] += 1
                        break
                elif range_def['min'] <= ltv < max_val:
                    distribution[range_def['label']] += 1
                    break

        # Convertir a formato de respuesta
        result = [
            {
                'range': label,
                'count': count,
                'min_value': next(r['min'] for r in ranges if r['label'] == label),
                'max_value': next(r['max'] for r in ranges if r['label'] == label)
            }
            for label, count in distribution.items()
        ]

        return result

    @staticmethod
    def get_seasonal_trends(sucursal_id=None, year=None):
        """
        Obtiene tendencias estacionales por mes y trimestre
        """
        from datetime import datetime
        from apps.finanzas.models import Transaction

        # Si no se especifica año, usar el actual
        if not year:
            year = datetime.now().year

        # Filtrar turnos completados del año
        turnos_qs = Turno.objects.filter(
            estado='COMPLETADO',
            fecha_hora_inicio__year=year
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        # Agrupar por mes
        monthly_data = turnos_qs.annotate(
            month=ExtractMonth('fecha_hora_inicio')
        ).values('month').annotate(
            appointments=Count('id'),
            revenue=Sum('monto_total')
        ).order_by('month')

        # Convertir a diccionario para fácil acceso
        monthly_dict = {item['month']: item for item in monthly_data}

        # Nombres de meses en español
        month_names = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]

        # Crear resultado con todos los meses (incluso si no hay datos)
        monthly_trends = []
        for month_num in range(1, 13):
            data = monthly_dict.get(month_num, {'appointments': 0, 'revenue': 0})
            monthly_trends.append({
                'month': month_num,
                'month_name': month_names[month_num - 1],
                'appointments': data['appointments'],
                'revenue': float(data['revenue'] or 0),
                'avg_ticket': float(data['revenue'] / data['appointments']) if data['appointments'] > 0 else 0
            })

        # Agrupar por trimestre
        quarterly_data = []
        quarters = [
            {'name': 'Q1', 'months': [1, 2, 3]},
            {'name': 'Q2', 'months': [4, 5, 6]},
            {'name': 'Q3', 'months': [7, 8, 9]},
            {'name': 'Q4', 'months': [10, 11, 12]}
        ]

        for quarter in quarters:
            quarter_turnos = [m for m in monthly_trends if m['month'] in quarter['months']]
            total_appointments = sum(m['appointments'] for m in quarter_turnos)
            total_revenue = sum(m['revenue'] for m in quarter_turnos)

            quarterly_data.append({
                'quarter': quarter['name'],
                'appointments': total_appointments,
                'revenue': total_revenue,
                'avg_ticket': total_revenue / total_appointments if total_appointments > 0 else 0
            })

        # Identificar mes pico
        peak_month = max(monthly_trends, key=lambda x: x['revenue'])
        lowest_month = min(monthly_trends, key=lambda x: x['revenue'])

        return {
            'year': year,
            'monthly_trends': monthly_trends,
            'quarterly_trends': quarterly_data,
            'peak_month': peak_month['month_name'],
            'peak_revenue': peak_month['revenue'],
            'lowest_month': lowest_month['month_name'],
            'lowest_revenue': lowest_month['revenue'],
            'total_year_revenue': sum(m['revenue'] for m in monthly_trends),
            'total_year_appointments': sum(m['appointments'] for m in monthly_trends)
        }

    @staticmethod
    def get_inventory_rotation(sucursal_id=None, days=90):
        """
        Obtiene análisis de rotación de inventario de productos
        """
        from apps.inventario.models import Producto
        from apps.finanzas.models import Transaction
        from datetime import datetime, timedelta
        from django.utils import timezone

        # Fecha de inicio para el período de análisis
        start_date = timezone.now().date() - timedelta(days=days)

        # Obtener productos
        productos_qs = Producto.objects.filter(activo=True)
        if sucursal_id:
            productos_qs = productos_qs.filter(sucursal_id=sucursal_id)

        rotation_data = []

        for producto in productos_qs:
            # Calcular ventas en el período
            sales = Transaction.objects.filter(
                type='INCOME_PRODUCT',
                description__icontains=producto.nombre,  # Assuming product name is in description
                date__gte=start_date
            ).count()

            # Stock actual
            current_stock = float(producto.stock_actual)

            # Calcular tasa de rotación (ventas / días del período)
            rotation_rate = sales / days if days > 0 else 0

            # Días de inventario restante (stock / tasa de rotación diaria)
            days_of_inventory = current_stock / rotation_rate if rotation_rate > 0 else 999

            # Clasificar velocidad de rotación
            if rotation_rate >= 1:  # Más de 1 venta por día
                speed = 'FAST'
                speed_label = 'Rápida'
            elif rotation_rate >= 0.3:  # Al menos 1 venta cada 3 días
                speed = 'MEDIUM'
                speed_label = 'Media'
            elif rotation_rate > 0:
                speed = 'SLOW'
                speed_label = 'Lenta'
            else:
                speed = 'DEAD'
                speed_label = 'Sin Movimiento'

            # Valorización del stock (stock * precio)
            stock_value = current_stock * float(producto.precio_venta or 0)

            rotation_data.append({
                'product_id': producto.id,
                'product_name': producto.nombre,
                'category': getattr(producto.categoria, 'nombre', 'Sin categoría') if hasattr(producto, 'categoria') else 'Sin categoría',
                'current_stock': current_stock,
                'sales_count': sales,
                'rotation_rate': round(rotation_rate, 2),
                'days_of_inventory': min(days_of_inventory, 999),  # Cap at 999 for display
                'speed': speed,
                'speed_label': speed_label,
                'stock_value': float(stock_value),
                'unit_price': float(producto.precio_venta or 0)
            })

        # Ordenar por tasa de rotación descendente
        rotation_data.sort(key=lambda x: x['rotation_rate'], reverse=True)

        # Calcular estadísticas agregadas
        total_stock_value = sum(item['stock_value'] for item in rotation_data)
        fast_moving = len([item for item in rotation_data if item['speed'] == 'FAST'])
        medium_moving = len([item for item in rotation_data if item['speed'] == 'MEDIUM'])
        slow_moving = len([item for item in rotation_data if item['speed'] == 'SLOW'])
        dead_stock = len([item for item in rotation_data if item['speed'] == 'DEAD'])

        # Top 10 productos de mayor rotación
        top_rotation = rotation_data[:10]

        # Productos sin movimiento (dead stock)
        dead_stock_items = [item for item in rotation_data if item['speed'] == 'DEAD']

        return {
            'period_days': days,
            'products': rotation_data,
            'top_rotation': top_rotation,
            'dead_stock_items': dead_stock_items,
            'summary': {
                'total_products': len(rotation_data),
                'total_stock_value': total_stock_value,
                'fast_moving_count': fast_moving,
                'medium_moving_count': medium_moving,
                'slow_moving_count': slow_moving,
                'dead_stock_count': dead_stock,
                'avg_rotation_rate': sum(item['rotation_rate'] for item in rotation_data) / len(rotation_data) if rotation_data else 0
            }
        }

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
            revenue=Sum('monto_total')
        ).order_by('-revenue')

        result = []
        for item in performance:
            avg_ticket = (item['revenue'] / item['services_count']) if item['services_count'] > 0 else 0

            # Obtener comisiones del empleado en el período
            # TODO: Implementar cuando el modelo Comision esté disponible
            # from apps.empleados.models import Comision
            # comisiones_total = Comision.objects.filter(
            #     empleado_id=item['profesional__id'],
            #     turno__fecha_hora_inicio__date__gte=start_date,
            #     turno__fecha_hora_inicio__date__lte=end_date
            # ).aggregate(total=Sum('monto'))['total'] or 0
            comisiones_total = 0

            result.append({
                'employee_id': item['profesional__id'],
                'employee_name': f"{item['profesional__first_name']} {item['profesional__last_name']}",
                'services_count': item['services_count'],
                'revenue_generated': float(item['revenue'] or 0),
                'average_ticket': float(avg_ticket),
                'commissions_earned': float(comisiones_total)
            })

        return result

    @staticmethod
    def get_workload_distribution(sucursal_id=None, start_date=None, end_date=None, group_by='weekday'):
        """
        Calcula distribución de carga de trabajo por empleado
        group_by: 'weekday' o 'time_slot'
        """
        turnos_qs = Turno.objects.filter(
            estado='COMPLETADO',
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        if group_by == 'weekday':
            # Agrupar por día de la semana
            workload = turnos_qs.annotate(
                weekday=ExtractWeekDay('fecha_hora_inicio')
            ).values(
                'weekday',
                'profesional__id',
                'profesional__first_name',
                'profesional__last_name'
            ).annotate(
                count=Count('id')
            ).order_by('weekday', 'profesional__id')

            days_map = {
                1: 'Sunday',
                2: 'Monday',
                3: 'Tuesday',
                4: 'Wednesday',
                5: 'Thursday',
                6: 'Friday',
                7: 'Saturday'
            }

            # Organizar por día
            result_by_day = {}
            employee_names = {}

            for item in workload:
                day_name = days_map.get(item['weekday'], 'Unknown')
                employee_id = item['profesional__id']
                employee_name = f"{item['profesional__first_name']} {item['profesional__last_name']}"

                if day_name not in result_by_day:
                    result_by_day[day_name] = {'day': day_name}

                result_by_day[day_name][employee_name] = item['count']
                employee_names[employee_id] = employee_name

            # Asegurar que todos los empleados estén en todos los días
            all_employees = list(employee_names.values())
            for day_data in result_by_day.values():
                for employee_name in all_employees:
                    if employee_name not in day_data:
                        day_data[employee_name] = 0

            # Ordenar días
            ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            result = [result_by_day[day] for day in ordered_days if day in result_by_day]

        else:  # group_by == 'time_slot'
            # Agrupar por franja horaria
            time_slots = {
                'Mañana': (6, 12),
                'Tarde': (12, 18),
                'Noche': (18, 24)
            }

            result = []
            employee_names = {}

            for slot_name, (start_hour, end_hour) in time_slots.items():
                slot_data = {'time_slot': slot_name}

                slot_turnos = turnos_qs.filter(
                    fecha_hora_inicio__hour__gte=start_hour,
                    fecha_hora_inicio__hour__lt=end_hour
                ).values(
                    'profesional__id',
                    'profesional__first_name',
                    'profesional__last_name'
                ).annotate(
                    count=Count('id')
                )

                for item in slot_turnos:
                    employee_name = f"{item['profesional__first_name']} {item['profesional__last_name']}"
                    slot_data[employee_name] = item['count']
                    employee_names[item['profesional__id']] = employee_name

                # Asegurar que todos los empleados estén en todas las franjas
                all_employees = list(employee_names.values())
                for employee_name in all_employees:
                    if employee_name not in slot_data:
                        slot_data[employee_name] = 0

                result.append(slot_data)

        return result

    # ========== OCCUPANCY ANALYTICS ==========

    @staticmethod
    def get_occupancy_by_day_of_week(sucursal_id=None, start_date=None, end_date=None):
        """
        Calcula ocupación por día de la semana con porcentaje
        """
        turnos_qs = Turno.objects.filter(
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        # Calcular días totales en el rango para capacidad teórica
        total_days = (end_date - start_date).days + 1
        weeks = total_days / 7

        # Capacidad teórica: 10 turnos por día (simplificado)
        capacity_per_day = 10 * weeks

        # Contar turnos por día de semana
        by_weekday = turnos_qs.annotate(
            weekday=ExtractWeekDay('fecha_hora_inicio')
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

        result = []
        for day_num, day_name in days_map.items():
            # Buscar datos para este día
            day_data = next((item for item in by_weekday if item['weekday'] == day_num), None)

            if day_data:
                completed_count = day_data['completed']
                occupancy_percentage = (completed_count / capacity_per_day * 100) if capacity_per_day > 0 else 0
            else:
                completed_count = 0
                occupancy_percentage = 0

            result.append({
                'day': day_name,
                'count': completed_count,
                'occupancy_percentage': round(min(occupancy_percentage, 100), 1)  # Cap at 100%
            })

        return result

    @staticmethod
    def get_occupancy_heatmap(sucursal_id=None, start_date=None, end_date=None):
        """
        Calcula ocupación por día de semana y franja horaria
        Franjas: Morning (6-12), Afternoon (12-18), Evening (18-24)
        """
        from datetime import time

        turnos_qs = Turno.objects.filter(
            fecha_hora_inicio__date__gte=start_date,
            fecha_hora_inicio__date__lte=end_date,
            estado__in=['COMPLETADO', 'CONFIRMADO']
        )

        if sucursal_id:
            turnos_qs = turnos_qs.filter(sucursal_id=sucursal_id)

        # Definir franjas horarias
        time_slots = {
            'morning': (6, 12),
            'afternoon': (12, 18),
            'evening': (18, 24)
        }

        days_map = {
            1: 'Sunday',
            2: 'Monday',
            3: 'Tuesday',
            4: 'Wednesday',
            5: 'Thursday',
            6: 'Friday',
            7: 'Saturday'
        }

        # Calcular total de días en el rango para capacidad teórica
        total_days = (end_date - start_date).days + 1
        weeks = total_days / 7

        # Capacidad teórica: 8 turnos por hora, asumiendo 1 empleado
        # Esto es simplificado - en producción debería considerar empleados disponibles
        capacity_per_slot = 8 * 6 * weeks  # 8 turnos/hora * 6 horas por franja * semanas

        result = []
        for day_num, day_name in days_map.items():
            day_data = {'day': day_name}

            for slot_name, (start_hour, end_hour) in time_slots.items():
                # Contar turnos en esta franja
                count = turnos_qs.filter(
                    fecha_hora_inicio__iso_week_day=day_num,
                    fecha_hora_inicio__hour__gte=start_hour,
                    fecha_hora_inicio__hour__lt=end_hour
                ).count()

                # Calcular porcentaje de ocupación
                occupancy_percentage = (count / capacity_per_slot * 100) if capacity_per_slot > 0 else 0
                day_data[slot_name] = round(min(occupancy_percentage, 100), 1)  # Cap at 100%

            result.append(day_data)

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

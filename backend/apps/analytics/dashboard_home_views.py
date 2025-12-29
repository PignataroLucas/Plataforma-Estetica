"""
Views para Dashboard Home (Página Principal)
Endpoints específicos para el dashboard principal de la plataforma
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from datetime import datetime, timedelta

from apps.turnos.models import Turno
from apps.finanzas.models import Transaction
from apps.clientes.models import Cliente
from apps.inventario.models import Producto


class DashboardHomeView(APIView):
    """
    GET /api/dashboard/home/

    Dashboard principal con resumen del día actual
    Muestra:
    - Resumen de citas del día
    - Ingresos del día
    - KPIs rápidos
    - Alertas importantes
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sucursal = request.user.sucursal
        today = timezone.now().date()
        now = timezone.now()

        # Determinar si el usuario puede ver datos financieros
        user_role = request.user.rol
        can_view_financials = user_role in ['ADMIN', 'MANAGER']

        # ========== CITAS DEL DÍA ==========
        # Empleados básicos solo ven sus propias citas
        if user_role == 'EMPLEADO':
            turnos_hoy = Turno.objects.filter(
                sucursal=sucursal,
                fecha_hora_inicio__date=today,
                profesional=request.user
            )
        else:
            turnos_hoy = Turno.objects.filter(
                sucursal=sucursal,
                fecha_hora_inicio__date=today
            )

        # Contar por estado
        citas_pendientes = turnos_hoy.filter(estado='PENDIENTE').count()
        citas_confirmadas = turnos_hoy.filter(estado='CONFIRMADO').count()
        citas_completadas = turnos_hoy.filter(estado='COMPLETADO').count()
        citas_canceladas = turnos_hoy.filter(estado='CANCELADO').count()
        citas_no_show = turnos_hoy.filter(estado='NO_SHOW').count()

        # Próximas 3 citas de hoy
        proximas_citas = turnos_hoy.filter(
            fecha_hora_inicio__gte=now,
            estado__in=['PENDIENTE', 'CONFIRMADO']
        ).select_related('cliente', 'servicio', 'profesional').order_by('fecha_hora_inicio')[:3]

        proximas_citas_data = [{
            'id': turno.id,
            'hora': turno.fecha_hora_inicio.strftime('%H:%M'),
            'cliente': f"{turno.cliente.nombre} {turno.cliente.apellido}",
            'servicio': turno.servicio.nombre if turno.servicio else 'Sin servicio',
            'profesional': f"{turno.profesional.nombre} {turno.profesional.apellido}" if turno.profesional else 'Sin asignar',
            'estado': turno.estado,
        } for turno in proximas_citas]

        # ========== INGRESOS DEL DÍA (solo Admin/Manager) ==========
        if can_view_financials:
            ingresos_hoy = Transaction.objects.filter(
                branch=sucursal,
                date=today,
                type__in=['INCOME_SERVICE', 'INCOME_PRODUCT', 'INCOME_OTHER']
            ).aggregate(total=Sum('amount'))['total'] or 0

            gastos_hoy = Transaction.objects.filter(
                branch=sucursal,
                date=today,
                type='EXPENSE'
            ).aggregate(total=Sum('amount'))['total'] or 0

            # ========== INGRESOS DEL MES ==========
            inicio_mes = today.replace(day=1)

            ingresos_mes = Transaction.objects.filter(
                branch=sucursal,
                date__gte=inicio_mes,
                date__lte=today,
                type__in=['INCOME_SERVICE', 'INCOME_PRODUCT', 'INCOME_OTHER']
            ).aggregate(total=Sum('amount'))['total'] or 0

            gastos_mes = Transaction.objects.filter(
                branch=sucursal,
                date__gte=inicio_mes,
                date__lte=today,
                type='EXPENSE'
            ).aggregate(total=Sum('amount'))['total'] or 0
        else:
            ingresos_hoy = 0
            gastos_hoy = 0
            ingresos_mes = 0
            gastos_mes = 0

        # ========== CLIENTES ATENDIDOS HOY ==========
        clientes_hoy = turnos_hoy.filter(
            estado='COMPLETADO'
        ).values('cliente').distinct().count()

        # ========== ALERTAS ==========
        alertas = []

        # Alertas solo para Admin/Manager
        if can_view_financials:
            # 1. Stock bajo
            productos_stock_bajo = Producto.objects.filter(
                sucursal=sucursal,
                activo=True,
                stock_actual__lte=F('stock_minimo')
            ).count()

            if productos_stock_bajo > 0:
                alertas.append({
                    'tipo': 'stock_bajo',
                    'severidad': 'warning',
                    'titulo': 'Stock bajo',
                    'mensaje': f'{productos_stock_bajo} producto(s) con stock bajo',
                    'count': productos_stock_bajo
                })

            # 3. Clientes en riesgo (no vuelven hace 60+ días)
            hace_60_dias = today - timedelta(days=60)
            clientes_en_riesgo = Cliente.objects.filter(
                centro_estetica=sucursal.centro_estetica
            ).annotate(
                visitas_recientes=Count('turnos', filter=Q(
                    turnos__sucursal=sucursal,
                    turnos__estado='COMPLETADO',
                    turnos__fecha_hora_inicio__date__gte=hace_60_dias
                ))
            ).filter(visitas_recientes=0).count()

            if clientes_en_riesgo > 5:  # Solo alertar si hay más de 5
                alertas.append({
                    'tipo': 'clientes_riesgo',
                    'severidad': 'warning',
                    'titulo': 'Clientes inactivos',
                    'mensaje': f'{clientes_en_riesgo} clientes sin visitas en 60+ días',
                    'count': clientes_en_riesgo
                })

            # 4. Turnos pendientes de pago
            turnos_pendientes_pago = Turno.objects.filter(
                sucursal=sucursal,
                estado='COMPLETADO',
                estado_pago='PENDIENTE'
            ).count()

            if turnos_pendientes_pago > 0:
                alertas.append({
                    'tipo': 'pagos_pendientes',
                    'severidad': 'error',
                    'titulo': 'Pagos pendientes',
                    'mensaje': f'{turnos_pendientes_pago} servicio(s) completados sin pago',
                    'count': turnos_pendientes_pago
                })

        # 2. Citas sin confirmar (para todos los roles)
        citas_sin_confirmar = turnos_hoy.filter(
            estado='PENDIENTE',
            fecha_hora_inicio__gte=now
        ).count()

        if citas_sin_confirmar > 0:
            mensaje = f'{citas_sin_confirmar} cita(s) sin confirmar para hoy'
            if user_role == 'EMPLEADO':
                mensaje = f'Tienes {citas_sin_confirmar} cita(s) sin confirmar'

            alertas.append({
                'tipo': 'citas_pendientes',
                'severidad': 'info',
                'titulo': 'Citas pendientes',
                'mensaje': mensaje,
                'count': citas_sin_confirmar
            })

        # ========== RESPONSE ==========
        return Response({
            'fecha': today.strftime('%Y-%m-%d'),
            'can_view_financials': can_view_financials,
            'user_role': user_role,
            'citas_hoy': {
                'total': turnos_hoy.count(),
                'pendientes': citas_pendientes,
                'confirmadas': citas_confirmadas,
                'completadas': citas_completadas,
                'canceladas': citas_canceladas,
                'no_show': citas_no_show,
                'proximas': proximas_citas_data
            },
            'ingresos_hoy': {
                'ingresos': float(ingresos_hoy),
                'gastos': float(gastos_hoy),
                'neto': float(ingresos_hoy - gastos_hoy)
            },
            'ingresos_mes': {
                'ingresos': float(ingresos_mes),
                'gastos': float(gastos_mes),
                'neto': float(ingresos_mes - gastos_mes)
            },
            'clientes_atendidos_hoy': clientes_hoy,
            'alertas': alertas
        })


class DashboardStatsView(APIView):
    """
    GET /api/dashboard/stats/

    Estadísticas rápidas para widgets del dashboard
    - Clientes totales
    - Servicios del mes
    - Productos vendidos
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sucursal = request.user.sucursal
        today = timezone.now().date()
        inicio_mes = today.replace(day=1)

        # Clientes totales del centro
        total_clientes = Cliente.objects.filter(
            centro_estetica=sucursal.centro_estetica
        ).count()

        # Servicios del mes
        servicios_mes = Turno.objects.filter(
            sucursal=sucursal,
            estado='COMPLETADO',
            fecha_hora_inicio__date__gte=inicio_mes,
            fecha_hora_inicio__date__lte=today
        ).count()

        # Productos con stock crítico
        productos_criticos = Producto.objects.filter(
            sucursal=sucursal,
            activo=True,
            stock_actual__lte=F('stock_minimo')
        ).count()

        # Ocupación de hoy
        total_horas_dia = 8  # Asumimos 8 horas laborales
        turnos_hoy = Turno.objects.filter(
            sucursal=sucursal,
            fecha_hora_inicio__date=today,
            estado__in=['CONFIRMADO', 'COMPLETADO']
        ).count()

        # Estimación simple de ocupación (cada turno = 1 hora aprox)
        ocupacion_porcentaje = min(100, (turnos_hoy / total_horas_dia) * 100) if turnos_hoy > 0 else 0

        return Response({
            'total_clientes': total_clientes,
            'servicios_mes': servicios_mes,
            'productos_criticos': productos_criticos,
            'ocupacion_hoy': round(ocupacion_porcentaje, 1)
        })

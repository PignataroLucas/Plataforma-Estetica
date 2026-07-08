"""
Views para Dashboard Home (Página Principal)
Endpoints específicos para el dashboard principal de la plataforma
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Max, Q, F
from datetime import date, datetime, timedelta

from apps.turnos.models import Turno
from apps.finanzas.models import Transaction
from apps.clientes.models import Cliente
from apps.inventario.models import Producto


def _proximo_cumpleanos(fecha_nac, hoy):
    """
    Calcula datos del próximo cumpleaños de un cliente.

    Devuelve (dias_para_cumple, edad_a_cumplir, cumple_hoy).
    Maneja el 29/02: en años no bisiestos se toma el 28/02.
    """
    def _cumple_en(anio):
        try:
            return date(anio, fecha_nac.month, fecha_nac.day)
        except ValueError:
            # 29/02 en año no bisiesto -> 28/02
            return date(anio, fecha_nac.month, 28)

    proximo = _cumple_en(hoy.year)
    if proximo < hoy:
        proximo = _cumple_en(hoy.year + 1)

    dias_para_cumple = (proximo - hoy).days
    edad_a_cumplir = proximo.year - fecha_nac.year
    return dias_para_cumple, edad_a_cumplir, dias_para_cumple == 0


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
            'hora': timezone.localtime(turno.fecha_hora_inicio).strftime('%H:%M'),
            'cliente': f"{turno.cliente.nombre} {turno.cliente.apellido}",
            'servicio': turno.servicio.nombre if turno.servicio else 'Sin servicio',
            'profesional': turno.profesional.get_full_name() if turno.profesional else 'Sin asignar',
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

        # ========== CUMPLEAÑOS PRÓXIMOS (solo Admin/Manager) ==========
        # Clientes que cumplen años dentro de los próximos 7 días (incluye hoy).
        # Se incluye el LTV para resaltar clientes valiosos sin abrir el detalle.
        cumpleanos = []
        if can_view_financials:
            from apps.analytics.utils import AnalyticsCalculator

            VENTANA_DIAS = 7
            clientes_con_cumple = Cliente.objects.filter(
                centro_estetica=sucursal.centro_estetica,
                activo=True,
                fecha_nacimiento__isnull=False
            )

            for cliente in clientes_con_cumple:
                dias, edad, cumple_hoy = _proximo_cumpleanos(
                    cliente.fecha_nacimiento, today
                )
                if dias <= VENTANA_DIAS:
                    cumpleanos.append({
                        'cliente_id': cliente.id,
                        'nombre_completo': cliente.nombre_completo,
                        'telefono': cliente.telefono,
                        'fecha_nacimiento': cliente.fecha_nacimiento.isoformat(),
                        'dia_mes': cliente.fecha_nacimiento.strftime('%d/%m'),
                        'dias_para_cumple': dias,
                        'cumple_hoy': cumple_hoy,
                        'edad_a_cumplir': edad,
                        'lifetime_value': AnalyticsCalculator.get_client_lifetime_value(cliente.id),
                    })

            # Más cercanos primero; a igualdad de días, el más valioso arriba
            cumpleanos.sort(key=lambda c: (c['dias_para_cumple'], -c['lifetime_value']))

        # ========== RESPONSE ==========
        return Response({
            'fecha': today.strftime('%Y-%m-%d'),
            'can_view_financials': can_view_financials,
            'user_role': user_role,
            'cumpleanos': cumpleanos,
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


class DashboardAlertaDetailView(APIView):
    """
    GET /api/dashboard/alertas/<tipo>/

    Detalle de una alerta del dashboard para mostrar en el popup.
    Tipos soportados: stock_bajo, clientes_riesgo, pagos_pendientes, citas_pendientes

    Cada queryset replica exactamente el filtro usado en DashboardHomeView
    para que el detalle coincida con el count de la alerta.
    """
    permission_classes = [IsAuthenticated]

    # Máximo de clientes inactivos devueltos (puede ser una lista muy larga)
    MAX_CLIENTES_RIESGO = 100

    def get(self, request, tipo):
        sucursal = request.user.sucursal
        today = timezone.now().date()
        now = timezone.now()
        user_role = request.user.rol
        can_view_financials = user_role in ['ADMIN', 'MANAGER']

        if tipo == 'citas_pendientes':
            turnos = Turno.objects.filter(
                sucursal=sucursal,
                fecha_hora_inicio__date=today,
                fecha_hora_inicio__gte=now,
                estado='PENDIENTE'
            )
            if user_role == 'EMPLEADO':
                turnos = turnos.filter(profesional=request.user)

            turnos = turnos.select_related(
                'cliente', 'servicio', 'profesional'
            ).order_by('fecha_hora_inicio')

            items = [{
                'id': turno.id,
                'hora': timezone.localtime(turno.fecha_hora_inicio).strftime('%H:%M'),
                'cliente': turno.cliente.nombre_completo,
                'telefono': turno.cliente.telefono,
                'servicio': turno.servicio.nombre if turno.servicio else 'Sin servicio',
                'profesional': turno.profesional.get_full_name() if turno.profesional else 'Sin asignar',
            } for turno in turnos]

            return Response({'tipo': tipo, 'count': len(items), 'items': items})

        # El resto de las alertas son financieras: solo Admin/Manager
        if not can_view_financials:
            return Response(
                {'detail': 'No tiene permisos para ver el detalle de esta alerta'},
                status=403
            )

        if tipo == 'stock_bajo':
            productos = Producto.objects.filter(
                sucursal=sucursal,
                activo=True,
                stock_actual__lte=F('stock_minimo')
            ).select_related('categoria').order_by('stock_actual', 'nombre')

            items = [{
                'id': producto.id,
                'nombre': producto.nombre,
                'sku': producto.sku,
                'categoria': producto.categoria.nombre if producto.categoria else None,
                'stock_actual': float(producto.stock_actual),
                'stock_minimo': float(producto.stock_minimo),
                'unidad_medida': producto.unidad_medida,
            } for producto in productos]

            return Response({'tipo': tipo, 'count': len(items), 'items': items})

        if tipo == 'pagos_pendientes':
            turnos = Turno.objects.filter(
                sucursal=sucursal,
                estado='COMPLETADO',
                estado_pago='PENDIENTE'
            ).select_related(
                'cliente', 'servicio', 'profesional'
            ).order_by('-fecha_hora_inicio')

            items = [{
                'id': turno.id,
                'fecha': timezone.localtime(turno.fecha_hora_inicio).strftime('%d/%m/%Y %H:%M'),
                'cliente': turno.cliente.nombre_completo,
                'telefono': turno.cliente.telefono,
                'servicio': turno.servicio.nombre if turno.servicio else 'Sin servicio',
                'profesional': turno.profesional.get_full_name() if turno.profesional else 'Sin asignar',
                'monto_total': float(turno.monto_total or 0),
            } for turno in turnos]

            return Response({'tipo': tipo, 'count': len(items), 'items': items})

        if tipo == 'clientes_riesgo':
            hace_60_dias = today - timedelta(days=60)
            # "ultima_visita_completada" y no "ultima_visita": el modelo Cliente
            # ya tiene un campo con ese nombre y la anotación no puede pisarlo
            clientes = Cliente.objects.filter(
                centro_estetica=sucursal.centro_estetica
            ).annotate(
                visitas_recientes=Count('turnos', filter=Q(
                    turnos__sucursal=sucursal,
                    turnos__estado='COMPLETADO',
                    turnos__fecha_hora_inicio__date__gte=hace_60_dias
                )),
                ultima_visita_completada=Max('turnos__fecha_hora_inicio', filter=Q(
                    turnos__sucursal=sucursal,
                    turnos__estado='COMPLETADO'
                ))
            ).filter(visitas_recientes=0).order_by(
                F('ultima_visita_completada').desc(nulls_last=True)
            )

            total = clientes.count()
            items = []
            for cliente in clientes[:self.MAX_CLIENTES_RIESGO]:
                ultima_visita = cliente.ultima_visita_completada
                items.append({
                    'id': cliente.id,
                    'nombre_completo': cliente.nombre_completo,
                    'telefono': cliente.telefono,
                    'ultima_visita': timezone.localtime(ultima_visita).strftime('%d/%m/%Y') if ultima_visita else None,
                    'dias_sin_visita': (today - timezone.localtime(ultima_visita).date()).days if ultima_visita else None,
                })

            return Response({'tipo': tipo, 'count': total, 'items': items})

        return Response({'detail': f'Tipo de alerta desconocido: {tipo}'}, status=404)

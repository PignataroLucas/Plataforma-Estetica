from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from apps.finanzas.models import Transaction, TransactionCategory
from apps.turnos.models import Turno
from apps.inventario.models import Producto, MovimientoInventario
from apps.clientes.models import Cliente
from .models import CierreCaja
from .serializers import (
    TransaccionMiCajaSerializer,
    CobrarTurnoSerializer,
    VenderProductoSerializer,
    CierreCajaSerializer,
    CierreCajaCreateSerializer,
    VentaUnificadaSerializer
)
from .permissions import CanAccessMiCaja, CanViewTransaction, CanCobrarTurno


class MiCajaViewSet(viewsets.ViewSet):
    """
    ViewSet for Mi Caja - Employee cash register system
    Accessible by all authenticated users
    """
    permission_classes = [CanAccessMiCaja]

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_user_agent(self, request):
        """Get user agent from request"""
        return request.META.get('HTTP_USER_AGENT', '')

    @action(detail=False, methods=['post'], url_path='cobrar-turno')
    def cobrar_turno(self, request):
        """
        Register payment for a completed appointment
        """
        serializer = CobrarTurnoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        turno_id = serializer.validated_data['turno_id']
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        notas = serializer.validated_data.get('notas', '')

        try:
            turno = Turno.objects.select_related(
                'servicio', 'cliente', 'profesional', 'sucursal'
            ).get(id=turno_id)
        except Turno.DoesNotExist:
            return Response(
                {'error': 'Turno no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar permisos: empleado solo puede cobrar sus turnos
        if request.user.rol == 'EMPLEADO' and turno.profesional != request.user:
            return Response(
                {'error': 'Solo puedes cobrar tus propios turnos'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener categoría de servicios (system category)
        try:
            categoria_servicios = TransactionCategory.objects.get(
                branch=turno.sucursal,
                name='Servicios',
                type='INCOME',
                is_system_category=True
            )
        except TransactionCategory.DoesNotExist:
            return Response(
                {'error': 'Categoría de Servicios no configurada'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Crear transacción con atomic para prevenir race conditions
        with transaction.atomic():
            # Crear transacción de ingreso
            transaccion = Transaction.objects.create(
                branch=turno.sucursal,
                category=categoria_servicios,
                client=turno.cliente,
                appointment=turno,
                type='INCOME_SERVICE',
                amount=amount,
                payment_method=payment_method,
                date=timezone.now().date(),
                description=f"Servicio: {turno.servicio.nombre} - {turno.cliente.nombre} {turno.cliente.apellido}",
                notes=notas,
                auto_generated=False,
                registered_by=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=self.get_user_agent(request)
            )

            # Actualizar estado de pago del turno
            turno.estado_pago = 'PAGADO'
            turno.save(update_fields=['estado_pago'])

        # Serializar respuesta
        serializer = TransaccionMiCajaSerializer(transaccion)

        return Response({
            'success': True,
            'message': f'Cobro registrado exitosamente: ${amount}',
            'transaction': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='vender-producto')
    def vender_producto(self, request):
        """
        Sell a product and update inventory
        """
        serializer = VenderProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        producto_id = serializer.validated_data['producto_id']
        cantidad = serializer.validated_data['cantidad']
        cliente_id = serializer.validated_data['cliente_id']
        payment_method = serializer.validated_data['payment_method']
        descuento_porcentaje = serializer.validated_data.get('descuento_porcentaje', Decimal('0.00'))

        try:
            producto = Producto.objects.select_related('sucursal').get(id=producto_id)
            cliente = Cliente.objects.get(id=cliente_id)
        except (Producto.DoesNotExist, Cliente.DoesNotExist) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calcular montos
        subtotal = producto.precio_venta * cantidad
        descuento_monto = (subtotal * descuento_porcentaje) / 100
        total = subtotal - descuento_monto

        # Obtener categoría de productos (system category)
        try:
            categoria_productos = TransactionCategory.objects.get(
                branch=producto.sucursal,
                name='Productos',
                type='INCOME',
                is_system_category=True
            )
        except TransactionCategory.DoesNotExist:
            return Response(
                {'error': 'Categoría de Productos no configurada'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Atomic transaction para consistencia
        with transaction.atomic():
            # Guardar stock anterior
            stock_anterior = producto.stock_actual

            # Reducir stock
            producto.stock_actual -= cantidad
            stock_nuevo = producto.stock_actual
            producto.save(update_fields=['stock_actual'])

            # Crear movimiento de inventario
            # NOTE: This will automatically trigger a signal that creates a Transaction
            movimiento = MovimientoInventario.objects.create(
                producto=producto,
                tipo='SALIDA',
                cantidad=cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_nuevo,
                precio_unitario=producto.precio_venta,
                usuario=request.user,
                notas=f"Venta a {cliente.nombre} {cliente.apellido}"
            )

            # Refresh to get the auto-created transaction from signal
            movimiento.refresh_from_db()

            # Update the auto-created transaction with additional details
            transaccion = movimiento.financial_transaction
            transaccion.client = cliente
            transaccion.payment_method = payment_method
            transaccion.category = categoria_productos
            transaccion.amount = total  # Update with discounted amount
            transaccion.description = f"Venta: {cantidad}x {producto.nombre} - {cliente.nombre} {cliente.apellido}"
            transaccion.notes = f"Subtotal: ${subtotal}, Descuento: {descuento_porcentaje}% (${descuento_monto})"
            transaccion.ip_address = self.get_client_ip(request)
            transaccion.user_agent = self.get_user_agent(request)
            transaccion.save()

        # Serializar respuesta
        serializer = TransaccionMiCajaSerializer(transaccion)

        return Response({
            'success': True,
            'message': f'Venta registrada: {cantidad}x {producto.nombre} - ${total}',
            'transaction': serializer.data,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'stock_restante': producto.stock_actual
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='mis-transacciones')
    def mis_transacciones(self, request):
        """
        Get transactions created by the current user
        """
        # Obtener parámetros
        fecha_str = request.query_params.get('fecha')
        payment_method = request.query_params.get('payment_method')

        # Fecha por defecto: hoy
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            fecha = timezone.now().date()

        # Filtrar transacciones
        queryset = Transaction.objects.filter(
            registered_by=request.user,
            date=fecha
        ).select_related('client', 'appointment', 'product', 'registered_by')

        # Filtrar por método de pago si se especifica
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Ordenar por hora de creación
        queryset = queryset.order_by('created_at')

        # Calcular resumen
        total = sum(t.amount for t in queryset if t.is_income)
        por_metodo = {}
        for t in queryset:
            if t.is_income:
                metodo = t.payment_method
                por_metodo[metodo] = por_metodo.get(metodo, Decimal('0.00')) + t.amount

        # Serializar
        serializer = TransaccionMiCajaSerializer(queryset, many=True)

        return Response({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'empleado': {
                'id': request.user.id,
                'nombre': request.user.get_full_name()
            },
            'resumen': {
                'total': float(total),
                'cantidad_transacciones': queryset.count(),
                'por_metodo': {k: float(v) for k, v in por_metodo.items()}
            },
            'transacciones': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='cierre-caja')
    def cierre_caja(self, request):
        """
        Create a cash register closing record
        """
        serializer = CierreCajaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fecha = serializer.validated_data['fecha']
        efectivo_contado = serializer.validated_data['efectivo_contado']
        notas = serializer.validated_data.get('notas', '')

        # Verificar que no exista cierre para ese día
        if CierreCaja.objects.filter(empleado=request.user, fecha=fecha).exists():
            return Response(
                {'error': f'Ya existe un cierre de caja para el {fecha.strftime("%d/%m/%Y")}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcular totales del sistema
        transacciones = Transaction.objects.filter(
            registered_by=request.user,
            date=fecha
        )

        total_sistema = sum(t.amount for t in transacciones if t.is_income)

        # Desglose por método de pago
        desglose_metodos = {}
        for t in transacciones:
            if t.is_income:
                metodo = t.payment_method
                desglose_metodos[metodo] = desglose_metodos.get(metodo, 0) + float(t.amount)

        # Calcular diferencia
        efectivo_sistema = desglose_metodos.get('CASH', 0)
        diferencia = float(efectivo_contado) - efectivo_sistema

        # Crear cierre de caja
        cierre = CierreCaja.objects.create(
            empleado=request.user,
            sucursal=request.user.sucursal,
            fecha=fecha,
            total_sistema=total_sistema,
            efectivo_contado=efectivo_contado,
            diferencia=Decimal(str(diferencia)),
            desglose_metodos=desglose_metodos,
            notas=notas
        )

        # Serializar respuesta
        serializer = CierreCajaSerializer(cierre)

        return Response({
            'success': True,
            'message': 'Cierre de caja registrado exitosamente',
            'cierre': serializer.data,
            'alerta': cierre.diferencia_significativa
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='turnos-pendientes-cobro')
    def turnos_pendientes_cobro(self, request):
        """
        Get completed appointments without payment registered
        """
        # Obtener turnos completados del usuario sin pago
        turnos = Turno.objects.filter(
            profesional=request.user,
            estado='COMPLETADO',
            estado_pago__in=['PENDIENTE', 'CON_SENA']
        ).select_related('cliente', 'servicio').order_by('fecha_hora_inicio')

        # Filtrar los que no tienen transacción de pago
        turnos_pendientes = []
        for turno in turnos:
            if not turno.transactions.filter(type='INCOME_SERVICE').exists():
                turnos_pendientes.append({
                    'id': turno.id,
                    'cliente': f"{turno.cliente.nombre} {turno.cliente.apellido}",
                    'servicio': turno.servicio.nombre,
                    'monto': float(turno.servicio.precio),
                    'fecha': turno.fecha_hora_inicio.strftime('%Y-%m-%d'),
                    'hora': turno.fecha_hora_inicio.strftime('%H:%M'),
                    'estado_pago': turno.estado_pago
                })

        return Response({
            'count': len(turnos_pendientes),
            'turnos': turnos_pendientes
        })

    @action(detail=False, methods=['post'], url_path='venta-unificada')
    def venta_unificada(self, request):
        """
        Register a unified sale with multiple items (products and/or services)
        """
        serializer = VentaUnificadaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data['items']
        cliente_id = serializer.validated_data['cliente_id']
        payment_method = serializer.validated_data['payment_method']
        notas = serializer.validated_data.get('notas', '')

        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        transacciones_creadas = []
        productos_actualizados = []

        # Process all items in a single atomic transaction
        with transaction.atomic():
            for item_data in items:
                tipo = item_data['tipo']

                if tipo == 'producto':
                    # Process product sale
                    producto_id = item_data['producto_id']
                    cantidad = item_data['cantidad']
                    descuento_porcentaje = item_data.get('descuento_porcentaje', Decimal('0.00'))

                    producto = Producto.objects.select_related('sucursal').get(id=producto_id)

                    # Calculate amounts
                    subtotal = producto.precio_venta * cantidad
                    descuento_monto = (subtotal * descuento_porcentaje) / 100
                    total = subtotal - descuento_monto

                    # Get product income category
                    categoria_productos = TransactionCategory.objects.get(
                        branch=producto.sucursal,
                        name='Productos',
                        type='INCOME',
                        is_system_category=True
                    )

                    # Save previous stock
                    stock_anterior = producto.stock_actual

                    # Reduce stock
                    producto.stock_actual -= cantidad
                    stock_nuevo = producto.stock_actual
                    producto.save(update_fields=['stock_actual'])

                    # Create inventory movement
                    movimiento = MovimientoInventario.objects.create(
                        producto=producto,
                        tipo='SALIDA',
                        cantidad=cantidad,
                        stock_anterior=stock_anterior,
                        stock_nuevo=stock_nuevo,
                        precio_unitario=producto.precio_venta,
                        usuario=request.user,
                        notas=f"Venta a {cliente.nombre} {cliente.apellido} - {notas}" if notas else f"Venta a {cliente.nombre} {cliente.apellido}"
                    )

                    # Refresh to get auto-created transaction
                    movimiento.refresh_from_db()

                    # Update auto-created transaction
                    transaccion = movimiento.financial_transaction
                    transaccion.client = cliente
                    transaccion.payment_method = payment_method
                    transaccion.category = categoria_productos
                    transaccion.amount = total
                    transaccion.description = f"Venta: {cantidad}x {producto.nombre}"
                    if descuento_porcentaje > 0:
                        transaccion.notes = f"Subtotal: ${subtotal}, Descuento: {descuento_porcentaje}% (${descuento_monto})"
                    transaccion.ip_address = self.get_client_ip(request)
                    transaccion.user_agent = self.get_user_agent(request)
                    transaccion.save()

                    transacciones_creadas.append(transaccion)
                    productos_actualizados.append({
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'stock_restante': producto.stock_actual
                    })

                elif tipo == 'servicio':
                    # Process service payment
                    turno_id = item_data['turno_id']

                    turno = Turno.objects.select_related(
                        'servicio', 'cliente', 'profesional', 'sucursal'
                    ).get(id=turno_id)

                    # Get service income category
                    categoria_servicios = TransactionCategory.objects.get(
                        branch=turno.sucursal,
                        name='Servicios',
                        type='INCOME',
                        is_system_category=True
                    )

                    # Create income transaction
                    transaccion = Transaction.objects.create(
                        branch=turno.sucursal,
                        category=categoria_servicios,
                        client=cliente,  # Use the unified sale client
                        appointment=turno,
                        type='INCOME_SERVICE',
                        amount=turno.servicio.precio,
                        payment_method=payment_method,
                        date=timezone.now().date(),
                        description=f"Servicio: {turno.servicio.nombre}",
                        notes=notas,
                        auto_generated=False,
                        registered_by=request.user,
                        ip_address=self.get_client_ip(request),
                        user_agent=self.get_user_agent(request)
                    )

                    # Update appointment payment status
                    turno.estado_pago = 'PAGADO'
                    turno.save(update_fields=['estado_pago'])

                    transacciones_creadas.append(transaccion)

        # Serialize response
        transacciones_serializer = TransaccionMiCajaSerializer(transacciones_creadas, many=True)

        return Response({
            'success': True,
            'message': f'Venta registrada exitosamente: {len(transacciones_creadas)} item(s)',
            'transactions': transacciones_serializer.data,
            'productos_actualizados': productos_actualizados,
            'total_items': len(items),
            'total_monto': float(sum(t.amount for t in transacciones_creadas))
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='resumen-dia')
    def resumen_dia(self, request):
        """
        Get daily summary for current user
        """
        fecha_str = request.query_params.get('fecha')

        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha = timezone.now().date()
        else:
            fecha = timezone.now().date()

        # Obtener transacciones del día
        transacciones = Transaction.objects.filter(
            registered_by=request.user,
            date=fecha
        )

        # Calcular totales
        total_ingresos = sum(t.amount for t in transacciones if t.is_income)
        cantidad = transacciones.filter(type__startswith='INCOME').count()

        # Desglose por método
        por_metodo = {}
        for t in transacciones:
            if t.is_income:
                metodo = t.get_payment_method_display()
                por_metodo[metodo] = por_metodo.get(metodo, Decimal('0.00')) + t.amount

        # Verificar si hay cierre
        tiene_cierre = CierreCaja.objects.filter(
            empleado=request.user,
            fecha=fecha
        ).exists()

        return Response({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'total': float(total_ingresos),
            'cantidad_transacciones': cantidad,
            'por_metodo': {k: float(v) for k, v in por_metodo.items()},
            'tiene_cierre': tiene_cierre
        })

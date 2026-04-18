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
from apps.servicios.models import Servicio
from apps.clientes.models import Cliente
from .serializers import (
    TransaccionMiCajaSerializer,
    CierreCajaSerializer,
    CierreCajaCreateSerializer,
    VentaUnificadaSerializer,
    EditarTransaccionSerializer,
    EliminarTransaccionSerializer
)
from .models import CierreCaja, TransaccionEliminada
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

    @action(detail=False, methods=['get'], url_path='mis-transacciones')
    def mis_transacciones(self, request):
        """
        Get transactions created by the current user
        """
        fecha_str = request.query_params.get('fecha')
        payment_method = request.query_params.get('payment_method')

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

        queryset = Transaction.objects.filter(
            registered_by=request.user,
            date=fecha
        ).select_related('client', 'appointment', 'product', 'registered_by')

        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        queryset = queryset.order_by('created_at')

        total = sum(t.amount for t in queryset if t.is_income)
        por_metodo = {}
        for t in queryset:
            if t.is_income:
                metodo = t.payment_method
                por_metodo[metodo] = por_metodo.get(metodo, Decimal('0.00')) + t.amount

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

        if CierreCaja.objects.filter(empleado=request.user, fecha=fecha).exists():
            return Response(
                {'error': f'Ya existe un cierre de caja para el {fecha.strftime("%d/%m/%Y")}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transacciones = Transaction.objects.filter(
            registered_by=request.user,
            date=fecha
        )

        total_sistema = sum(t.amount for t in transacciones if t.is_income)

        desglose_metodos = {}
        for t in transacciones:
            if t.is_income:
                metodo = t.payment_method
                desglose_metodos[metodo] = desglose_metodos.get(metodo, 0) + float(t.amount)

        efectivo_sistema = desglose_metodos.get('CASH', 0)
        diferencia = float(efectivo_contado) - efectivo_sistema

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
        Get appointments ready to be charged
        """
        from django.db.models import Q

        now = timezone.now()

        turnos = Turno.objects.filter(
            sucursal=request.user.sucursal,
            estado_pago__in=['PENDIENTE', 'CON_SENA']
        ).filter(
            Q(estado='COMPLETADO') |
            Q(estado='CONFIRMADO', fecha_hora_fin__lt=now)
        ).select_related('cliente', 'servicio', 'profesional').order_by('fecha_hora_inicio')

        turnos_pendientes = []
        for turno in turnos:
            transacciones_servicio = turno.transactions.filter(type='INCOME_SERVICE')
            total_pagado = sum(t.amount for t in transacciones_servicio)
            monto_pendiente = float(turno.servicio.precio) - float(total_pagado)

            if monto_pendiente > 0:
                monto_sena_pagado = float(total_pagado) if turno.estado_pago == 'CON_SENA' else 0

                turnos_pendientes.append({
                    'id': turno.id,
                    'cliente': f"{turno.cliente.nombre} {turno.cliente.apellido}",
                    'servicio': turno.servicio.nombre,
                    'profesional': turno.profesional.get_full_name() if turno.profesional else 'Sin asignar',
                    'monto': monto_pendiente,
                    'monto_total': float(turno.servicio.precio),
                    'monto_sena': monto_sena_pagado,
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
        Register a unified sale with multiple items (products, services from turnos,
        or direct services without turno). Client is optional.
        """
        serializer = VentaUnificadaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items = serializer.validated_data['items']
        cliente_id = serializer.validated_data.get('cliente_id')
        payment_method = serializer.validated_data['payment_method']
        notas = serializer.validated_data.get('notas', '')

        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                return Response(
                    {'error': 'Cliente no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )

        transacciones_creadas = []
        productos_actualizados = []

        with transaction.atomic():
            for item_data in items:
                tipo = item_data['tipo']

                if tipo == 'producto':
                    transaccion, producto_info = self._procesar_producto(
                        item_data, cliente, payment_method, notas, request
                    )
                    transacciones_creadas.append(transaccion)
                    productos_actualizados.append(producto_info)

                elif tipo == 'servicio':
                    transaccion = self._procesar_servicio_turno(
                        item_data, cliente, payment_method, notas, request
                    )
                    transacciones_creadas.append(transaccion)

                elif tipo == 'servicio_directo':
                    transaccion = self._procesar_servicio_directo(
                        item_data, cliente, payment_method, notas, request
                    )
                    transacciones_creadas.append(transaccion)

        transacciones_serializer = TransaccionMiCajaSerializer(transacciones_creadas, many=True)

        return Response({
            'success': True,
            'message': f'Venta registrada exitosamente: {len(transacciones_creadas)} item(s)',
            'transactions': transacciones_serializer.data,
            'productos_actualizados': productos_actualizados,
            'total_items': len(items),
            'total_monto': float(sum(t.amount for t in transacciones_creadas))
        }, status=status.HTTP_201_CREATED)

    def _procesar_producto(self, item_data, cliente, payment_method, notas, request):
        """Process a product sale item"""
        producto_id = item_data['producto_id']
        cantidad = item_data['cantidad']
        descuento_porcentaje = item_data.get('descuento_porcentaje', Decimal('0.00'))
        precio_override = item_data.get('precio_unitario')

        producto = Producto.objects.select_related('sucursal').get(id=producto_id)

        precio_unitario = precio_override if precio_override else producto.precio_venta
        subtotal = precio_unitario * cantidad
        descuento_monto = (subtotal * descuento_porcentaje) / 100
        total = subtotal - descuento_monto

        categoria_productos = TransactionCategory.objects.get(
            branch=producto.sucursal,
            name='Productos',
            type='INCOME',
            is_system_category=True
        )

        stock_anterior = producto.stock_actual
        producto.stock_actual -= cantidad
        stock_nuevo = producto.stock_actual
        producto.save(update_fields=['stock_actual'])

        cliente_desc = f" - {cliente.nombre} {cliente.apellido}" if cliente else ""
        movimiento = MovimientoInventario.objects.create(
            producto=producto,
            tipo='SALIDA',
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            precio_unitario=precio_unitario,
            usuario=request.user,
            notas=f"Venta{cliente_desc} - {notas}" if notas else f"Venta{cliente_desc}"
        )

        movimiento.refresh_from_db()

        transaccion = movimiento.financial_transaction
        transaccion.client = cliente
        transaccion.payment_method = payment_method
        transaccion.category = categoria_productos
        transaccion.amount = total
        transaccion.description = f"Venta: {cantidad}x {producto.nombre}"
        notes_parts = []
        if precio_override and precio_override != producto.precio_venta:
            notes_parts.append(f"Precio modificado: ${precio_unitario} (catálogo: ${producto.precio_venta})")
        if descuento_porcentaje > 0:
            notes_parts.append(f"Subtotal: ${subtotal}, Descuento: {descuento_porcentaje}% (${descuento_monto})")
        if notes_parts:
            transaccion.notes = ". ".join(notes_parts)
        transaccion.ip_address = self.get_client_ip(request)
        transaccion.user_agent = self.get_user_agent(request)
        transaccion.save()

        producto_info = {
            'id': producto.id,
            'nombre': producto.nombre,
            'stock_restante': producto.stock_actual
        }

        return transaccion, producto_info

    def _procesar_servicio_turno(self, item_data, cliente, payment_method, notas, request):
        """Process a service payment from an existing turno"""
        turno_id = item_data['turno_id']
        precio_override = item_data.get('precio_unitario')
        descuento_porcentaje = item_data.get('descuento_porcentaje', Decimal('0.00'))

        turno = Turno.objects.select_related(
            'servicio', 'cliente', 'profesional', 'sucursal'
        ).get(id=turno_id)

        precio_catalogo = turno.servicio.precio
        if turno.estado_pago == 'CON_SENA' and turno.monto_sena:
            monto_pendiente_original = precio_catalogo - turno.monto_sena
            descripcion = f"Saldo de servicio: {turno.servicio.nombre} (Seña ya pagada: ${turno.monto_sena})"
        else:
            monto_pendiente_original = precio_catalogo
            descripcion = f"Servicio: {turno.servicio.nombre}"

        # If precio_unitario override provided, it represents the total to charge (pre-discount)
        monto_base = precio_override if precio_override else monto_pendiente_original

        # Apply discount if any
        if descuento_porcentaje > 0:
            descuento_monto = (monto_base * descuento_porcentaje) / 100
            monto_a_cobrar = monto_base - descuento_monto
            descripcion += f" (Descuento: {descuento_porcentaje}%)"
        else:
            monto_a_cobrar = monto_base

        categoria_servicios = TransactionCategory.objects.get(
            branch=turno.sucursal,
            name='Servicios',
            type='INCOME',
            is_system_category=True
        )

        # Use turno's client if no client specified in sale
        transaction_client = cliente if cliente else turno.cliente

        notes_parts = []
        if precio_override and precio_override != monto_pendiente_original:
            notes_parts.append(f"Importe modificado: ${precio_override} (estimado: ${monto_pendiente_original})")
        if notas:
            notes_parts.append(notas)
        final_notes = ". ".join(notes_parts) if notes_parts else notas

        transaccion = Transaction.objects.create(
            branch=turno.sucursal,
            category=categoria_servicios,
            client=transaction_client,
            appointment=turno,
            service=turno.servicio,
            type='INCOME_SERVICE',
            amount=monto_a_cobrar,
            payment_method=payment_method,
            date=timezone.now().date(),
            description=descripcion,
            notes=final_notes,
            auto_generated=False,
            registered_by=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=self.get_user_agent(request)
        )

        if turno.estado != 'COMPLETADO':
            turno.estado = 'COMPLETADO'
        turno.estado_pago = 'PAGADO'
        turno.save(update_fields=['estado', 'estado_pago'])

        return transaccion

    def _procesar_servicio_directo(self, item_data, cliente, payment_method, notas, request):
        """Process a direct service sale (without turno/appointment)"""
        servicio_id = item_data['servicio_id']
        precio_override = item_data.get('precio_unitario')
        descuento_porcentaje = item_data.get('descuento_porcentaje', Decimal('0.00'))

        servicio = Servicio.objects.select_related('sucursal').get(id=servicio_id)

        precio_unitario = precio_override if precio_override else servicio.precio
        descuento_monto = (precio_unitario * descuento_porcentaje) / 100
        monto_final = precio_unitario - descuento_monto

        categoria_servicios = TransactionCategory.objects.get(
            branch=servicio.sucursal,
            name='Servicios',
            type='INCOME',
            is_system_category=True
        )

        descripcion = f"Servicio directo: {servicio.nombre}"
        if cliente:
            descripcion += f" - {cliente.nombre} {cliente.apellido}"

        notes_parts = []
        if precio_override and precio_override != servicio.precio:
            notes_parts.append(f"Precio modificado: ${precio_unitario} (catálogo: ${servicio.precio})")
        if descuento_porcentaje > 0:
            notes_parts.append(f"Descuento: {descuento_porcentaje}% (${descuento_monto})")
        if notas:
            notes_parts.append(notas)

        transaccion = Transaction.objects.create(
            branch=servicio.sucursal,
            category=categoria_servicios,
            client=cliente,
            service=servicio,
            type='INCOME_SERVICE',
            amount=monto_final,
            payment_method=payment_method,
            date=timezone.now().date(),
            description=descripcion,
            notes=". ".join(notes_parts) if notes_parts else '',
            auto_generated=False,
            registered_by=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=self.get_user_agent(request)
        )

        return transaccion

    @action(detail=False, methods=['patch'], url_path='editar-transaccion')
    def editar_transaccion(self, request):
        """
        Edit an existing transaction from Mi Caja.
        Editable fields: amount, payment_method, notas, cliente_id.
        """
        serializer = EditarTransaccionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaccion_id = serializer.validated_data['transaccion_id']

        try:
            transaccion = Transaction.objects.select_related(
                'client', 'appointment', 'product', 'registered_by', 'inventory_movement'
            ).get(id=transaccion_id)
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transacción no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Permission check: own transaction or ADMIN/MANAGER
        if request.user.rol == 'EMPLEADO' and transaccion.registered_by != request.user:
            return Response(
                {'error': 'Solo puedes editar tus propias transacciones'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not transaccion.can_be_edited:
            return Response(
                {'error': 'No se pueden editar transacciones con más de 30 días'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_fields = []

        if 'amount' in serializer.validated_data:
            transaccion.amount = serializer.validated_data['amount']
            updated_fields.append('amount')

        if 'payment_method' in serializer.validated_data:
            transaccion.payment_method = serializer.validated_data['payment_method']
            updated_fields.append('payment_method')

        if 'notas' in serializer.validated_data:
            transaccion.notes = serializer.validated_data['notas']
            updated_fields.append('notes')

        if 'cliente_id' in serializer.validated_data:
            cliente_id = serializer.validated_data['cliente_id']
            if cliente_id is None:
                transaccion.client = None
            else:
                transaccion.client = Cliente.objects.get(id=cliente_id)
            updated_fields.append('client')

        if updated_fields:
            transaccion.edited_by = request.user
            updated_fields.append('edited_by')
            transaccion.save(update_fields=updated_fields)

        result_serializer = TransaccionMiCajaSerializer(transaccion)

        return Response({
            'success': True,
            'message': 'Transacción actualizada exitosamente',
            'transaction': result_serializer.data
        })

    @action(detail=False, methods=['post'], url_path='eliminar-transaccion')
    def eliminar_transaccion(self, request):
        """
        Delete a transaction from Mi Caja.
        Creates an audit log (TransaccionEliminada) with mandatory reason.
        Reverses inventory if product sale. Resets turno if service payment.
        """
        serializer = EliminarTransaccionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaccion_id = serializer.validated_data['transaccion_id']
        motivo = serializer.validated_data['motivo']

        try:
            transaccion = Transaction.objects.select_related(
                'client', 'appointment', 'product', 'registered_by',
                'inventory_movement', 'branch'
            ).get(id=transaccion_id)
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transacción no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Permission check
        if request.user.rol == 'EMPLEADO' and transaccion.registered_by != request.user:
            return Response(
                {'error': 'Solo puedes eliminar tus propias transacciones'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not transaccion.can_be_edited:
            return Response(
                {'error': 'No se pueden eliminar transacciones con más de 30 días'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # 1. Create audit log
            cliente_nombre = ''
            if transaccion.client:
                cliente_nombre = f"{transaccion.client.nombre} {transaccion.client.apellido}"

            registrada_por_nombre = ''
            if transaccion.registered_by:
                registrada_por_nombre = transaccion.registered_by.get_full_name()

            TransaccionEliminada.objects.create(
                eliminada_por=request.user,
                sucursal=transaccion.branch,
                motivo=motivo,
                transaccion_id_original=transaccion.id,
                tipo=transaccion.type,
                monto=transaccion.amount,
                metodo_pago=transaccion.payment_method,
                fecha=transaccion.date,
                descripcion=transaccion.description,
                notas_originales=transaccion.notes,
                cliente_nombre=cliente_nombre,
                registrada_por_nombre=registrada_por_nombre
            )

            # 2. Collect related data before deleting
            mov_to_reverse = None
            if transaccion.inventory_movement:
                mov = transaccion.inventory_movement
                mov_to_reverse = (mov, mov.producto, mov.cantidad)

            turno_to_reset = None
            if transaccion.appointment:
                turno = transaccion.appointment
                other_payments = turno.transactions.filter(
                    type='INCOME_SERVICE'
                ).exclude(id=transaccion.id).exists()
                if not other_payments:
                    turno_to_reset = turno

            # 3. Delete transaction first (before inventory movement,
            #    because mov has OneToOneField SET_NULL to transaction)
            transaccion.delete()

            # 4. Reverse inventory if product sale
            if mov_to_reverse:
                mov, producto, cantidad = mov_to_reverse
                producto.stock_actual += cantidad
                producto.save(update_fields=['stock_actual'])
                # Refresh from DB so the signal sees financial_transaction=None
                # (it was SET_NULL when we deleted the transaction above)
                mov.refresh_from_db()
                mov.delete()

            # 5. Reset turno payment status if service payment
            if turno_to_reset:
                turno_to_reset.estado_pago = 'PENDIENTE'
                turno_to_reset.save(update_fields=['estado_pago'])

        return Response({
            'success': True,
            'message': 'Transacción eliminada exitosamente'
        })

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

        transacciones = Transaction.objects.filter(
            registered_by=request.user,
            date=fecha
        )

        total_ingresos = sum(t.amount for t in transacciones if t.is_income)
        cantidad = transacciones.filter(type__startswith='INCOME').count()

        por_metodo = {}
        for t in transacciones:
            if t.is_income:
                metodo = t.get_payment_method_display()
                por_metodo[metodo] = por_metodo.get(metodo, Decimal('0.00')) + t.amount

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

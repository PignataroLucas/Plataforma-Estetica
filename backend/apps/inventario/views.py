from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import models
from .models import Producto, CategoriaProducto, Proveedor, MovimientoInventario
from .serializers import (
    ProductoListSerializer,
    ProductoDetailSerializer,
    ProductoCreateUpdateSerializer,
    CategoriaProductoSerializer,
    ProveedorSerializer,
    MovimientoInventarioSerializer,
    AjustarStockSerializer
)


class CategoriaProductoViewSet(viewsets.ModelViewSet):
    """ViewSet para categorías de productos"""
    permission_classes = [IsAuthenticated]
    serializer_class = CategoriaProductoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'creado_en']
    ordering = ['nombre']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return CategoriaProducto.objects.filter(sucursal=user.sucursal)
        return CategoriaProducto.objects.none()

    def perform_create(self, serializer):
        serializer.save(sucursal=self.request.user.sucursal)


class ProveedorViewSet(viewsets.ModelViewSet):
    """ViewSet para proveedores"""
    permission_classes = [IsAuthenticated]
    serializer_class = ProveedorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre', 'razon_social', 'cuit', 'email']
    ordering_fields = ['nombre', 'creado_en']
    ordering = ['nombre']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return Proveedor.objects.filter(sucursal=user.sucursal)
        return Proveedor.objects.none()

    def perform_create(self, serializer):
        serializer.save(sucursal=self.request.user.sucursal)


class ProductoViewSet(viewsets.ModelViewSet):
    """ViewSet para productos"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'categoria', 'proveedor', 'activo']
    search_fields = ['nombre', 'descripcion', 'marca', 'codigo_barras', 'sku']
    ordering_fields = ['nombre', 'stock_actual', 'precio_venta', 'creado_en']
    ordering = ['nombre']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return Producto.objects.filter(sucursal=user.sucursal).select_related(
                'categoria', 'proveedor'
            )
        return Producto.objects.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductoDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductoCreateUpdateSerializer
        return ProductoListSerializer

    def perform_create(self, serializer):
        serializer.save(sucursal=self.request.user.sucursal)

    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """
        Obtener productos con stock bajo (menor o igual al stock mínimo)
        """
        productos = self.get_queryset().filter(
            stock_actual__lte=models.F('stock_minimo')
        )
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def ajustar_stock(self, request, pk=None):
        """
        Ajustar el stock de un producto (entrada, salida o ajuste)
        """
        producto = self.get_object()
        serializer = AjustarStockSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tipo_movimiento = serializer.validated_data['tipo_movimiento']
        cantidad = serializer.validated_data['cantidad']
        motivo = serializer.validated_data.get('motivo', '')
        notas = serializer.validated_data.get('notas', '')
        costo_unitario = serializer.validated_data.get('costo_unitario')

        stock_anterior = producto.stock_actual

        # Calcular nuevo stock según el tipo de movimiento
        if tipo_movimiento == MovimientoInventario.TipoMovimiento.ENTRADA:
            stock_nuevo = stock_anterior + cantidad
        elif tipo_movimiento == MovimientoInventario.TipoMovimiento.SALIDA:
            if cantidad > stock_anterior:
                return Response(
                    {'error': 'No hay stock suficiente para realizar la salida'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            stock_nuevo = stock_anterior - cantidad
        elif tipo_movimiento == MovimientoInventario.TipoMovimiento.AJUSTE:
            # Para ajustes, la cantidad es el nuevo stock total
            stock_nuevo = cantidad
            cantidad = abs(stock_nuevo - stock_anterior)  # Calcular diferencia
        else:
            return Response(
                {'error': 'Tipo de movimiento no válido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar stock del producto
        producto.stock_actual = stock_nuevo
        producto.save()

        # Registrar movimiento
        movimiento = MovimientoInventario.objects.create(
            producto=producto,
            tipo=tipo_movimiento,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            motivo=motivo,
            notas=notas,
            costo_unitario=costo_unitario,
            usuario=request.user
        )

        return Response({
            'mensaje': 'Stock ajustado correctamente',
            'stock_anterior': float(stock_anterior),
            'stock_nuevo': float(stock_nuevo),
            'movimiento_id': movimiento.id
        })

    @action(detail=True, methods=['get'])
    def movimientos(self, request, pk=None):
        """
        Obtener historial de movimientos de un producto
        """
        producto = self.get_object()
        movimientos = producto.movimientos.all()[:50]  # Últimos 50 movimientos
        serializer = MovimientoInventarioSerializer(movimientos, many=True)
        return Response(serializer.data)


class MovimientoInventarioViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar movimientos de inventario (solo lectura)"""
    permission_classes = [IsAuthenticated]
    serializer_class = MovimientoInventarioSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['producto', 'tipo', 'usuario']
    ordering_fields = ['creado_en']
    ordering = ['-creado_en']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            return MovimientoInventario.objects.filter(
                producto__sucursal=user.sucursal
            ).select_related('producto', 'usuario')
        return MovimientoInventario.objects.none()

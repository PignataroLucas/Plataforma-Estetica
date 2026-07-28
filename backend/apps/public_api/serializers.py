"""
Serializers públicos: exponen SOLO datos de cara al cliente.

Deliberadamente NO incluyen datos internos (precio_costo, márgenes, comisiones,
proveedores, códigos internos, stock exacto).
"""
from rest_framework import serializers

from apps.clientes.utils import normalizar_telefono
from apps.empleados.models import CentroEstetica, Sucursal
from apps.inventario.models import Producto
from apps.servicios.models import Servicio


class SucursalPublicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['id', 'nombre', 'direccion', 'ciudad', 'provincia', 'telefono']


class CentroPublicoSerializer(serializers.ModelSerializer):
    sucursales = serializers.SerializerMethodField()
    telefono_whatsapp = serializers.SerializerMethodField()

    class Meta:
        model = CentroEstetica
        fields = [
            'id', 'nombre', 'direccion', 'ciudad', 'provincia', 'pais',
            'telefono', 'telefono_whatsapp', 'email', 'logo', 'sucursales',
        ]

    def get_sucursales(self, obj):
        activas = obj.sucursales.filter(activa=True)
        return SucursalPublicaSerializer(activas, many=True).data

    def get_telefono_whatsapp(self, obj):
        """
        Teléfono en E.164 para armar el link de WhatsApp desde la app.
        Vacío si el centro no cargó teléfono o si no es un número válido:
        preferimos no ofrecer el botón antes que abrir un chat con un desconocido.
        """
        return normalizar_telefono(obj.telefono)


class ServicioPublicoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.SerializerMethodField()
    color = serializers.CharField(source='color_display', read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)

    class Meta:
        model = Servicio
        fields = [
            'id', 'nombre', 'descripcion', 'duracion_minutos', 'precio',
            'categoria_nombre', 'color', 'sucursal', 'sucursal_nombre',
            # Ficha del tratamiento (app mobile)
            'beneficios', 'video_url', 'reservable_por_cliente',
        ]

    def get_categoria_nombre(self, obj):
        return obj.categoria.nombre if obj.categoria else None


class ProductoPublicoSerializer(serializers.ModelSerializer):
    precio = serializers.DecimalField(
        source='precio_venta_final', max_digits=10, decimal_places=2, read_only=True
    )
    porcentaje_descuento = serializers.ReadOnlyField()
    categoria_nombre = serializers.SerializerMethodField()
    disponible = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'marca',
            'precio', 'en_oferta', 'precio_oferta', 'porcentaje_descuento',
            'disponible', 'foto', 'categoria_nombre', 'sucursal',
            # Datos para el motor de recompra (app mobile)
            'contenido_ml', 'duracion_estimada_dias', 'pao_meses', 'frecuencia_uso',
        ]

    def get_categoria_nombre(self, obj):
        return obj.categoria.nombre if obj.categoria else None

    def get_disponible(self, obj):
        # Expone disponibilidad como booleano, sin revelar el stock exacto
        return obj.stock_actual > 0

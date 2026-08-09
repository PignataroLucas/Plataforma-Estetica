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
from apps.turnos.services import fechas_reservables, modo_reserva_de


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
    modo_reserva = serializers.SerializerMethodField()
    fechas_disponibles = serializers.SerializerMethodField()

    class Meta:
        model = Servicio
        fields = [
            'id', 'nombre', 'descripcion', 'duracion_minutos', 'precio',
            'categoria_nombre', 'color', 'sucursal', 'sucursal_nombre',
            # Ficha del tratamiento (app mobile)
            'beneficios', 'video_url', 'reservable_por_cliente',
            'modo_reserva', 'fechas_disponibles',
        ]

    def get_categoria_nombre(self, obj):
        return obj.categoria.nombre if obj.categoria else None

    def get_modo_reserva(self, obj):
        """'fechas' (fechas puntuales cargadas) o 'dias' (patrón semanal)."""
        return modo_reserva_de(obj)

    def get_fechas_disponibles(self, obj):
        """
        Fechas concretas ya resueltas (YYYY-MM-DD), en los dos modos. La ficha las
        muestra como "próximas fechas" y el flujo de reserva arma el calendario
        con esto, sin repetir la regla del lado del cliente.
        """
        return [fecha.isoformat() for fecha in fechas_reservables(obj)]


class ProductoPublicoSerializer(serializers.ModelSerializer):
    """
    No expone disponibilidad, y es a propósito.

    Había un campo `disponible` que devolvía `stock_actual > 0`. Desde el sync
    con Conto, `stock_actual` es el stock **del depósito**, no el del mostrador:
    el Duo Serum tiene 9 en el centro y −5 en el depósito. La app le habría
    dicho a una clienta que no está disponible algo que está en la vitrina.

    Mostrar disponibilidad de verdad requiere separar los dos stocks, que es un
    trabajo aparte. Hasta entonces, no decir nada es más honesto que mentir.
    """
    precio = serializers.DecimalField(
        source='precio_venta_final', max_digits=10, decimal_places=2, read_only=True
    )
    porcentaje_descuento = serializers.ReadOnlyField()
    categoria_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            # `descripcion` es el "qué es" y `beneficios` el "qué gana",
            # mismo criterio que la ficha del tratamiento.
            'id', 'nombre', 'descripcion', 'beneficios', 'marca',
            'precio', 'en_oferta', 'precio_oferta', 'porcentaje_descuento',
            # `foto_thumb` es para la grilla y `foto` para la ficha: la grilla
            # nunca debería bajar 31 originales por datos móviles.
            'foto', 'foto_thumb', 'categoria_nombre', 'sucursal',
            # Datos para el motor de recompra (app mobile)
            'contenido_ml', 'duracion_estimada_dias', 'pao_meses', 'frecuencia_uso',
        ]

    def get_categoria_nombre(self, obj):
        return obj.categoria.nombre if obj.categoria else None

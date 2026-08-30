"""
Cuánto vende la app de las clientas (COMPRA_EN_APP_SPEC.md §5.7).

Es la métrica que justifica el proyecto entero: si dentro de tres meses no se
puede separar lo que vendió la app de lo que vendió la web, no hay forma de
decir si valió la pena.

**Todo se apoya en una sola premisa**, que es la del §3.2: los únicos que
emitimos códigos con prefijo `APP-` somos nosotros, así que una venta que llega
con uno es, por definición, una venta de la app. No se puede usar el campo
`origen_venta` de Tienda Nube — una compra hecha desde la app llega como
`store`, exactamente igual que una del navegador (§6.3).

De ahí que el camino sea siempre `ContoSale.cupon_app`, y no un campo propio en
`Transaction`: la atribución tiene un solo dueño, y duplicarla en la tabla
financiera crearía dos lugares que pueden discrepar cuando se reprocesa un
comprobante.
"""
from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum

from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoSale, CuponApp

CERO = Decimal('0.00')

# Lo que cuenta como una venta: importada y sin reversar. Las omitidas y las que
# fallaron no son plata que entró.
VENTAS = {
    'type': ContoSale.VoucherType.SALE,
    'status': ContoSale.Status.PROCESSED,
}


def _ventas(centro, desde, hasta, sucursal_id=None):
    """Las ventas importadas del centro en el período."""
    qs = ContoSale.objects.filter(
        integration__center=centro,
        date__gte=desde,
        date__lte=hasta,
        **VENTAS,
    )
    if sucursal_id:
        qs = qs.filter(integration__branch_id=sucursal_id)
    return qs


def resumen(centro, desde, hasta, sucursal_id=None):
    """
    Cuánto vendió la app en el período, contra cuánto vendió todo lo demás.

    El ticket promedio de los dos lados es la comparación que pidió Conto y que
    el §5.7 adopta: **es mejor pregunta que "cuánto vendió la app"**, porque
    distingue las compras que el descuento trajo de las que iban a pasar igual
    y solo le costaron margen al centro.
    """
    ventas = _ventas(centro, desde, hasta, sucursal_id)

    datos = ventas.aggregate(
        app_cantidad=Count('id', filter=Q(cupon_app__isnull=False)),
        app_total=Sum('total', filter=Q(cupon_app__isnull=False)),
        app_ticket=Avg('total', filter=Q(cupon_app__isnull=False)),
        app_descuento=Sum('coupon_discount', filter=Q(cupon_app__isnull=False)),
        resto_cantidad=Count('id', filter=Q(cupon_app__isnull=True)),
        resto_total=Sum('total', filter=Q(cupon_app__isnull=True)),
        resto_ticket=Avg('total', filter=Q(cupon_app__isnull=True)),
    )

    app_total = datos['app_total'] or CERO
    resto_total = datos['resto_total'] or CERO
    total = app_total + resto_total

    return {
        'app': {
            'ventas': datos['app_cantidad'],
            'facturado': float(app_total),
            'ticket_promedio': float(datos['app_ticket'] or CERO),
            'descuento_otorgado': float(datos['app_descuento'] or CERO),
        },
        'resto': {
            'ventas': datos['resto_cantidad'],
            'facturado': float(resto_total),
            'ticket_promedio': float(datos['resto_ticket'] or CERO),
        },
        # Cuánto de lo que entró por ventas online vino de la app.
        'participacion_app': (
            round(float(app_total / total * 100), 2) if total > CERO else 0.0
        ),
    }


def productos(centro, desde, hasta, sucursal_id=None, limite=10):
    """
    Qué productos vende la app.

    Va por `Transaction` y no por las líneas del comprobante porque la
    transacción ya tiene el producto resuelto contra el catálogo y el descuento
    prorrateado — o sea, lo que de verdad ingresó por cada uno.

    **La subconsulta no es preferencia de estilo.** `conto_sales` es un
    many-to-many: filtrar con `conto_sales__cupon_app__isnull=False` hace un
    join que devuelve una fila por cada venta ligada, y una transacción ligada a
    dos comprobantes se cuenta dos veces. Un `.distinct()` no lo arregla —
    aplica al SELECT final, que después de `values().annotate()` ya incluye los
    agregados, así que el `Sum` sigue sumando el duplicado. Con `id__in` no hay
    join en la consulta de afuera y cada transacción aparece una sola vez.
    """
    de_la_app = (
        ContoSale.objects
        .filter(integration__center=centro, cupon_app__isnull=False, **VENTAS)
        .values('transactions__id')
    )

    qs = Transaction.objects.filter(
        id__in=de_la_app,
        branch__centro_estetica=centro,
        date__gte=desde,
        date__lte=hasta,
        type='INCOME_PRODUCT',
        product__isnull=False,
    )
    if sucursal_id:
        qs = qs.filter(branch_id=sucursal_id)

    filas = (
        qs.values('product_id', 'product__nombre')
        .annotate(ventas=Count('id'), facturado=Sum('amount'))
        .order_by('-facturado')[:limite]
    )

    return [
        {
            'producto_id': f['product_id'],
            'producto': f['product__nombre'],
            'ventas': f['ventas'],
            'facturado': float(f['facturado'] or CERO),
        }
        for f in filas
    ]


def clientas(centro, desde, hasta, sucursal_id=None, limite=10):
    """
    Quiénes compran por la app.

    Sale del cupón y no del comprador del comprobante: el cupón dice a quién se
    lo dimos, que es la clienta de la plataforma. El comprador de Tienda Nube
    puede ser la misma persona con otro mail (§6.7).
    """
    qs = _ventas(centro, desde, hasta, sucursal_id).filter(
        cupon_app__isnull=False, cupon_app__cliente__isnull=False
    )

    filas = (
        qs.values(
            'cupon_app__cliente_id',
            'cupon_app__cliente__nombre',
            'cupon_app__cliente__apellido',
        )
        .annotate(compras=Count('id'), gastado=Sum('total'))
        .order_by('-gastado')[:limite]
    )

    return [
        {
            'cliente_id': f['cupon_app__cliente_id'],
            'cliente': f"{f['cupon_app__cliente__apellido']}, "
                       f"{f['cupon_app__cliente__nombre']}",
            'compras': f['compras'],
            'gastado': float(f['gastado'] or CERO),
        }
        for f in filas
    ]


def cupones(centro, desde, hasta):
    """
    Cuántas compras se empezaron y cuántas se terminaron.

    Es la métrica que solo nosotros podemos calcular, porque Tienda Nube no sabe
    que un cupón se emitió al tocar "Comprar": cada cupón emitido es una
    intención de compra, y los que vencen sin usarse son carritos abandonados en
    el checkout.

    Se cuenta sobre la fecha de emisión, no la de uso: la pregunta es qué pasó
    con las intenciones de este período.
    """
    emitidos = CuponApp.objects.filter(
        integration__center=centro,
        issued_at__date__gte=desde,
        issued_at__date__lte=hasta,
    )

    datos = emitidos.aggregate(
        total=Count('id'),
        usados=Count('id', filter=Q(used_at__isnull=False)),
    )

    return {
        'emitidos': datos['total'],
        'usados': datos['usados'],
        'sin_usar': datos['total'] - datos['usados'],
        # Qué proporción de los "Comprar" terminó en una venta.
        'conversion': (
            round(datos['usados'] / datos['total'] * 100, 2)
            if datos['total'] else 0.0
        ),
    }

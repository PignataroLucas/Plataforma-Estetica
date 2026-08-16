"""
Preparar una compra desde la app: cupón + qué mandarle al checkout de Tienda Nube.

Esto es el paso 2 al 5 del §4 del COMPRA_EN_APP_SPEC.md. La app manda el carrito,
acá se resuelve el descuento, se emite el cupón y se devuelve lo que el WebView
necesita para armar el carrito del otro lado.

Dos cosas se aprendieron probando contra la tienda demo y explican esta forma:

1. **No hay una URL que agregue al carrito.** Solo funciona un POST a `/comprar/`
   con `add_to_cart` y `quantity`, y **agrega un producto por vez**: mandando dos
   pares en el mismo POST, Tienda Nube toma el primero y descarta el resto. Por
   eso se devuelve una lista y no una URL armada.
2. **El `add_to_cart` es el id de PRODUCTO**, no el de la variante.
"""
from decimal import Decimal, ROUND_HALF_UP

from apps.inventario.models import Producto

from .cupones import SinDescuento, SinIntegracion, emitir_cupon
from .models import TiendanubeIntegration

CENTAVO = Decimal('0.01')


class CompraInvalida(Exception):
    """El carrito no se puede comprar. El mensaje va tal cual a la app."""


def preparar_compra(cliente, items):
    """
    Resolver todo lo que hace falta para abrir el checkout de esta compra.

    `items` es [{'producto': <Producto>, 'cantidad': int}]. Devuelve un dict
    listo para serializar.

    El cupón puede no existir y la compra sigue en pie: si a la clienta no le
    corresponde descuento, comprar igual tiene que funcionar. Lo que no puede
    pasar es lo contrario —cobrar sin el descuento que la app mostró—, y de eso
    se ocupa que el porcentaje salga de un solo lugar (§5.8).
    """
    integration = (
        TiendanubeIntegration.objects
        .filter(center=cliente.centro_estetica, is_active=True)
        .first()
    )
    if integration is None or not integration.store_url:
        raise CompraInvalida(
            'La tienda online no está disponible en este momento.'
        )

    lineas = []
    subtotal = Decimal('0.00')
    for item in items:
        producto = item['producto']
        cantidad = item['cantidad']
        # Ya se validó al resolver los productos, pero esto es lo que impide que
        # un carrito viejo —guardado antes de que el producto se despublicara—
        # mande al checkout un id vacío.
        if not producto.tiendanube_product_id:
            raise CompraInvalida(
                f'«{producto.nombre}» no está disponible para comprar desde la app.'
            )
        lineas.append({
            'producto_tiendanube': producto.tiendanube_product_id,
            'cantidad': cantidad,
            'nombre': producto.nombre,
        })
        subtotal += producto.precio_venta_final * cantidad

    cupon = None
    try:
        cupon = emitir_cupon(cliente)
    except SinDescuento:
        # A esta clienta no le toca descuento. No es un error: el catálogo le
        # mostró precio de lista y eso es lo que va a pagar.
        pass
    except SinIntegracion as exc:
        raise CompraInvalida(str(exc))

    porcentaje = cupon.percentage if cupon else Decimal('0.00')
    total = (subtotal * (1 - porcentaje / 100)).quantize(CENTAVO, rounding=ROUND_HALF_UP)

    return {
        'checkout': {
            # El WebView hace un POST por línea contra esta URL.
            'url': f'{integration.store_url}/comprar/',
            'items': lineas,
        },
        'cupon': {
            'codigo': cupon.code,
            'porcentaje': f'{cupon.percentage:.2f}',
        } if cupon else None,
        'subtotal': f'{subtotal.quantize(CENTAVO)}',
        'total': f'{total}',
    }


def resolver_items(cliente, pedidos):
    """
    Convertir lo que mandó la app en productos de este centro.

    `pedidos` es [{'producto': <id>, 'cantidad': int}]. Todo se resuelve contra
    el centro de la clienta: un id de otro centro no es un 404 accidental, es la
    única barrera entre carritos de inquilinos distintos.
    """
    if not pedidos:
        raise CompraInvalida('El carrito está vacío.')

    ids = [p['producto'] for p in pedidos]
    productos = {
        p.id: p
        for p in Producto.objects.filter(
            id__in=ids,
            sucursal__centro_estetica=cliente.centro_estetica,
            activo=True,
        )
    }

    items = []
    for pedido in pedidos:
        producto = productos.get(pedido['producto'])
        if producto is None:
            raise CompraInvalida('Alguno de los productos ya no está disponible.')
        items.append({'producto': producto, 'cantidad': pedido['cantidad']})

    return items

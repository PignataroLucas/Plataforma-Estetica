"""
Emisión y limpieza de los cupones de la app.

El cupón es el mecanismo entero de COMPRA_EN_APP_SPEC.md §3.2: aplica el
descuento, lo ata a un solo uso —para que el código no termine circulando en un
grupo de WhatsApp— y hace que la venta sea atribuible cuando vuelve por Conto.

Una sola regla manda acá: **el porcentaje sale de `Cliente.descuento_app`**, que
es el mismo número que la app usó para mostrar el precio (§5.8). Si esto lo
recalculara por su cuenta, la clienta vería un precio y pagaría otro, que es la
trampa del §6.1.
"""
import logging
import secrets
from datetime import timedelta

from django.db import transaction as db_transaction
from django.utils import timezone

from .models import CuponApp, TiendanubeIntegration
from .tiendanube import TiendanubeClient, TiendanubeError

logger = logging.getLogger(__name__)

# Prefijo pedido por el §5.3: hace que los cupones de la app se puedan agrupar o
# excluir en el reporte de cupones de Conto, que está pensado para campañas y no
# para un cupón por venta (§5.7).
PREFIJO = 'APP-'

# Sin vocales ni caracteres que se confundan al leerlos (0/O, 1/I/L): el código
# se ve en el checkout y alguien lo va a dictar por teléfono alguna vez.
ALFABETO = '23456789BCDFGHJKMNPQRSTVWXYZ'
LARGO = 8

# Alcanza y sobra: el cupón se emite al tocar "Comprar" y se usa en esa misma
# sesión. Corto además limita el daño si un código se filtra (§9).
VIGENCIA = timedelta(hours=1)


class SinIntegracion(Exception):
    """El centro no tiene su tienda de Tienda Nube vinculada"""


class SinDescuento(Exception):
    """A la clienta no le corresponde ningún descuento: no hay cupón que emitir"""


def generar_codigo():
    """
    Código impredecible, no secuencial.

    28^8 son unas 3.7e11 combinaciones. La unicidad la garantiza la base, no
    esto: ver `emitir_cupon`.
    """
    sufijo = ''.join(secrets.choice(ALFABETO) for _ in range(LARGO))
    return f'{PREFIJO}{sufijo}'


def emitir_cupon(cliente):
    """
    Crear el cupón de esta clienta en Tienda Nube y guardarlo.

    Devuelve el `CuponApp`. Lanza `SinIntegracion` si el centro no tiene tienda
    vinculada y `SinDescuento` si el porcentaje resuelto es cero — un cupón del
    0% no descuenta nada y ensucia el panel del centro con una fila por compra.

    El orden importa: primero se crea en Tienda Nube y después se guarda acá. Al
    revés quedaría una fila diciendo que existe un cupón que la clienta no puede
    usar, y la atribución del §5.6 buscaría un código que nunca existió.
    """
    integration = (
        TiendanubeIntegration.objects
        .filter(center=cliente.centro_estetica, is_active=True)
        .first()
    )
    if integration is None or not integration.can_issue_coupons:
        raise SinIntegracion(
            f"El centro «{cliente.centro_estetica.nombre}» no tiene su tienda de "
            f"Tienda Nube vinculada. Instalá la app en la tienda primero."
        )

    porcentaje = cliente.descuento_app
    if porcentaje <= 0:
        raise SinDescuento(
            "A esta clienta no le corresponde descuento: el segmento está en 0%."
        )

    expira = timezone.now() + VIGENCIA
    codigo = _codigo_libre()

    cupon_tn = TiendanubeClient(integration).create_coupon(
        _payload(codigo, porcentaje, expira, integration)
    )

    cupon = CuponApp.objects.create(
        integration=integration,
        cliente=cliente,
        code=codigo,
        percentage=porcentaje,
        tiendanube_coupon_id=str((cupon_tn or {}).get('id') or ''),
        expires_at=expira,
    )
    logger.info(
        "Cupón %s emitido para la clienta %s (%s%%)",
        cupon.code, cliente.pk, porcentaje,
    )
    return cupon


def _codigo_libre(intentos=5):
    """
    Un código que no exista ya.

    La colisión es improbable pero no imposible, y Tienda Nube rechaza los
    códigos repetidos: mejor descubrirlo acá que con un 422 en la cara de la
    clienta que está por pagar.
    """
    for _ in range(intentos):
        codigo = generar_codigo()
        if not CuponApp.objects.filter(code=codigo).exists():
            return codigo
    raise RuntimeError('No se pudo generar un código de cupón libre')


def _payload(codigo, porcentaje, expira, integration):
    """
    El cupón como lo espera Tienda Nube.

    `end_date` y `end_time` van en hora local de la tienda, que es la de
    Argentina. Igual la garantía real de que un cupón no sobrevive es
    `max_uses: 1` más la limpieza: no sabemos si TN trata `end_time` como
    inclusivo, y no vale la pena depender de eso.
    """
    vence_local = timezone.localtime(expira)
    return {
        'code': codigo,
        'type': 'percentage',
        'value': str(porcentaje),
        'valid': True,
        'max_uses': 1,
        'end_date': vence_local.strftime('%Y-%m-%d'),
        'end_time': vence_local.strftime('%H:%M'),
        # La decisión del §7.2, que es del centro. Se manda explícito aunque
        # coincida con el default de TN: así el comportamiento no depende de
        # que ellos no cambien el suyo.
        'combines_with_other_discounts': integration.coupons_combine_with_other_discounts,
    }


def limpiar_vencidos(limite=None):
    """
    Borrar de Tienda Nube los cupones que vencieron sin usarse.

    Cada "Comprar" que no termina en compra deja un cupón vivo; sin esto, en
    unos meses el panel del centro tiene miles (§6.5).

    La fila local se conserva: es lo que después responde cuántas compras se
    empezaron y no se terminaron. Solo se marca `revoked_at`.

    Devuelve (borrados, errores). No propaga: un cupón que no se pudo borrar se
    reintenta en la corrida siguiente.
    """
    vencidos = (
        CuponApp.objects
        .filter(
            expires_at__lt=timezone.now(),
            used_at__isnull=True,
            revoked_at__isnull=True,
        )
        .exclude(tiendanube_coupon_id='')
        .select_related('integration')
        .order_by('expires_at')
    )
    if limite:
        vencidos = vencidos[:limite]

    borrados, errores = 0, []
    for cupon in vencidos:
        if not cupon.integration.can_issue_coupons:
            # El centro desinstaló la app: sus cupones ya no existen del otro
            # lado. Se marcan para no reintentarlos en cada corrida.
            _marcar_revocado(cupon)
            borrados += 1
            continue

        try:
            TiendanubeClient(cupon.integration).delete_coupon(cupon.tiendanube_coupon_id)
        except TiendanubeError as exc:
            logger.warning("No se pudo borrar el cupón %s: %s", cupon.code, exc)
            errores.append(f"{cupon.code}: {exc}")
            continue

        _marcar_revocado(cupon)
        borrados += 1

    return borrados, errores


def _marcar_revocado(cupon):
    with db_transaction.atomic():
        cupon.revoked_at = timezone.now()
        cupon.save(update_fields=['revoked_at'])

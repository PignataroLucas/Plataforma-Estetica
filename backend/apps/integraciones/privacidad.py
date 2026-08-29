"""
Los tres webhooks de privacidad que Tienda Nube exige para homologar una app.

`store/redact`, `customers/redact` y `customers/data_request`
(COMPRA_EN_APP_SPEC.md §5.1). Cada uno deja una fila en `TiendanubePrivacyRequest`
y solo uno de los tres borra algo.

**Por qué los de comprador no borran nada.** Esta app pide leer productos y
leer y escribir cupones: nunca lee clientes ni órdenes de la tienda, así que no
hay dato de un comprador de Tienda Nube guardado acá que se pueda borrar. Lo que
sí existe —la ficha de la clienta en el CRM— es dato del centro, cargado en esta
plataforma y no traído de la tienda. Borrarlo porque Tienda Nube reenvió un
pedido sería destruir datos del centro por decisión de un tercero. Por eso se
registra el pedido y lo resuelve una persona.

Todo lo de acá corre dentro del webhook, que tiene **3 segundos de timeout**:
solo escrituras a la base, ninguna llamada HTTP de salida.
"""
import logging

from django.db import transaction as db_transaction
from django.utils import timezone

from .models import TiendanubeIntegration, TiendanubePrivacyRequest

logger = logging.getLogger(__name__)


def procesar(event, payload):
    """
    Atender un webhook de privacidad ya verificado.

    `event` es uno de `TiendanubePrivacyRequest.Event`. Devuelve la fila creada.
    El `store_id` sale del payload, no de la URL: es el único dato que Tienda
    Nube garantiza en los tres eventos.
    """
    store_id = str(payload.get('store_id') or '')

    with db_transaction.atomic():
        pedido = _registrar(event, store_id, payload)

        if event == TiendanubePrivacyRequest.Event.STORE_REDACT:
            _desvincular_tienda(pedido)

    return pedido


def _registrar(event, store_id, payload):
    integracion = (
        TiendanubeIntegration.objects.filter(store_id=store_id).first()
        if store_id else None
    )
    return TiendanubePrivacyRequest.objects.create(
        integration=integracion,
        store_id=store_id,
        event=event,
        payload=payload,
    )


def _desvincular_tienda(pedido):
    """
    El centro desinstaló la app: matar el token y dejar la integración fría.

    **La fila de la integración no se borra, y los `CuponApp` tampoco.** El FK
    de `CuponApp` es CASCADE, así que borrar la integración se llevaría puesta
    la historia entera de cupones emitidos —qué código, a qué clienta, cuándo—,
    que es sobre lo que se apoya la atribución de ventas de la app (§5.7). Lo
    que Tienda Nube pide borrar es su dato: la credencial. Eso es lo que se
    borra.

    Los cupones que quedaron vivos del otro lado se mueren con la desinstalación
    y la limpieza los marca sin reintentar, porque `can_issue_coupons` ya da
    falso (`cupones.limpiar_vencidos`).
    """
    integracion = pedido.integration
    if integracion is None:
        # Una tienda que nunca vinculamos, o que ya se había desvinculado. El
        # pedido igual queda registrado; no hay nada que borrar.
        _marcar_resuelto(pedido, 'No había integración vinculada para esa tienda.')
        return

    integracion.token = ''
    integracion.scope = ''
    integracion.is_active = False
    integracion.uninstalled_at = timezone.now()
    integracion.save(update_fields=[
        'token', 'scope', 'is_active', 'uninstalled_at', 'updated_at'
    ])

    logger.warning(
        "Tienda Nube %s pidió el borrado de la tienda: se desvinculó el centro %s",
        integracion.store_id, integracion.center_id,
    )
    _marcar_resuelto(
        pedido,
        'Se borró el token y se desactivó la integración. Se conservan los '
        'cupones emitidos, que son dato de la plataforma y no de la tienda.'
    )


def _marcar_resuelto(pedido, notas):
    pedido.handled_at = timezone.now()
    pedido.notes = notas
    pedido.save(update_fields=['handled_at', 'notes'])

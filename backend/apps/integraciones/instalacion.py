"""
Linking a center to its Tienda Nube store, once the token is in hand.

Shared by the two ways that happens: the OAuth callback, when the merchant
installs the app, and the `vincular_tiendanube` command, which is the fallback
for when the callback is not reachable yet. Both end here so the guard that
stops one center from taking another's store lives in a single place — issuing
coupons on the wrong store is someone else's money.

Getting the token is not here: that is `tiendanube.exchange_code_for_token`,
which runs before there is anything to link.
"""
import logging
from datetime import timedelta

from django.utils import timezone

from .models import TiendanubeInstallIntent, TiendanubeIntegration
from .tiendanube import TiendanubeClient, TiendanubeError

logger = logging.getLogger(__name__)

# Donde el comerciante autoriza la app. El `app_id` de Tienda Nube es el mismo
# número que el `client_id`, así que sale de la misma variable de entorno.
AUTHORIZE_URL = 'https://www.tiendanube.com/apps/{app_id}/authorize'

# Cuánto vive una instalación ya empezada. Tiene que alcanzar para
# entrar a Tienda Nube, loguearse y aceptar los permisos, y ser lo bastante
# corta como para que dos centros no se pisen (ver `resolver_centro`).
VENTANA_DE_INSTALACION = timedelta(minutes=15)


class TiendaDeOtroCentro(Exception):
    """La tienda ya está vinculada a otro centro"""


class CentroSinResolver(Exception):
    """Llegó un token válido y no hay forma de saber de qué centro es"""


def cerrar_intentos_abiertos(centro):
    """
    Cerrar los intentos que este centro dejó abiertos.

    Si alguien apretó «Vincular» dos veces, el que vale es el último: dos
    intentos abiertos del mismo centro harían fallar la resolución por ambigua
    contra sí misma.
    """
    return (
        TiendanubeInstallIntent.objects
        .filter(center=centro, consumed_at__isnull=True, expires_at__gt=timezone.now())
        .update(consumed_at=timezone.now())
    )


def resolver_centro(store_id):
    """
    De qué centro es la tienda que acaba de autorizar.

    Devuelve `(centro, intento)`. El intento viene para que quien vincule lo
    marque usado recién cuando la vinculación salió bien.

    Dos caminos, en este orden:

    1. **La tienda ya tiene integración.** Es una reinstalación o una
       reautorización, y el centro está fuera de discusión. Manda sobre
       cualquier intento abierto: si el store id ya es de un centro, un intento
       de otro centro es un error de operación, no una instrucción.
    2. **Un único intento abierto.** Primera instalación, declarada de antemano.

    Con cero intentos o con más de uno se levanta `CentroSinResolver`. Adivinar
    tendría el costo de emitir cupones en la tienda equivocada; que la operadora
    reintente cuesta un click.
    """
    integracion = (
        TiendanubeIntegration.objects
        .filter(store_id=str(store_id))
        .select_related('center')
        .first()
    )
    if integracion is not None:
        return integracion.center, None

    abiertos = list(
        TiendanubeInstallIntent.objects
        .filter(consumed_at__isnull=True, expires_at__gt=timezone.now())
        .select_related('center')[:2]
    )

    if not abiertos:
        raise CentroSinResolver(
            f"La tienda {store_id} autorizó la app, pero nadie declaró estar "
            f"instalándola, así que no se sabe de qué centro es. Empezá desde "
            f"«Instalaciones de Tienda Nube iniciadas» en el admin y volvé a "
            f"instalar."
        )
    if len(abiertos) > 1:
        raise CentroSinResolver(
            f"Hay más de un centro instalando la app al mismo tiempo, así que "
            f"no se puede saber de cuál es la tienda {store_id}. Esperá unos "
            f"minutos y volvé a empezar, de a un centro por vez."
        )

    intento = abiertos[0]
    return intento.center, intento


def vincular(centro, datos, intento=None):
    """
    Guardar el token de esta tienda contra este centro.

    `datos` es lo que devuelve el intercambio OAuth: `access_token`, `user_id`
    y `scope`. Devuelve `(integracion, creada)`.

    Se pisa la fila en vez de crear otra: reinstalar emite un token nuevo y deja
    el viejo sin efecto, así que dos filas para un centro dejarían la emisión de
    cupones dependiendo de cuál se lea primero.
    """
    store_id = str(datos['user_id'])

    ocupada = (
        TiendanubeIntegration.objects
        .filter(store_id=store_id)
        .exclude(center=centro)
        .select_related('center')
        .first()
    )
    if ocupada:
        raise TiendaDeOtroCentro(
            f"La tienda {store_id} ya está vinculada al centro "
            f"«{ocupada.center.nombre}». Desvinculala antes de reasignarla."
        )

    integracion, creada = TiendanubeIntegration.objects.update_or_create(
        center=centro,
        defaults={
            'store_id': store_id,
            'token': datos['access_token'],
            'scope': datos.get('scope', ''),
            'is_active': True,
            'installed_at': timezone.now(),
            'uninstalled_at': None,
        },
    )

    # Recién acá: una intención consumida por una vinculación que falló dejaría
    # al centro sin forma de reintentar sin volver a empezar de cero.
    if intento is not None:
        intento.consumed_at = timezone.now()
        intento.save(update_fields=['consumed_at'])

    logger.info(
        "Tienda Nube %s vinculada al centro %s (%s)",
        store_id, centro.pk, 'nueva' if creada else 'actualizada',
    )
    return integracion, creada


def completar_datos_tienda(integracion):
    """
    Leer la tienda y guardar su nombre y su URL.

    Es la única prueba de que el token sirve de verdad: sin esto la vinculación
    se da por buena con un token que puede fallar en el primer cupón. La URL
    además no es cosmética — es contra la que el WebView arma el carrito (§5.5),
    y por eso sale de acá y no de algo tipeado a mano.

    Devuelve el error como texto si no se pudo leer, y `None` si salió bien. No
    levanta: el token ya es válido —el intercambio lo devolvió—, así que tirarlo
    por una lectura que puede fallar por red obligaría a reinstalar de gusto.
    """
    try:
        tienda = TiendanubeClient(integracion).get_store() or {}
    except TiendanubeError as exc:
        logger.warning("No se pudo leer la tienda %s: %s", integracion.store_id, exc)
        return str(exc)

    nombre = tienda.get('name')
    if isinstance(nombre, dict):
        # Tienda Nube devuelve los textos por idioma: {'es': 'Ame Demo'}
        nombre = nombre.get('es') or next(iter(nombre.values()), '')

    integracion.store_name = (nombre or '')[:200]
    integracion.store_url = (tienda.get('url_with_protocol') or '').rstrip('/')
    integracion.save(update_fields=['store_name', 'store_url', 'updated_at'])
    return None

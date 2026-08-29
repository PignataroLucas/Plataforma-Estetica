"""
HTTP client for Tienda Nube.

Deliberately small. The sales keep coming through Conto (see
INTEGRACION_CONTO_SPEC.md §1): this channel exists only to issue the discount
coupons that make a purchase from the app attributable and cheaper
(COMPRA_EN_APP_SPEC.md §5.1). Nothing here reads orders or stock.

The OAuth exchange and the webhook signature check are module-level functions
and not methods: both run *before* there is an integration to hang them on,
which is the whole point of them.
"""
import hashlib
import hmac
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OAUTH_TOKEN_URL = 'https://www.tiendanube.com/apps/authorize/token'
API_BASE_URL = 'https://api.tiendanube.com/v1'

# Tienda Nube requires a User-Agent that identifies the app and a contact
# address; it is the field declared as "Correo de contacto" in the partner
# panel. Requests without it get rejected.
USER_AGENT = 'Ame-App-Clientes (lucasmartinpignataro@gmail.com)'

TIMEOUT = 20


class TiendanubeError(Exception):
    """Base error for the Tienda Nube integration"""


class TiendanubeNotConfigured(TiendanubeError):
    """The app credentials are missing from the environment"""


class TiendanubeAuthError(TiendanubeError):
    """The token is missing, invalid or was revoked by uninstalling the app"""


class TiendanubeUnavailable(TiendanubeError):
    """Network failure or 5xx. Retryable"""


def exchange_code_for_token(code):
    """
    Trade the installation code for a permanent token.

    Tienda Nube redirects the merchant back with a `code` that **lives five
    minutes**, so this runs as close to the redirect as possible. The token it
    returns does not expire: it is valid until the merchant uninstalls the app
    or a new one is issued, which is why there is no refresh flow anywhere.

    Returns the raw payload: `access_token`, `user_id` (the store id) and
    `scope`.
    """
    client_id = getattr(settings, 'TIENDANUBE_CLIENT_ID', '')
    client_secret = getattr(settings, 'TIENDANUBE_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        raise TiendanubeNotConfigured(
            "Faltan TIENDANUBE_CLIENT_ID y TIENDANUBE_CLIENT_SECRET en el entorno. "
            "Salen de «Claves de Acceso» en el panel de partners de Tienda Nube."
        )

    try:
        response = requests.post(
            OAUTH_TOKEN_URL,
            json={
                'client_id': str(client_id),
                'client_secret': client_secret,
                'grant_type': 'authorization_code',
                'code': code,
            },
            headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise TiendanubeUnavailable(f"No se pudo conectar con Tienda Nube: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise TiendanubeError(
            f"Tienda Nube devolvió una respuesta que no es JSON ({response.status_code})"
        ) from exc

    # The error comes back as 200 with an `error` key as often as it comes back
    # as 4xx, so both paths have to be checked.
    error = payload.get('error')
    if error or response.status_code >= 400:
        description = payload.get('error_description') or response.text[:300]
        raise TiendanubeAuthError(_explicar_error(error, description))

    if not payload.get('access_token') or not payload.get('user_id'):
        raise TiendanubeError(
            f"La respuesta no trae access_token y user_id: {payload!r}"
        )

    return payload


def verify_webhook_signature(raw_body, signature):
    """
    Whether this webhook really came from Tienda Nube.

    The signature is the HMAC-SHA256 of the **raw request body**, hex encoded,
    keyed with the app's client secret, and travels in `x-linkedstore-hmac-sha256`.

    Two things that look like details and are not:

    - It has to be the bytes as they arrived. Parsing the JSON and dumping it
      again changes spacing and key order, and the hash stops matching for
      requests that were perfectly valid.
    - The comparison is `compare_digest`, not `==`. A plain comparison returns
      as soon as two bytes differ, and that timing is enough to guess a
      signature one byte at a time.

    Without a configured secret this returns False rather than passing the
    request through: an endpoint that deactivates integrations is not one to
    leave open because a variable is missing from the environment.
    """
    secret = getattr(settings, 'TIENDANUBE_CLIENT_SECRET', '')
    if not secret or not signature:
        return False

    esperada = hmac.new(
        secret.encode('utf-8'), raw_body, hashlib.sha256
    ).hexdigest()
    # En minúscula los dos lados: el ejemplo de Tienda Nube es el `hash_hmac` de
    # PHP, que devuelve hexadecimal en minúscula, pero `AB` y `ab` son el mismo
    # byte y rechazar por eso sería un no a un pedido legítimo.
    return hmac.compare_digest(esperada, signature.strip().lower())


def _explicar_error(error, description):
    """
    Turn Tienda Nube's OAuth errors into something actionable.

    The two failures look alike from the terminal and have opposite fixes, and
    guessing wrong costs a round trip through the browser each time.
    """
    if error == 'invalid_grant':
        return (
            f"Tienda Nube rechazó el código ({description}). "
            f"Suele ser que venció: dura 5 minutos. Volvé a instalar la app "
            f"para obtener uno nuevo."
        )
    if error == 'invalid_client':
        return (
            f"Tienda Nube rechazó las credenciales de la app ({description}). "
            f"Revisá TIENDANUBE_CLIENT_ID y TIENDANUBE_CLIENT_SECRET contra "
            f"«Claves de Acceso» del panel de partners."
        )
    return f"Tienda Nube rechazó el intercambio: {error or ''} {description}".strip()


class TiendanubeClient:
    """
    Authenticated client for one store.

    Scoped to an integration on purpose: the store id and the token always
    travel together, so there is no way to call one store with another's token.
    """

    PER_PAGE = 200
    # Guard contra una paginación que no termine nunca.
    MAX_PAGES = 50

    def __init__(self, integration, session=None):
        self.integration = integration
        self.session = session or requests.Session()

    def get_store(self):
        """Read the store, to confirm the token works and name the link."""
        return self._request('GET', 'store')

    def iter_products(self):
        """
        Yield the store's products, following pagination.

        Read-only, y es el único lugar donde se lee el catálogo de Tienda Nube:
        sirve para emparejar cada `Producto` nuestro con su variante (§5.2). El
        stock y los precios siguen viniendo por Conto.
        """
        for page in range(1, self.MAX_PAGES + 1):
            lote = self._request(
                'GET', 'products', params={'page': page, 'per_page': self.PER_PAGE}
            ) or []
            if not lote:
                return
            yield from lote
            if len(lote) < self.PER_PAGE:
                return

    def create_coupon(self, payload):
        """Create a coupon. `payload` goes as Tienda Nube documents it."""
        return self._request('POST', 'coupons', json=payload)

    def delete_coupon(self, coupon_id):
        """
        Delete a coupon in Tienda Nube.

        A 404 is success as far as the caller is concerned: the coupon is gone,
        which is the point. Treating it as an error would make the cleanup
        command retry the same rows forever.
        """
        try:
            return self._request('DELETE', f'coupons/{coupon_id}')
        except TiendanubeError as exc:
            if '404' in str(exc):
                return None
            raise

    # -- internals --------------------------------------------------------- #

    def _request(self, method, path, **kwargs):
        url = f"{API_BASE_URL}/{self.integration.store_id}/{path.lstrip('/')}"
        headers = {
            # Not "Bearer": Tienda Nube uses its own `Authentication` header.
            'Authentication': f'bearer {self.integration.token}',
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/json',
        }

        try:
            response = self.session.request(
                method, url, headers=headers, timeout=TIMEOUT, **kwargs
            )
        except requests.RequestException as exc:
            raise TiendanubeUnavailable(f"No se pudo conectar con Tienda Nube: {exc}") from exc

        if response.status_code in (401, 403):
            raise TiendanubeAuthError(
                "Tienda Nube rechazó el token. Puede que el centro haya "
                "desinstalado la app."
            )
        if response.status_code >= 500:
            raise TiendanubeUnavailable(f"Tienda Nube devolvió {response.status_code}.")
        if response.status_code >= 400:
            raise TiendanubeError(
                f"Tienda Nube devolvió {response.status_code}: {response.text[:300]}"
            )

        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise TiendanubeError("Tienda Nube devolvió una respuesta que no es JSON") from exc

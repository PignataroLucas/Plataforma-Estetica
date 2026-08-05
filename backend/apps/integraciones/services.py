"""
HTTP client and tenant-scoped database access for the Conto integration.

Two responsibilities, deliberately split:

- `ContoClient` talks to Conto over HTTP. It knows nothing about our models.
- `ContoScope` is the ONLY place that resolves Conto data against our database.
  Every lookup it performs is filtered by the integration's branch or center.

The split matters because the sync runs in Celery, where there is no
`request.user` and therefore none of the tenant filtering the view layer relies
on. Funnelling every lookup through `ContoScope` means there is no second path
that could forget the filter. See INTEGRACION_CONTO_SPEC.md §3.
"""
import logging
import re
from datetime import timezone as datetime_timezone
from urllib.parse import urlparse

import requests

from apps.clientes.models import Cliente
from apps.inventario.models import Producto

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #

class ContoError(Exception):
    """Base error for the Conto integration"""


class ContoNotLinked(ContoError):
    """The integration has no verified account id, so it must not sync"""


class ContoAuthError(ContoError):
    """Token missing, invalid or revoked (401). Needs a visible alert"""


class ContoAccountInactive(ContoError):
    """The Conto account is disabled (403)"""


class ContoAccountMismatch(ContoError):
    """
    The account id in the response is not the one this integration is linked to.

    This is the isolation tripwire: it means the token was swapped or the
    account migrated, and importing would write another business's data into
    this tenant. Always fails closed.
    """


class ContoBadRequest(ContoError):
    """Malformed request (400)"""


class ContoUnavailable(ContoError):
    """Network failure or 5xx. Retryable"""


# --------------------------------------------------------------------------- #
# HTTP client
# --------------------------------------------------------------------------- #

class ContoClient:
    """
    Read-only client for the Conto API.

    Contract documented in CONTO_API_REQUIREMENTS.md.
    """

    USER_AGENT = 'Plataforma Estetica (integraciones)'
    TIMEOUT = 20
    # Guard against a malformed `next` chain looping forever.
    MAX_PAGES = 500

    def __init__(self, integration, session=None):
        self.integration = integration
        self.base_url = integration.base_url.rstrip('/')
        self.session = session or requests.Session()

    # -- public API -------------------------------------------------------- #

    def get_account(self):
        """
        Fetch the account this token belongs to.

        This is the one call that does NOT check the tripwire: it is what
        establishes the identity in the first place.
        """
        return self._request(f'{self.base_url}/api/cuenta/')

    def iter_stock(self, since=None):
        """Yield catalog entries, following pagination."""
        params = {}
        if since:
            params['desde'] = self._format_timestamp(since)
        yield from self._paginate(f'{self.base_url}/api/stock/', params)

    def iter_sales(self, since):
        """Yield vouchers updated at or after `since`, following pagination."""
        params = {'desde': self._format_timestamp(since)}
        yield from self._paginate(f'{self.base_url}/api/ventas/', params)

    # -- internals --------------------------------------------------------- #

    @staticmethod
    def _format_timestamp(value):
        """ISO 8601 in UTC with a trailing Z, as the contract requires."""
        return value.astimezone(datetime_timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def _paginate(self, url, params):
        """
        Walk the `results` / `next` envelope, verifying the account on every page.

        The tripwire runs per page, not just on the first one: a token could in
        principle stop resolving to the same account mid-walk.
        """
        expected = self.integration.conto_account_id
        if not expected:
            raise ContoNotLinked(
                "La integración no tiene una cuenta verificada. "
                "Verificá la vinculación antes de sincronizar."
            )

        next_url = url
        for page in range(self.MAX_PAGES):
            payload = self._request(next_url, params if page == 0 else None)

            received = payload.get('cuenta_id')
            if received != expected:
                raise ContoAccountMismatch(
                    f"La respuesta de Conto pertenece a la cuenta {received!r} "
                    f"y esta integración está vinculada a {expected!r}. "
                    f"Sincronización abortada."
                )

            for item in payload.get('results') or []:
                yield item

            next_url = payload.get('next')
            if not next_url:
                return
            self._assert_same_origin(next_url)
        else:
            raise ContoError(
                f"La paginación superó {self.MAX_PAGES} páginas. "
                f"Puede haber un bucle en el campo 'next'."
            )

    def _assert_same_origin(self, url):
        """
        The `next` URL comes from the response body, so it is untrusted input.

        Following it blindly would let a compromised or misconfigured response
        redirect our authenticated requests elsewhere.
        """
        expected = urlparse(self.base_url)
        received = urlparse(url)
        if (received.scheme, received.netloc) != (expected.scheme, expected.netloc):
            raise ContoError(
                f"El campo 'next' apunta a otro origen ({received.netloc}), "
                f"se esperaba {expected.netloc}"
            )

    def _request(self, url, params=None):
        """Perform the request and map transport/status errors to our exceptions."""
        headers = {
            'Authorization': f'Bearer {self.integration.token}',
            'User-Agent': self.USER_AGENT,
            'Accept': 'application/json',
        }

        try:
            response = self.session.request(
                'GET', url, params=params, headers=headers, timeout=self.TIMEOUT
            )
        except requests.RequestException as exc:
            raise ContoUnavailable(f"No se pudo conectar con Conto: {exc}") from exc

        status = response.status_code

        if status == 401:
            raise ContoAuthError(
                "Conto rechazó el token (401). Puede haber sido revocado o rotado."
            )
        if status == 403:
            raise ContoAccountInactive("La cuenta de Conto está desactivada (403).")
        if status == 400:
            raise ContoBadRequest(f"Conto rechazó la consulta (400): {response.text[:300]}")
        if status >= 500:
            raise ContoUnavailable(f"Conto devolvió {status}.")
        if status != 200:
            raise ContoError(f"Conto devolvió un estado inesperado: {status}")

        try:
            return response.json()
        except ValueError as exc:
            raise ContoError("Conto devolvió una respuesta que no es JSON") from exc


# --------------------------------------------------------------------------- #
# Tenant-scoped database access
# --------------------------------------------------------------------------- #

class ContoScope:
    """
    Resolves Conto payloads against our database, always within one tenant.

    Every method here filters by the integration's branch or center. Nothing
    outside this class should look up a Producto or Cliente during a sync.
    """

    def __init__(self, integration):
        self.integration = integration
        self.branch = integration.branch
        self.branch_id = integration.branch_id
        self.center = integration.center

    # -- normalization ----------------------------------------------------- #

    @staticmethod
    def normalize_sku(sku):
        return (sku or '').strip().upper()

    @staticmethod
    def normalize_email(email):
        return (email or '').strip().lower()

    @staticmethod
    def normalize_phone(phone):
        """Reduce to digits so formatting differences do not block a match."""
        return re.sub(r'\D', '', phone or '')

    # -- products ---------------------------------------------------------- #

    def find_product(self, sku):
        """
        Find a product by SKU **within this integration's branch**.

        Returns None when the SKU is missing, unknown, or matches more than one
        product. Ambiguity is treated as "not found" on purpose: `Producto.sku`
        is not unique yet, and guessing would attribute income to the wrong
        product and decrement the wrong stock.
        """
        normalized = self.normalize_sku(sku)
        if not normalized:
            return None

        matches = list(
            Producto.objects.filter(
                sucursal=self.branch,
                sku__iexact=normalized,
            )[:2]
        )

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            logger.warning(
                "SKU ambiguo %r en la sucursal %s: matchea más de un producto",
                normalized, self.branch_id,
            )
        return None

    def create_product(self, sku, name, cost, price, stock=0, active=True):
        """
        Create a product mirrored from Conto.

        Created with `stock_actual=0` and the stock set afterwards through a
        queryset update. Creating it with stock and cost already set would fire
        `create_initial_stock_movement`, which generates an ENTRADA movement and,
        through it, a phantom purchase expense — the center did not buy this
        stock now, it already had it. A queryset update does not fire signals.

        See apps/inventario/signals.py:11 and INTEGRACION_CONTO_SPEC.md §4.1.
        """
        producto = Producto.objects.create(
            sucursal=self.branch,
            nombre=name,
            sku=self.normalize_sku(sku),
            precio_costo=cost or 0,
            precio_venta=price or 0,
            stock_actual=0,
            activo=active,
        )

        if stock:
            Producto.objects.filter(pk=producto.pk).update(stock_actual=stock)
            producto.stock_actual = stock

        logger.info(
            "Producto creado desde Conto: %s (sku %s) en sucursal %s",
            name, self.normalize_sku(sku), self.branch_id,
        )
        return producto

    def update_stock(self, producto, stock=None, cost=None, price=None):
        """
        Push Conto's values onto an existing product without creating movements.

        The real inventory movement happened in Conto. Creating a
        `MovimientoInventario` here would generate a phantom financial
        transaction on every sync.
        """
        fields = {}
        if stock is not None:
            fields['stock_actual'] = stock
        if cost is not None:
            fields['precio_costo'] = cost
        if price is not None:
            fields['precio_venta'] = price

        if not fields:
            return False

        Producto.objects.filter(pk=producto.pk, sucursal=self.branch).update(**fields)
        return True

    # -- clients ----------------------------------------------------------- #

    def find_client(self, email=None, phone=None):
        """
        Find a client by email, then by phone, **within this center**.

        The center filter is not optional: the same person can legitimately be a
        client of two different centers with the same email address, and they
        are two separate records.
        """
        queryset = Cliente.objects.filter(centro_estetica=self.center)

        normalized_email = self.normalize_email(email)
        if normalized_email:
            match = queryset.filter(email__iexact=normalized_email).first()
            if match:
                return match

        digits = self.normalize_phone(phone)
        if len(digits) >= 8:
            # Compare on digits only, so "+54 9 11 3333-4444" and "1133334444"
            # can match. Requires 8+ digits to avoid absurd collisions.
            for candidate in queryset.exclude(telefono='').only('id', 'telefono'):
                candidate_digits = self.normalize_phone(candidate.telefono)
                if candidate_digits and self._phones_match(digits, candidate_digits):
                    return candidate

        return None

    @staticmethod
    def _phones_match(left, right):
        """
        Argentine numbers arrive with and without country code and the mobile 9.

        Comparing the last 8 digits is what actually works in practice; anything
        stricter fails on real data and anything looser starts colliding.
        """
        return left[-8:] == right[-8:]

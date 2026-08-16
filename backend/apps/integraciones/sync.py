"""
Synchronization logic for the Conto integration.

Plain classes with no Celery involved, so they can be tested directly. The
Celery tasks in tasks.py are thin wrappers around these.

Two flows with different semantics:

- `StockSynchronizer` pulls state. It overwrites local values and never creates
  inventory movements — the real movement happened in Conto.
- `SalesImporter` pulls events. It creates financial transactions and never
  touches stock, which arrives through the other flow.

Keeping stock out of the sales import is not an optimization: creating a
`MovimientoInventario` here would decrement stock twice and duplicate the
transaction through the inventory signal.
"""
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction as db_transaction
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.finanzas.models import Transaction, TransactionCategory

from .models import ContoSale
from .services import ContoClient, ContoError, ContoScope

logger = logging.getLogger(__name__)

# Sales are pulled with a window that overlaps the previous run, to cover clock
# skew between the two systems. Duplicates are absorbed by the uniqueness of
# (integration, voucher_id).
SALES_OVERLAP = timedelta(minutes=5)

ZERO = Decimal('0.00')

# Conto's `medio_pago` values, confirmed by their team: six, not the two
# originally reported. Anything unlisted falls back to the integration's
# configured default rather than being guessed.
#
# `card` is deliberately absent: it says a card was used but not which gateway
# processed it, so it is resolved through `gateway_origen` instead.
PAYMENT_METHOD_MAP = {
    'cash': Transaction.PaymentMethod.CASH,
    'transfer': Transaction.PaymentMethod.BANK_TRANSFER,
    'mercadopago': Transaction.PaymentMethod.MERCADOPAGO,
    # Mercado Libre settles through Mercado Pago.
    'mercadolibre': Transaction.PaymentMethod.MERCADOPAGO,
    # No cheque option exists on our side.
    'check': Transaction.PaymentMethod.OTHER,
}

# Matched against `gateway_origen`, which Conto exposes raw from Tienda Nube.
#
# Keys are normalized (lowercase, letters and digits only) because the real
# values arrive hyphenated — `mercado-pago`, `pago-nube` — and enumerating every
# spelling variant is how this silently stops matching.
GATEWAY_MAP = {
    'mercadopago': Transaction.PaymentMethod.MERCADOPAGO,
    # Pago Nube is Tienda Nube's own card gateway, not Mercado Pago. Mapping it
    # to MERCADOPAGO would put money in the wrong bucket of the cash breakdown;
    # OTHER is at least honest. Revisit if the split matters.
    'pagonube': Transaction.PaymentMethod.OTHER,
}


def normalize_gateway(value):
    """Lowercase and strip anything that is not a letter or a digit."""
    return re.sub(r'[^a-z0-9]', '', (value or '').lower())


def to_decimal(value):
    """Conto may send amounts as numbers or strings; both must parse exactly."""
    if value is None or value == '':
        return ZERO
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def optional_decimal(value, voucher_id=None, label='monto'):
    """
    Like `to_decimal`, but keeps "not reported" apart from zero.

    `to_decimal` maps a missing value to zero, which is right for amounts that
    have to add up. For the coupon discount the absence is the information: a
    column full of nulls is how we find out Conto never shipped the field.

    An unparseable value is logged and dropped rather than raised. Conto added
    these fields without being able to compile (COMPRA_EN_APP_SPEC.md §7.1), and
    failing a voucher whose money is real over a field nothing reads yet would
    be the wrong trade. The raw value stays in `payload` either way.
    """
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        logger.warning(
            "Voucher %s de Conto: %s ilegible (%r), se guarda vacío",
            voucher_id, label, value,
        )
        return None


def raw_origin_fields(voucher):
    """
    Conto's origin and coupon fields, verbatim, as `ContoSale` column values.

    Nothing here interprets them. Matching a code against the coupons the app
    issues is COMPRA_EN_APP_SPEC.md §5.6 and does not exist yet; this only makes
    sure the data is on the row when it does — see the model for why `payload`
    is not enough.

    Values are truncated to their column width instead of being trusted: one
    long string would abort the import of a real sale over a field nobody reads.
    """
    return {
        'sale_origin': str(voucher.get('origen_venta') or '')[:50],
        'app_origin': str(voucher.get('app_origen') or '')[:100],
        'coupon_code': str(voucher.get('cupon') or '')[:200],
        'coupon_discount': optional_decimal(
            voucher.get('descuento_cupon'),
            voucher_id=voucher.get('id'),
            label='descuento_cupon',
        ),
    }


def get_income_category(branch, name):
    """
    Resolve an income category, creating it if the branch does not have it.

    Follows the pattern already used across the project (filter().first() then
    create) rather than get_or_create, because these categories may exist
    without being system categories.
    """
    category = TransactionCategory.objects.filter(
        branch=branch, name=name, type='INCOME', parent_category__isnull=True
    ).first()
    if category:
        return category
    return TransactionCategory.objects.create(
        branch=branch, name=name, type='INCOME',
        is_system_category=True, color='#059669', order=9,
    )


def get_expense_category(branch, name):
    category = TransactionCategory.objects.filter(
        branch=branch, name=name, type='EXPENSE', parent_category__isnull=True
    ).first()
    if category:
        return category
    return TransactionCategory.objects.create(
        branch=branch, name=name, type='EXPENSE',
        is_system_category=True, color='#EF4444', order=9,
    )


# --------------------------------------------------------------------------- #
# Stock
# --------------------------------------------------------------------------- #

@dataclass
class StockSyncResult:
    updated: int = 0
    created: int = 0
    unmatched: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def summary(self):
        return (
            f"{self.updated} actualizados, {self.created} creados, "
            f"{len(self.unmatched)} sin match, {len(self.errors)} con error"
        )


class StockSynchronizer:
    """Pulls the catalog state from Conto onto our products."""

    def __init__(self, integration, client=None):
        self.integration = integration
        self.client = client or ContoClient(integration)
        self.scope = ContoScope(integration)

    def run(self, full=False):
        # Captured before the pull: anything modified during the pull must be
        # picked up by the next run, not skipped.
        started_at = timezone.now()
        since = None if full else self.integration.last_stock_sync

        result = StockSyncResult()

        for item in self.client.iter_stock(since=since):
            try:
                self._process(item, result)
            except Exception as exc:
                logger.exception("Error sincronizando stock de Conto")
                result.errors.append(f"{item.get('sku')}: {exc}")

        self.integration.last_stock_sync = started_at
        self.integration.save(update_fields=['last_stock_sync', 'updated_at'])

        logger.info("Sync de stock de Conto: %s", result.summary)
        return result

    def _process(self, item, result):
        sku = item.get('sku')
        if not self.scope.normalize_sku(sku):
            result.unmatched.append(item.get('nombre') or '(sin sku ni nombre)')
            return

        stock = to_decimal(item.get('stock'))
        cost = to_decimal(item.get('costo'))
        price = to_decimal(item.get('precio'))

        producto = self.scope.find_product(sku)

        if producto:
            self.scope.update_stock(
                producto,
                stock=stock,
                cost=cost or None,
                price=price or None,
            )
            result.updated += 1
            return

        if not self.integration.create_missing_products:
            result.unmatched.append(sku)
            return

        self.scope.create_product(
            sku=sku,
            name=item.get('nombre') or sku,
            cost=cost,
            price=price,
            stock=stock,
            active=item.get('activo', True),
        )
        result.created += 1


# --------------------------------------------------------------------------- #
# Sales
# --------------------------------------------------------------------------- #

@dataclass
class SalesImportResult:
    processed: int = 0
    skipped: int = 0
    reverted: int = 0
    pending: int = 0
    errors: list = field(default_factory=list)

    @property
    def summary(self):
        return (
            f"{self.processed} procesadas, {self.skipped} omitidas, "
            f"{self.reverted} revertidas, {self.pending} pendientes, "
            f"{len(self.errors)} con error"
        )


class SalesImporter:
    """
    Imports Conto vouchers as financial transactions.

    Every voucher is stored raw before being processed, so a failure can be
    reprocessed without querying Conto again.
    """

    PAID = 'PAGADO'
    CANCELLED = 'CANCELADO'

    def __init__(self, integration, client=None):
        self.integration = integration
        self.client = client or ContoClient(integration)
        self.scope = ContoScope(integration)

    # -- entry point ------------------------------------------------------- #

    def run(self):
        started_at = timezone.now()
        since = self._window_start()

        result = SalesImportResult()

        for voucher in self.client.iter_sales(since):
            try:
                with db_transaction.atomic():
                    self._process(voucher, result)
            except ContoError:
                # Transport and isolation errors must abort the whole run.
                raise
            except Exception as exc:
                logger.exception(
                    "Error procesando voucher %s de Conto", voucher.get('id')
                )
                self._mark_error(voucher, exc)
                result.errors.append(f"{voucher.get('id')}: {exc}")

        self.integration.last_sales_sync = started_at
        self.integration.save(update_fields=['last_sales_sync', 'updated_at'])

        logger.info("Import de ventas de Conto: %s", result.summary)
        return result

    def reprocess(self, sale):
        """
        Re-run a single stored voucher without querying Conto.

        Used after fixing whatever made it fail — a missing product, a mapping
        correction. The raw payload was kept precisely so this is possible.
        """
        result = SalesImportResult()
        try:
            with db_transaction.atomic():
                self._process(sale.payload, result)
        except Exception as exc:
            logger.exception("Error reprocesando voucher %s", sale.voucher_id)
            self._mark_error(sale.payload, exc)
            result.errors.append(f"{sale.voucher_id}: {exc}")
        return result

    def _window_start(self):
        """
        Where to start pulling from.

        On the first run there is no cursor, so `import_from` decides. It is
        required on purpose: without it the first run would try to pull the
        entire history of the account.
        """
        if self.integration.last_sales_sync:
            return self.integration.last_sales_sync - SALES_OVERLAP

        if not self.integration.import_from:
            raise ContoError(
                "La integración no tiene 'importar desde' configurado. "
                "Definí esa fecha antes de la primera sincronización de ventas."
            )
        return self.integration.import_from

    # -- per voucher ------------------------------------------------------- #

    def _process(self, voucher, result):
        voucher_id = str(voucher.get('id') or '').strip()
        if not voucher_id:
            raise ValueError("El voucher no trae 'id'")

        is_credit_note = (voucher.get('tipo') or '').upper() == 'NOTA_CREDITO'
        status = (voucher.get('estado') or '').upper()
        channel = voucher.get('canal') or ''

        sale, _ = ContoSale.objects.get_or_create(
            integration=self.integration,
            voucher_id=voucher_id,
            defaults={'payload': voucher, 'channel': channel},
        )

        # Always refresh the stored snapshot, including on reprocesses.
        sale.payload = voucher
        sale.channel = channel
        sale.type = (
            ContoSale.VoucherType.CREDIT_NOTE if is_credit_note
            else ContoSale.VoucherType.SALE
        )
        sale.related_voucher_id = str(voucher.get('relacionada_con') or '')
        sale.external_order_id = str(voucher.get('orden_externa_id') or '')
        sale.date = self._parse_date(voucher.get('fecha'))
        sale.total = to_decimal(voucher.get('total'))

        # Copied before the early returns below on purpose: a voucher that is
        # skipped or still pending today may be reprocessed once the attribution
        # exists, and it should carry its origin by then.
        for name, value in raw_origin_fields(voucher).items():
            setattr(sale, name, value)

        if channel not in (self.integration.channels_to_import or []):
            self._set_status(sale, ContoSale.Status.SKIPPED)
            result.skipped += 1
            return

        # `import_from` has to be enforced here, on the sale date, not just as
        # the API cursor. Conto filters `desde` by `actualizado_en`, so an old
        # voucher touched recently arrives with its original date — which would
        # import periods the center already loaded by hand and double-count the
        # revenue. Ask for a window and you get updates, not dates.
        if self._is_before_import_window(sale.date):
            self._set_status(sale, ContoSale.Status.SKIPPED)
            result.skipped += 1
            return

        if status == self.CANCELLED:
            reverted = self._revert(sale)
            self._set_status(sale, ContoSale.Status.SKIPPED)
            result.reverted += 1 if reverted else 0
            result.skipped += 0 if reverted else 1
            return

        if status != self.PAID:
            # Not paid yet. Conto bumps `actualizado_en` when it changes, so the
            # next window will bring it back.
            self._set_status(sale, ContoSale.Status.PENDING)
            result.pending += 1
            return

        if sale.status == ContoSale.Status.PROCESSED:
            sale.save()
            return

        if is_credit_note:
            handled = self._process_credit_note(sale, voucher)
        else:
            handled = self._process_sale(sale, voucher)

        if handled:
            result.processed += 1
        else:
            result.pending += 1

    def _is_before_import_window(self, sale_date):
        """
        True when the sale predates `import_from` and must not be imported.

        Compared in local time, because `import_from` is set by a human thinking
        in calendar days and `fecha` already arrives resolved in Argentine time.
        """
        if not sale_date or not self.integration.import_from:
            return False
        return sale_date < timezone.localtime(self.integration.import_from).date()

    # -- sales ------------------------------------------------------------- #

    def _process_sale(self, sale, voucher):
        branch = self.integration.branch
        payment_method = self._payment_method(voucher)
        client = self._resolve_client(voucher.get('cliente'))
        date = sale.date or timezone.localdate()

        items = voucher.get('items') or []
        product_items = [i for i in items if self._item_type(i) == 'PRODUCTO']
        other_items = [i for i in items if self._item_type(i) in ('ENVIO', 'OTRO')]
        discount_total = sum(
            (self._line_total(i) for i in items if self._item_type(i) == 'DESCUENTO'),
            ZERO,
        )

        discounts = self._spread_discount(discount_total, product_items, other_items)

        created = []

        product_category = get_income_category(branch, 'Productos')
        for index, item in enumerate(product_items):
            amount = self._line_total(item) - discounts['product'][index]
            producto = self.scope.find_product(item.get('sku'))
            created.append(Transaction.objects.create(
                branch=branch,
                category=product_category,
                client=client,
                product=producto,
                type='INCOME_PRODUCT',
                amount=amount,
                payment_method=payment_method,
                date=date,
                description=self._description(item, voucher),
                notes=self._notes(voucher, producto, item),
                auto_generated=True,
            ))

        if other_items:
            other_category = get_income_category(branch, 'Otros Ingresos')
            for index, item in enumerate(other_items):
                amount = self._line_total(item) - discounts['other'][index]
                if amount <= ZERO:
                    continue
                created.append(Transaction.objects.create(
                    branch=branch,
                    category=other_category,
                    client=client,
                    type='INCOME_OTHER',
                    amount=amount,
                    payment_method=payment_method,
                    date=date,
                    description=self._description(item, voucher),
                    notes=self._notes(voucher, None, item),
                    auto_generated=True,
                ))

        if not created:
            raise ValueError(
                "El voucher no generó ninguna transacción: no trae ítems cobrables"
            )

        sale.transactions.set(created)
        sale.total_discrepancy = self._reconcile(created, voucher)
        self._set_status(sale, ContoSale.Status.PROCESSED, processed=True)
        return True

    def _reconcile(self, created, voucher):
        """
        Check our income adds up to what Conto says the customer paid.

        `total` comes straight from Tienda Nube's `order.total`, and Conto
        confirmed the line items — summed with the sign of their type — equal it
        exactly. So a difference is not a judgement call about shipping: it means
        our breakdown is wrong, or Conto is sending something unexpected.

        Returns the difference, or None when it reconciles. The sale is imported
        either way: the money did come in, and dropping it would be worse than
        importing it flagged.
        """
        declared = to_decimal(voucher.get('total'))
        if declared <= ZERO:
            return None

        imported = sum((t.amount for t in created), ZERO)
        difference = imported - declared

        if abs(difference) <= Decimal('0.01'):
            return None

        logger.warning(
            "Voucher %s de Conto no cuadra: importamos %s y el total declarado "
            "es %s (diferencia %s)",
            voucher.get('id'), imported, declared, difference,
        )
        return difference

    def _spread_discount(self, discount_total, product_items, other_items):
        """
        Spread a discount across the lines it applies to.

        `Transaction.amount` is positive by design, so a discount cannot be its
        own negative line. It is prorated over the product lines; if there are
        none, it comes off shipping. With neither, the caller raises rather than
        silently dropping money.
        """
        empty = {
            'product': [ZERO] * len(product_items),
            'other': [ZERO] * len(other_items),
        }
        if discount_total <= ZERO:
            return empty

        targets, key = (
            (product_items, 'product') if product_items
            else (other_items, 'other')
        )
        if not targets:
            raise ValueError(
                f"El voucher trae un descuento de {discount_total} sin líneas "
                f"sobre las que prorratearlo"
            )

        subtotals = [self._line_total(item) for item in targets]
        base = sum(subtotals, ZERO)
        if base <= ZERO:
            raise ValueError("No se puede prorratear el descuento sobre líneas en cero")

        shares = []
        allocated = ZERO
        for subtotal in subtotals[:-1]:
            share = (discount_total * subtotal / base).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            shares.append(share)
            allocated += share
        # The last line absorbs the rounding remainder so the sum matches exactly.
        shares.append(discount_total - allocated)

        result = dict(empty)
        result[key] = shares
        return result

    # -- credit notes ------------------------------------------------------ #

    def _process_credit_note(self, sale, voucher):
        """
        A credit note compensates instead of reverting the original sale.

        Credit notes can be partial, and reverting only works when total. One
        uniform path beats two behaviours for the same event, and it leaves the
        trace that a refund happened.
        """
        if sale.related_voucher_id:
            original = ContoSale.objects.filter(
                integration=self.integration,
                voucher_id=sale.related_voucher_id,
            ).first()
            if not original:
                # The note arrived before the sale it references. Next window.
                self._set_status(sale, ContoSale.Status.PENDING)
                return False

        amount = to_decimal(voucher.get('total'))
        if amount <= ZERO:
            raise ValueError("La nota de crédito no trae un total válido")

        category = get_expense_category(self.integration.branch, 'Devoluciones')
        reference = sale.related_voucher_id or 's/d'

        compensating = Transaction.objects.create(
            branch=self.integration.branch,
            category=category,
            client=self._resolve_client(voucher.get('cliente')),
            type='EXPENSE',
            amount=amount,
            payment_method=self._payment_method(voucher),
            date=sale.date or timezone.localdate(),
            description=f"Nota de crédito Conto {sale.voucher_id}"[:300],
            notes=f"Reversa la venta {reference}. Canal: {sale.channel}.",
            auto_generated=True,
        )

        sale.transactions.set([compensating])
        self._set_status(sale, ContoSale.Status.PROCESSED, processed=True)
        return True

    # -- cancellations ----------------------------------------------------- #

    def _revert(self, sale):
        """
        Undo a voucher that came back cancelled.

        Reverting rather than compensating is correct here: a cancellation is
        total by definition. The payload is kept.
        """
        existing = list(sale.transactions.all())
        if not existing:
            return False

        sale.transactions.clear()
        for tx in existing:
            tx.delete()

        logger.info(
            "Voucher %s cancelado en Conto: %s transacciones revertidas",
            sale.voucher_id, len(existing),
        )
        return True

    # -- helpers ----------------------------------------------------------- #

    @staticmethod
    def _item_type(item):
        return (item.get('tipo') or 'PRODUCTO').upper()

    @staticmethod
    def _line_total(item):
        quantity = to_decimal(item.get('cantidad') or 1)
        unit = to_decimal(item.get('precio_unitario'))
        return (quantity * unit).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def _parse_date(value):
        """`fecha` arrives as YYYY-MM-DD, already resolved in Argentine time."""
        if not value:
            return None
        try:
            return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Fecha inválida en el voucher: {value!r}")

    def _payment_method(self, voucher):
        """
        Resolve the payment method, preferring the most specific signal.

        `gateway_origen` wins when recognised: it is the raw gateway Tienda Nube
        reports, so it distinguishes Pago Nube from Mercado Pago, which
        `medio_pago` cannot when it says `card`.

        Conto's notes field is never parsed. For dealership sales the real method
        only exists there as free text, which is the fragility both sides agreed
        to avoid — and that channel is not imported anyway.

        See INTEGRACION_CONTO_SPEC.md §5.2.
        """
        gateway = normalize_gateway(voucher.get('gateway_origen'))
        if gateway in GATEWAY_MAP:
            return GATEWAY_MAP[gateway]

        method = (voucher.get('medio_pago') or '').strip().lower()
        if method in PAYMENT_METHOD_MAP:
            return PAYMENT_METHOD_MAP[method]

        # `card` with an unknown or absent gateway, or a value Conto adds later.
        return self.integration.default_payment_method

    def _resolve_client(self, data):
        if not data:
            return None

        email = data.get('email')
        phone = data.get('telefono')

        existing = self.scope.find_client(email=email, phone=phone)
        if existing:
            return existing

        if not self.integration.create_missing_clients:
            return None

        full_name = (data.get('nombre') or '').strip()
        if not full_name and not email:
            return None

        first, _, last = full_name.partition(' ')
        return Cliente.objects.create(
            centro_estetica=self.integration.center,
            nombre=first or 'Sin nombre',
            apellido=last or '',
            email=self.scope.normalize_email(email),
            telefono=(phone or '')[:20],
            detalle_general='Cliente creado automáticamente desde Conto',
        )

    @staticmethod
    def _description(item, voucher):
        quantity = item.get('cantidad') or 1
        name = item.get('nombre') or 'Ítem'
        order = voucher.get('orden_externa_id')
        base = f"{quantity}x {name}"
        if order:
            base = f"{base} (orden {order})"
        return base[:300]

    def _notes(self, voucher, producto, item):
        parts = [f"Importado de Conto. Canal: {voucher.get('canal')}."]
        if not producto and self._item_type(item) == 'PRODUCTO':
            parts.append(
                f"SKU {item.get('sku') or 's/d'} sin producto asociado en la sucursal."
            )
        gateway = voucher.get('gateway_origen')
        if gateway:
            parts.append(f"Gateway: {gateway}.")
        return ' '.join(parts)

    @staticmethod
    def _set_status(sale, status, processed=False):
        sale.status = status
        sale.error_message = ''
        if processed:
            sale.processed_at = timezone.now()
        sale.save()

    def _mark_error(self, voucher, exc):
        """
        Record the failure outside the rolled-back transaction.

        The atomic block around `_process` is gone by the time we get here, so
        this write survives.
        """
        voucher_id = str(voucher.get('id') or '')
        if not voucher_id:
            return
        ContoSale.objects.update_or_create(
            integration=self.integration,
            voucher_id=voucher_id,
            defaults={
                'payload': voucher,
                'channel': voucher.get('canal') or '',
                **raw_origin_fields(voucher),
                'status': ContoSale.Status.ERROR,
                'error_message': str(exc)[:2000],
            },
        )

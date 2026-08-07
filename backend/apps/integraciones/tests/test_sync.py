"""
Tests for the stock synchronizer and the sales importer.

Uses a stub client instead of HTTP mocks: what matters here is the accounting
behaviour — how many transactions get created, for how much, and what happens
when a voucher comes back changed.
"""
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoSale
from apps.integraciones.services import ContoError
from apps.integraciones.sync import SalesImporter, StockSynchronizer
from apps.inventario.models import MovimientoInventario, Producto

from .test_services import make_center, make_product


class FakeClient:
    """Stands in for ContoClient, yielding canned payloads."""

    def __init__(self, stock=None, sales=None):
        self._stock = stock or []
        self._sales = sales or []
        self.stock_calls = []
        self.sales_calls = []

    def iter_stock(self, since=None):
        self.stock_calls.append(since)
        yield from self._stock

    def iter_sales(self, since):
        self.sales_calls.append(since)
        yield from self._sales


def stock_item(sku='SER-VITC-30', name='Serum Vitamina C 30ml',
               stock=12, cost='9200.00', price='18500.00', active=True):
    return {
        'sku': sku, 'nombre': name, 'stock': stock,
        'costo': cost, 'precio': price, 'activo': active,
        'actualizado_en': '2026-08-04T14:22:10Z',
    }


def product_line(sku='SER-VITC-30', name='Serum', quantity=1,
                 unit='18500.00', cost='9200.00'):
    return {
        'tipo': 'PRODUCTO', 'sku': sku, 'nombre': name,
        'cantidad': quantity, 'precio_unitario': unit, 'costo_unitario': cost,
    }


def voucher(voucher_id='8891', items=None, total='18500.00', status='PAGADO',
            channel='tiendanube', kind='VENTA', related=None,
            payment='card', gateway='mercadopago', client=None,
            date='2026-08-04'):
    return {
        'id': voucher_id,
        'tipo': kind,
        'relacionada_con': related,
        'canal': channel,
        'orden_externa_id': 'TN-12345',
        'fecha': date,
        'actualizado_en': '2026-08-04T14:22:10Z',
        'estado': status,
        'medio_pago': payment,
        'gateway_origen': gateway,
        'total': total,
        'cliente': client,
        'items': items if items is not None else [product_line()],
    }


def make_syncable_center(name, account_id, **kwargs):
    """A center whose integration is active, verified and ready to import."""
    center, branch, integration = make_center(name, account_id)
    integration.link_verified_at = timezone.now()
    integration.import_from = timezone.now() - timezone.timedelta(days=30)
    for key, value in kwargs.items():
        setattr(integration, key, value)
    integration.save()
    return center, branch, integration


# --------------------------------------------------------------------------- #
# Stock
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestStockSynchronizer:

    def test_updates_existing_product_without_creating_movements(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        producto = make_product(branch, 'SER-VITC-30', stock=0, cost='1.00', price='2.00')

        client = FakeClient(stock=[stock_item()])
        result = StockSynchronizer(integration, client=client).run()

        producto.refresh_from_db()
        assert result.updated == 1
        assert producto.stock_actual == Decimal('12.00')
        assert producto.precio_costo == Decimal('9200.00')
        assert MovimientoInventario.objects.count() == 0
        assert Transaction.objects.count() == 0

    def test_creates_missing_product_without_phantom_expense(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')

        client = FakeClient(stock=[stock_item()])
        result = StockSynchronizer(integration, client=client).run()

        producto = Producto.objects.get(sucursal=branch, sku='SER-VITC-30')
        assert result.created == 1
        assert producto.stock_actual == Decimal('12.00')
        assert MovimientoInventario.objects.count() == 0
        assert Transaction.objects.count() == 0

    def test_does_not_create_when_flag_is_off(self):
        _, branch, integration = make_syncable_center(
            'A', 'cnt_aaa', create_missing_products=False
        )

        client = FakeClient(stock=[stock_item()])
        result = StockSynchronizer(integration, client=client).run()

        assert result.created == 0
        assert result.unmatched == ['SER-VITC-30']
        assert not Producto.objects.filter(sucursal=branch).exists()

    def test_advances_the_cursor(self):
        _, _, integration = make_syncable_center('A', 'cnt_aaa')
        assert integration.last_stock_sync is None

        StockSynchronizer(integration, client=FakeClient(stock=[])).run()

        integration.refresh_from_db()
        assert integration.last_stock_sync is not None

    def test_item_without_sku_is_reported_not_created(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')

        client = FakeClient(stock=[stock_item(sku='', name='Sin código')])
        result = StockSynchronizer(integration, client=client).run()

        assert result.unmatched == ['Sin código']
        assert not Producto.objects.filter(sucursal=branch).exists()


# --------------------------------------------------------------------------- #
# Sales — the happy path
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestSalesImport:

    def test_paid_sale_creates_income_linked_to_the_voucher(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        producto = make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher()])
        result = SalesImporter(integration, client=client).run()

        assert result.processed == 1

        tx = Transaction.objects.get()
        assert tx.type == 'INCOME_PRODUCT'
        assert tx.amount == Decimal('18500.00')
        assert tx.product == producto
        assert tx.branch == branch
        assert tx.category.name == 'Productos'
        assert tx.auto_generated is True
        assert tx.registered_by is None  # no es la caja de ningún empleado
        assert str(tx.date) == '2026-08-04'

        sale = ContoSale.objects.get()
        assert sale.status == ContoSale.Status.PROCESSED
        assert list(sale.transactions.all()) == [tx]

    def test_quantity_multiplies_the_unit_price(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(
            items=[product_line(quantity=3, unit='1000.00')]
        )])
        SalesImporter(integration, client=client).run()

        assert Transaction.objects.get().amount == Decimal('3000.00')

    def test_shipping_becomes_a_separate_other_income(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(items=[
            product_line(unit='18500.00'),
            {'tipo': 'ENVIO', 'sku': None, 'nombre': 'Envío',
             'cantidad': 1, 'precio_unitario': '3000.00'},
        ])])
        SalesImporter(integration, client=client).run()

        products = Transaction.objects.filter(type='INCOME_PRODUCT')
        others = Transaction.objects.filter(type='INCOME_OTHER')
        assert products.get().amount == Decimal('18500.00')
        assert others.get().amount == Decimal('3000.00')

    def test_unknown_sku_still_records_the_income(self):
        """The money came in even if we cannot attribute it to a product."""
        _, branch, integration = make_syncable_center(
            'A', 'cnt_aaa', create_missing_products=False
        )

        client = FakeClient(sales=[voucher(items=[product_line(sku='NO-EXISTE')])])
        result = SalesImporter(integration, client=client).run()

        tx = Transaction.objects.get()
        assert result.processed == 1
        assert tx.amount == Decimal('18500.00')
        assert tx.product is None
        assert 'sin producto asociado' in tx.notes

    def test_running_twice_does_not_duplicate(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        SalesImporter(integration, client=FakeClient(sales=[voucher()])).run()
        SalesImporter(integration, client=FakeClient(sales=[voucher()])).run()

        assert Transaction.objects.count() == 1
        assert ContoSale.objects.count() == 1

    def test_second_run_uses_an_overlapping_window(self):
        _, _, integration = make_syncable_center('A', 'cnt_aaa')

        SalesImporter(integration, client=FakeClient(sales=[])).run()
        integration.refresh_from_db()
        first_cursor = integration.last_sales_sync

        client = FakeClient(sales=[])
        SalesImporter(integration, client=client).run()

        # The window starts before the previous cursor, to cover clock skew.
        assert client.sales_calls[0] < first_cursor


# --------------------------------------------------------------------------- #
# Sales — discounts
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestDiscounts:

    def test_discount_is_prorated_across_product_lines(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'A-1', name='Uno')
        make_product(branch, 'B-2', name='Dos')

        client = FakeClient(sales=[voucher(items=[
            product_line(sku='A-1', unit='10000.00'),
            product_line(sku='B-2', unit='5000.00'),
            {'tipo': 'DESCUENTO', 'nombre': 'Promo', 'cantidad': 1,
             'precio_unitario': '1500.00'},
        ])])
        SalesImporter(integration, client=client).run()

        amounts = sorted(t.amount for t in Transaction.objects.all())
        assert amounts == [Decimal('4500.00'), Decimal('9000.00')]

    def test_rounding_remainder_lands_on_the_last_line(self):
        """The prorated shares must add up to the discount exactly."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'A-1')
        make_product(branch, 'B-2')

        client = FakeClient(sales=[voucher(items=[
            product_line(sku='A-1', unit='10000.00'),
            product_line(sku='B-2', unit='5000.00'),
            {'tipo': 'DESCUENTO', 'nombre': 'Promo', 'cantidad': 1,
             'precio_unitario': '1000.00'},
        ])])
        SalesImporter(integration, client=client).run()

        total = sum(t.amount for t in Transaction.objects.all())
        assert total == Decimal('14000.00')

    def test_discount_without_product_lines_comes_off_shipping(self):
        _, _, integration = make_syncable_center('A', 'cnt_aaa')

        client = FakeClient(sales=[voucher(items=[
            {'tipo': 'ENVIO', 'nombre': 'Envío', 'cantidad': 1,
             'precio_unitario': '3000.00'},
            {'tipo': 'DESCUENTO', 'nombre': 'Envío gratis', 'cantidad': 1,
             'precio_unitario': '1000.00'},
        ])])
        SalesImporter(integration, client=client).run()

        assert Transaction.objects.get().amount == Decimal('2000.00')

    def test_discount_with_nothing_to_prorate_is_an_error_not_silence(self):
        _, _, integration = make_syncable_center('A', 'cnt_aaa')

        client = FakeClient(sales=[voucher(items=[
            {'tipo': 'DESCUENTO', 'nombre': 'Suelto', 'cantidad': 1,
             'precio_unitario': '500.00'},
        ])])
        result = SalesImporter(integration, client=client).run()

        assert len(result.errors) == 1
        assert Transaction.objects.count() == 0
        sale = ContoSale.objects.get()
        assert sale.status == ContoSale.Status.ERROR
        assert sale.payload  # el crudo queda guardado para reprocesar


# --------------------------------------------------------------------------- #
# Sales — states that are not "paid"
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestNonPaidStates:

    def test_channel_outside_the_list_is_skipped(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(channel='presencial')])
        result = SalesImporter(integration, client=client).run()

        assert result.skipped == 1
        assert Transaction.objects.count() == 0
        assert ContoSale.objects.get().status == ContoSale.Status.SKIPPED

    def test_unpaid_voucher_waits(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(status='PENDIENTE')])
        result = SalesImporter(integration, client=client).run()

        assert result.pending == 1
        assert Transaction.objects.count() == 0
        assert ContoSale.objects.get().status == ContoSale.Status.PENDING

    def test_voucher_paid_later_gets_imported(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        SalesImporter(
            integration, client=FakeClient(sales=[voucher(status='PENDIENTE')])
        ).run()
        assert Transaction.objects.count() == 0

        SalesImporter(
            integration, client=FakeClient(sales=[voucher(status='PAGADO')])
        ).run()

        assert Transaction.objects.count() == 1
        assert ContoSale.objects.get().status == ContoSale.Status.PROCESSED

    def test_cancellation_reverts_an_already_imported_sale(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        SalesImporter(integration, client=FakeClient(sales=[voucher()])).run()
        assert Transaction.objects.count() == 1

        result = SalesImporter(
            integration, client=FakeClient(sales=[voucher(status='CANCELADO')])
        ).run()

        assert result.reverted == 1
        assert Transaction.objects.count() == 0
        sale = ContoSale.objects.get()
        assert sale.status == ContoSale.Status.SKIPPED
        assert sale.payload  # el crudo se conserva

    def test_voucher_born_cancelled_creates_nothing(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(status='CANCELADO')])
        SalesImporter(integration, client=client).run()

        assert Transaction.objects.count() == 0
        assert ContoSale.objects.get().status == ContoSale.Status.SKIPPED


# --------------------------------------------------------------------------- #
# Sales — credit notes
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestCreditNotes:

    def test_credit_note_compensates_with_an_expense(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[
            voucher(voucher_id='8891'),
            voucher(voucher_id='9001', kind='NOTA_CREDITO', related='8891',
                    total='18500.00', items=[]),
        ])
        result = SalesImporter(integration, client=client).run()

        assert result.processed == 2
        income = Transaction.objects.get(type='INCOME_PRODUCT')
        expense = Transaction.objects.get(type='EXPENSE')
        assert income.amount == Decimal('18500.00')
        assert expense.amount == Decimal('18500.00')
        assert expense.category.name == 'Devoluciones'
        assert '8891' in expense.notes

    def test_partial_credit_note_compensates_only_its_amount(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[
            voucher(voucher_id='8891', items=[product_line(unit='18500.00')]),
            voucher(voucher_id='9001', kind='NOTA_CREDITO', related='8891',
                    total='5000.00', items=[]),
        ])
        SalesImporter(integration, client=client).run()

        assert Transaction.objects.get(type='INCOME_PRODUCT').amount == Decimal('18500.00')
        assert Transaction.objects.get(type='EXPENSE').amount == Decimal('5000.00')

    def test_credit_note_arriving_before_its_sale_waits(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        # Only the note, referencing a sale we have not seen yet.
        result = SalesImporter(integration, client=FakeClient(sales=[
            voucher(voucher_id='9001', kind='NOTA_CREDITO', related='8891',
                    total='18500.00', items=[]),
        ])).run()

        assert result.pending == 1
        assert Transaction.objects.count() == 0

        # The sale shows up, and the note is retried on the next window.
        SalesImporter(integration, client=FakeClient(sales=[
            voucher(voucher_id='8891'),
            voucher(voucher_id='9001', kind='NOTA_CREDITO', related='8891',
                    total='18500.00', items=[]),
        ])).run()

        assert Transaction.objects.filter(type='EXPENSE').count() == 1


# --------------------------------------------------------------------------- #
# Payment method mapping
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestPaymentMethod:

    # Values confirmed by Conto: transfer, card, cash, check, mercadopago,
    # mercadolibre. The default configured in these fixtures is MERCADOPAGO.
    @pytest.mark.parametrize('payment,gateway,expected', [
        ('cash', None, 'CASH'),
        ('check', None, 'OTHER'),
        ('mercadopago', None, 'MERCADOPAGO'),
        ('mercadolibre', None, 'MERCADOPAGO'),
        # Valores reales observados en la cuenta de AME: vienen con guion.
        ('mercadopago', 'mercado-pago', 'MERCADOPAGO'),
        ('card', 'mercado-pago', 'MERCADOPAGO'),
        ('card', 'MERCADO PAGO', 'MERCADOPAGO'),
        ('card', 'pago-nube', 'OTHER'),
        ('card', 'pagonube', 'OTHER'),
        (None, 'mercado-pago', 'MERCADOPAGO'),
        ('transfer', None, 'BANK_TRANSFER'),
        ('transfer', 'lo-que-sea', 'BANK_TRANSFER'),
        ('card', 'mercadopago', 'MERCADOPAGO'),
        ('card', 'Mercado Pago', 'MERCADOPAGO'),
        ('card', None, 'MERCADOPAGO'),          # cae al default configurado
        ('card', 'desconocido', 'MERCADOPAGO'),  # idem
        (None, None, 'MERCADOPAGO'),
    ])
    def test_mapping(self, payment, gateway, expected):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(payment=payment, gateway=gateway)])
        SalesImporter(integration, client=client).run()

        assert Transaction.objects.get().payment_method == expected

    def test_default_is_configurable(self):
        _, branch, integration = make_syncable_center(
            'A', 'cnt_aaa', default_payment_method='CREDIT_CARD'
        )
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(payment='card', gateway=None)])
        SalesImporter(integration, client=client).run()

        assert Transaction.objects.get().payment_method == 'CREDIT_CARD'

    def test_a_known_method_is_not_overridden_by_the_default(self):
        """
        Regression guard: `cash` used to fall through to the default, because the
        mapping only handled `transfer` and `card`. Conto reports six values.
        """
        _, branch, integration = make_syncable_center(
            'A', 'cnt_aaa', default_payment_method='MERCADOPAGO'
        )
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(payment='cash', gateway=None)])
        SalesImporter(integration, client=client).run()

        assert Transaction.objects.get().payment_method == 'CASH'

    def test_gateway_wins_over_a_generic_method(self):
        """`card` says a card was used but not which gateway processed it."""
        _, branch, integration = make_syncable_center(
            'A', 'cnt_aaa', default_payment_method='CREDIT_CARD'
        )
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(payment='card', gateway='mercadopago')])
        SalesImporter(integration, client=client).run()

        assert Transaction.objects.get().payment_method == 'MERCADOPAGO'


# --------------------------------------------------------------------------- #
# Clients
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestClientResolution:

    def test_existing_client_is_reused_within_the_center(self):
        center, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')
        existing = Cliente.objects.create(
            centro_estetica=center, nombre='Ana', apellido='Gómez',
            email='ana@ejemplo.com', telefono='1133334444',
        )

        client = FakeClient(sales=[voucher(client={
            'nombre': 'Ana Gómez', 'email': 'ana@ejemplo.com',
            'telefono': '+5491133334444',
        })])
        SalesImporter(integration, client=client).run()

        assert Cliente.objects.count() == 1
        assert Transaction.objects.get().client == existing

    def test_client_of_another_center_is_not_reused(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        center_b, _, _ = make_syncable_center('B', 'cnt_bbb')
        make_product(branch, 'SER-VITC-30')
        Cliente.objects.create(
            centro_estetica=center_b, nombre='Ana', apellido='Gómez',
            email='ana@ejemplo.com', telefono='1133334444',
        )

        client = FakeClient(sales=[voucher(client={
            'nombre': 'Ana Gómez', 'email': 'ana@ejemplo.com',
            'telefono': '1133334444',
        })])
        SalesImporter(integration, client=client).run()

        # A new client in center A, not the one belonging to center B.
        tx = Transaction.objects.get()
        assert tx.client is not None
        assert tx.client.centro_estetica == integration.center
        assert Cliente.objects.count() == 2

    def test_client_creation_can_be_disabled(self):
        _, branch, integration = make_syncable_center(
            'A', 'cnt_aaa', create_missing_clients=False
        )
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(client={
            'nombre': 'Ana Gómez', 'email': 'ana@ejemplo.com', 'telefono': '11',
        })])
        SalesImporter(integration, client=client).run()

        assert Cliente.objects.count() == 0
        assert Transaction.objects.get().client is None

    def test_sale_without_client_is_valid(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        SalesImporter(integration, client=FakeClient(sales=[voucher()])).run()

        assert Transaction.objects.get().client is None


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestGuards:

    def test_first_run_requires_import_from(self):
        """
        Without it, the first run would try to pull the whole account history.
        """
        _, _, integration = make_syncable_center('A', 'cnt_aaa')
        integration.import_from = None
        integration.save(update_fields=['import_from'])

        with pytest.raises(ContoError, match='importar desde'):
            SalesImporter(integration, client=FakeClient(sales=[])).run()

    def test_a_voucher_that_adds_up_is_not_flagged(self):
        """
        Conto's `total` is what the customer paid, and the lines summed with the
        sign of their type must equal it exactly.
        """
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(
            total='21500.00',
            items=[
                product_line(unit='18500.00'),
                {'tipo': 'ENVIO', 'nombre': 'Envío', 'cantidad': 1,
                 'precio_unitario': '3000.00'},
            ],
        )])
        SalesImporter(integration, client=client).run()

        assert ContoSale.objects.get().total_discrepancy is None

    def test_free_shipping_reconciles(self):
        """
        The case that exposed Conto's bug: a shipping line given free has an
        effective price of 0, so it must not inflate the income.
        """
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(
            total='18500.00',
            items=[
                product_line(unit='18500.00'),
                {'tipo': 'ENVIO', 'nombre': 'Envío gratis', 'cantidad': 1,
                 'precio_unitario': '0.00', 'precio_lista': '6231.00'},
            ],
        )])
        SalesImporter(integration, client=client).run()

        sale = ContoSale.objects.get()
        assert sale.total_discrepancy is None
        # La línea en cero no genera una transacción de ingreso vacía.
        assert Transaction.objects.count() == 1
        assert Transaction.objects.get().amount == Decimal('18500.00')

    def test_a_voucher_that_does_not_add_up_is_flagged_but_imported(self):
        """
        The money did come in, so dropping the sale would be worse than importing
        it flagged. But the breakdown cannot be trusted silently.
        """
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(
            total='12269.00',           # menor que la suma de las líneas
            items=[product_line(unit='18500.00')],
        )])
        result = SalesImporter(integration, client=client).run()

        sale = ContoSale.objects.get()
        assert result.processed == 1
        assert sale.status == ContoSale.Status.PROCESSED
        assert sale.total_discrepancy == Decimal('6231.00')
        assert Transaction.objects.count() == 1

    def test_a_voucher_without_a_total_is_not_flagged(self):
        """Nothing to reconcile against; the lines are all there is."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(total='0', items=[product_line()])])
        SalesImporter(integration, client=client).run()

        assert ContoSale.objects.get().total_discrepancy is None

    def test_a_sale_older_than_import_from_is_skipped(self):
        """
        Conto filters `desde` by `actualizado_en`, so an old voucher touched
        recently arrives with its original date. Importing it would duplicate a
        period the center already loaded by hand.
        """
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        integration.import_from = timezone.make_aware(
            timezone.datetime(2026, 7, 1)
        )
        integration.save()
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[
            voucher(voucher_id='vieja', date='2026-05-14'),
            voucher(voucher_id='nueva', date='2026-07-15'),
        ])
        result = SalesImporter(integration, client=client).run()

        assert result.processed == 1
        assert result.skipped == 1
        assert Transaction.objects.count() == 1
        assert ContoSale.objects.get(voucher_id='vieja').status == \
            ContoSale.Status.SKIPPED
        assert ContoSale.objects.get(voucher_id='nueva').status == \
            ContoSale.Status.PROCESSED

    def test_a_sale_on_the_import_from_date_is_included(self):
        """The boundary is inclusive: `import_from` is the first day imported."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        integration.import_from = timezone.make_aware(
            timezone.datetime(2026, 7, 1)
        )
        integration.save()
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(date='2026-07-01')])
        result = SalesImporter(integration, client=client).run()

        assert result.processed == 1

    def test_widening_import_from_lets_a_skipped_sale_through(self):
        """A voucher skipped for being too old must not stay skipped forever."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        integration.import_from = timezone.make_aware(
            timezone.datetime(2026, 7, 1)
        )
        integration.save()
        make_product(branch, 'SER-VITC-30')

        payload = voucher(date='2026-05-14')
        SalesImporter(integration, client=FakeClient(sales=[payload])).run()
        assert Transaction.objects.count() == 0

        # Se amplía el histórico y se limpia el cursor, como indica la guía.
        integration.import_from = timezone.make_aware(
            timezone.datetime(2026, 1, 1)
        )
        integration.last_sales_sync = None
        integration.save()

        SalesImporter(integration, client=FakeClient(sales=[payload])).run()

        assert Transaction.objects.count() == 1
        assert ContoSale.objects.get().status == ContoSale.Status.PROCESSED

    def test_voucher_without_id_is_an_error(self):
        _, _, integration = make_syncable_center('A', 'cnt_aaa')

        payload = voucher()
        payload['id'] = None
        result = SalesImporter(integration, client=FakeClient(sales=[payload])).run()

        assert len(result.errors) == 1
        assert Transaction.objects.count() == 0

    def test_invalid_date_is_recorded_as_an_error(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[voucher(date='04/08/2026')])
        result = SalesImporter(integration, client=client).run()

        assert len(result.errors) == 1
        assert Transaction.objects.count() == 0
        assert ContoSale.objects.get().status == ContoSale.Status.ERROR

"""
Tests for `reimportar_conto`.

The destructive path is the one that matters and the one that is easy to leave
untested — the informational run passing says nothing about it. It deletes
financial records, so what it must NOT touch is as important as what it deletes.
"""
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoSale
from apps.integraciones.sync import get_income_category

from .test_services import make_product
from .test_sync import FakeClient, make_syncable_center, product_line, voucher


def import_some_sales(integration, branch, count=2):
    """
    Import `count` vouchers. Safe to call twice on the same branch, which is what
    the delete-and-reimport test needs.
    """
    from apps.integraciones.sync import SalesImporter
    from apps.inventario.models import Producto

    if not Producto.objects.filter(sucursal=branch, sku='SER-VITC-30').exists():
        make_product(branch, 'SER-VITC-30')

    sales = [
        voucher(
            voucher_id=f'v{n}',
            total='1000.00',                     # cuadra con la línea
            items=[product_line(unit='1000.00')],
        )
        for n in range(count)
    ]
    SalesImporter(integration, client=FakeClient(sales=sales)).run()


def manual_transaction(branch, amount='500.00'):
    """A transaction loaded by hand, which the command must never touch."""
    return Transaction.objects.create(
        branch=branch,
        category=get_income_category(branch, 'Productos'),
        type='INCOME_PRODUCT',
        amount=Decimal(amount),
        payment_method='CASH',
        date=timezone.localdate(),
        description='Venta cargada a mano',
    )


def run(**options):
    out = StringIO()
    call_command('reimportar_conto', stdout=out, **options)
    return out.getvalue()


@pytest.mark.django_db
class TestReimportar:

    def test_the_informational_run_deletes_nothing(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        import_some_sales(integration, branch)
        antes = Transaction.objects.count()

        output = run()

        assert Transaction.objects.count() == antes
        assert ContoSale.objects.count() == 2
        assert 'no se borró nada' in output

    def test_confirming_deletes_the_imported_data(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        import_some_sales(integration, branch)
        assert Transaction.objects.count() == 2

        run(confirmar=True)

        assert Transaction.objects.count() == 0
        assert ContoSale.objects.count() == 0
        integration.refresh_from_db()
        assert integration.last_sales_sync is None

    def test_it_never_touches_transactions_loaded_by_hand(self):
        """The whole point: only what came from Conto is in scope."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        manual = manual_transaction(branch)
        import_some_sales(integration, branch)

        run(confirmar=True)

        assert Transaction.objects.count() == 1
        assert Transaction.objects.get().pk == manual.pk

    def test_it_never_touches_another_centers_import(self):
        _, branch_a, integration_a = make_syncable_center('A', 'cnt_aaa')
        _, branch_b, integration_b = make_syncable_center('B', 'cnt_bbb')
        import_some_sales(integration_a, branch_a)
        import_some_sales(integration_b, branch_b)

        run(confirmar=True, integration_id=integration_a.pk)

        assert ContoSale.objects.filter(integration=integration_a).count() == 0
        assert ContoSale.objects.filter(integration=integration_b).count() == 2
        assert Transaction.objects.filter(branch=branch_b).count() == 2

    def test_the_sales_can_be_imported_again_afterwards(self):
        """Deleting and re-importing has to produce the same result."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        import_some_sales(integration, branch)
        total_antes = sum(t.amount for t in Transaction.objects.all())

        run(confirmar=True)
        import_some_sales(integration, branch)

        assert Transaction.objects.count() == 2
        assert sum(t.amount for t in Transaction.objects.all()) == total_antes

    def test_running_on_an_empty_integration_is_harmless(self):
        make_syncable_center('A', 'cnt_aaa')
        output = run(confirmar=True)
        assert 'Nada que borrar' in output

    def test_it_refuses_when_there_is_more_than_one_integration(self):
        make_syncable_center('A', 'cnt_aaa')
        make_syncable_center('B', 'cnt_bbb')

        with pytest.raises(CommandError, match='más de una integración'):
            run(confirmar=True)

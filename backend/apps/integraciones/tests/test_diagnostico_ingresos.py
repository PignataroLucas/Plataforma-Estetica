"""
Tests for `diagnostico_ingresos`.

It is a read-only report, but a decision gets made from its output: how far back
`import_from` can go without double-counting income the center already loaded by
hand. A wrong number here is money counted twice in the real books, so what is
worth testing is that the origin split and the conclusion are right.
"""
from datetime import date
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from apps.empleados.models import Usuario
from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoSale
from apps.integraciones.sync import get_income_category

from .test_sync import make_syncable_center


def income(branch, when, amount='1000.00', by=None, type='INCOME_PRODUCT'):
    return Transaction.objects.create(
        branch=branch,
        category=get_income_category(branch, 'Productos'),
        type=type,
        amount=Decimal(amount),
        payment_method='CASH',
        date=when,
        description='Venta',
        registered_by=by,
    )


def imported_income(integration, branch, when, amount='1000.00'):
    """An income the way the importer leaves it: no user, linked to a voucher."""
    transaction = income(branch, when, amount)
    sale = ContoSale.objects.create(
        integration=integration,
        voucher_id=f'v-{when}-{amount}',
        status='PROCESSED',
        payload={},
    )
    sale.transactions.add(transaction)
    return transaction


def employee(center):
    return Usuario.objects.create_user(
        username=f'emp-{center.pk}', password='x', rol='EMPLEADO',
        centro_estetica=center, sucursal=center.sucursales.first(),
    )


def run(**options):
    out = StringIO()
    call_command('diagnostico_ingresos', stdout=out, **options)
    return out.getvalue()


@pytest.mark.django_db
class TestDiagnosticoIngresos:

    def test_reports_nothing_when_there_is_no_product_income(self):
        make_syncable_center('A', 'cnt_aaa')
        assert 'Sin ingresos por producto registrados' in run()

    def test_the_hole_starts_at_the_first_month_without_manual_loading(self):
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        user = employee(center)
        income(branch, date(2026, 5, 10), by=user)
        income(branch, date(2026, 6, 10), by=user)
        income(branch, date(2026, 7, 10))          # ya sin carga manual
        income(branch, date(2026, 8, 3))

        output = run()

        assert 'Sin carga manual desde 2026-07' in output
        assert '2026-07-01' in output

    def test_it_warns_when_the_latest_month_was_loaded_by_hand(self):
        """Importing over it would double the income, so it must not read green."""
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        income(branch, date(2026, 8, 3), by=employee(center))

        output = run()

        assert 'duplicaría ingresos' in output
        assert 'Sin carga manual desde' not in output

    def test_the_conto_column_does_not_inflate_the_month_total(self):
        """The link to vouchers is a many-to-many; joining it would double `total`."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        imported_income(integration, branch, date(2026, 8, 3), '1500.00')
        imported_income(integration, branch, date(2026, 8, 4), '2500.00')

        output = run()

        assert '4,000.00' in output
        linea = next(l for l in output.splitlines() if '2026-08' in l)
        assert linea.split()[-1] == '2'      # de_conto
        assert linea.split()[-2] == '0'      # a_mano

    def test_service_income_is_out_of_scope(self):
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        income(branch, date(2026, 8, 3), '9000.00',
               by=employee(center), type='INCOME_SERVICE')

        assert 'Sin ingresos por producto registrados' in run()

    def test_each_branch_is_counted_on_its_own(self):
        _, branch_a, _ = make_syncable_center('A', 'cnt_aaa')
        center_b, branch_b, _ = make_syncable_center('B', 'cnt_bbb')
        income(branch_a, date(2026, 8, 3), '1000.00')
        income(branch_b, date(2026, 8, 3), '7000.00', by=employee(center_b))

        output = run(sucursal=branch_a.pk)

        assert '1,000.00' in output
        assert '7,000.00' not in output

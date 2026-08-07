"""
Tests for `diagnostico_ingresos`.

It is a read-only report, but a decision gets made from its output: how far back
`import_from` can go without double-counting income the center already loaded by
hand. A wrong number here is money counted twice in the real books.

Two things are worth guarding. That months with no income at all still show up —
they are the hole, and a table that omits them hides exactly what is being looked
for. And that the origin split is right, because a sale that moved stock was made
in person and cannot collide with a Tienda Nube import, while one typed into
Finanzas can.

Everything is dated relative to today on purpose: the report reasons over the
calendar, so fixed dates would make these pass or fail depending on the month.
"""
from datetime import date
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.empleados.models import Usuario
from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoSale
from apps.integraciones.sync import get_income_category

from .test_services import make_product
from .test_sync import make_syncable_center


def month_start(offset):
    """First day of the month `offset` months before the current one."""
    today = timezone.localdate()
    year, month = today.year, today.month
    for _ in range(offset):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return date(year, month, 1)


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


def counter_sale(branch, amount='1000.00'):
    """
    A sale made in person: it moves stock, and the inventory signal bills it.
    Stock is seeded with `.update()` so creating the product does not fire the
    initial-stock movement.
    """
    from apps.inventario.models import MovimientoInventario, Producto

    producto = make_product(branch, 'MOSTRADOR-1')
    Producto.objects.filter(pk=producto.pk).update(stock_actual=10)
    MovimientoInventario.objects.create(
        producto=producto,
        tipo='SALIDA',
        cantidad=1,
        stock_anterior=10,
        stock_nuevo=9,
        precio_unitario=Decimal(amount),
    )


def employee(center):
    """The username is suffixed because a test may need more than one."""
    return Usuario.objects.create_user(
        username=f'emp-{center.pk}-{Usuario.objects.count()}', password='x',
        rol='EMPLEADO', centro_estetica=center,
        sucursal=center.sucursales.first(),
    )


def run(**options):
    out = StringIO()
    call_command('diagnostico_ingresos', stdout=out, **options)
    return out.getvalue()


def line_for(output, mes):
    return next(l for l in output.splitlines() if mes.strftime('%Y-%m') in l)


@pytest.mark.django_db
class TestDiagnosticoIngresos:

    def test_reports_nothing_when_there_is_no_product_income(self):
        make_syncable_center('A', 'cnt_aaa')
        assert 'Sin ingresos por producto' in run()

    def test_months_with_no_income_at_all_are_still_listed(self):
        """The production case: the hole was invisible because it had no rows."""
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        income(branch, month_start(2), by=employee(center))

        output = run(meses=4)

        for offset in range(4):
            assert line_for(output, month_start(offset))
        assert line_for(output, month_start(0)).split()[1] == '0'

    def test_the_hole_starts_after_the_last_month_loaded_by_hand(self):
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        user = employee(center)
        income(branch, month_start(3), by=user)
        income(branch, month_start(2), by=user)
        # Los dos meses siguientes no tienen ninguna transacción.

        output = run(meses=6)

        esperado = month_start(1)
        assert f'Sin carga manual desde {esperado.strftime("%Y-%m")}' in output
        assert esperado.strftime('%Y-%m-01') in output

    def test_it_warns_when_the_current_month_was_loaded_by_hand(self):
        """Importing over it would double the income, so it must not read green."""
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        income(branch, month_start(0), by=employee(center))

        output = run()

        assert 'duplicaría ingresos' in output
        assert 'Sin carga manual desde' not in output

    def test_a_sale_that_moved_stock_counts_as_counter_not_by_hand(self):
        """
        It is the distinction the whole decision rests on: a counter sale is
        `presencial` in Conto, never imported, so it cannot be duplicated.
        """
        _, branch, _ = make_syncable_center('A', 'cnt_aaa')
        counter_sale(branch)

        output = run()

        linea = line_for(output, month_start(0)).split()
        assert linea[3] == '0'      # a mano
        assert linea[4] == '1'      # mostrador
        assert 'Sin carga manual desde' in output

    def test_the_conto_column_does_not_inflate_the_month_total(self):
        """The link to vouchers is a many-to-many; joining it would double `total`."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        imported_income(integration, branch, month_start(0), '1500.00')
        imported_income(integration, branch, month_start(0), '2500.00')

        output = run()

        linea = line_for(output, month_start(0)).split()
        assert linea[2] == '4,000.00'
        assert linea[5] == '2'      # de Conto

    def test_it_says_when_the_cut_month_could_still_be_reviewed(self):
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        income(branch, month_start(2), by=employee(center))

        output = run(meses=6)

        assert 'si son ventas de mostrador' in output

    def test_service_income_is_out_of_scope(self):
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        income(branch, month_start(0), '9000.00',
               by=employee(center), type='INCOME_SERVICE')

        assert 'Sin ingresos por producto' in run()

    def test_income_older_than_the_window_is_reported_not_dropped(self):
        center, branch, _ = make_syncable_center('A', 'cnt_aaa')
        income(branch, month_start(0), by=employee(center))
        income(branch, month_start(8), '5000.00', by=employee(center))

        output = run(meses=3)

        assert 'Hay 1 ventas anteriores a' in output

    def test_each_branch_is_counted_on_its_own(self):
        _, branch_a, _ = make_syncable_center('A', 'cnt_aaa')
        center_b, branch_b, _ = make_syncable_center('B', 'cnt_bbb')
        income(branch_a, month_start(0), '1000.00')
        income(branch_b, month_start(0), '7000.00', by=employee(center_b))

        output = run(sucursal=branch_a.pk)

        assert '1,000.00' in output
        assert '7,000.00' not in output

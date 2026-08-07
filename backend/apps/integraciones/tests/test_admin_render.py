"""
The admin list pages have to render *with data in them*.

`format_html` escapes every argument to a SafeString before applying the format
string, so a numeric spec like `{:,.2f}` written inside the template raises
ValueError. But it only raises when there is a row to format: an empty changelist
renders fine. That is why the bug survived unnoticed — the pages look healthy
until the day they hold data, and then every one of them answers 500.

These two are the pages used to verify an import: the vouchers and the money they
produced.
"""
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.integraciones.models import ContoSale
from apps.integraciones.sync import SalesImporter

from .test_services import make_product
from .test_sync import FakeClient, make_syncable_center, product_line, voucher


@pytest.fixture(autouse=True)
def plain_static(settings):
    """
    The project serves static files through WhiteNoise's manifest storage, which
    demands a `collectstatic` that no test run does. Without this the admin
    template dies on its own stylesheet before reaching the rows, which is not
    what these tests are about.
    """
    settings.STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }


def import_one_sale(integration, branch, total='1000.00'):
    make_product(branch, 'SER-VITC-30')
    SalesImporter(integration, client=FakeClient(sales=[
        voucher(total=total, items=[product_line(unit=total)])
    ])).run()


@pytest.mark.django_db
class TestAdminChangelistsRender:

    def test_the_voucher_list_renders_with_vouchers_in_it(self, admin_client):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        import_one_sale(integration, branch)

        response = admin_client.get(reverse('admin:integraciones_contosale_changelist'))

        assert response.status_code == 200
        assert ContoSale.objects.count() == 1

    def test_a_voucher_that_does_not_add_up_renders_its_discrepancy(self, admin_client):
        """The red column is the one nobody looks at until it matters."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        import_one_sale(integration, branch)
        ContoSale.objects.update(total_discrepancy=Decimal('-12.34'))

        response = admin_client.get(reverse('admin:integraciones_contosale_changelist'))

        assert response.status_code == 200
        assert '-12.34' in response.content.decode()

    def test_the_transaction_list_renders_the_imported_income(self, admin_client):
        """Where the imported money is checked, so it has to open."""
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        import_one_sale(integration, branch)

        response = admin_client.get(reverse('admin:finanzas_transaction_changelist'))

        assert response.status_code == 200
        assert '1,000.00' in response.content.decode()

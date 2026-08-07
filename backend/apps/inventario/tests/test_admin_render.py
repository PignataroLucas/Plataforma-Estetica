"""
The inventory admin list pages have to render *with data in them*.

`format_html` escapes every argument to a SafeString before applying the format
string, so a numeric spec like `{:,.2f}` written inside the template raises
ValueError — but only once there is a row to format. An empty changelist renders
fine, which is how the product list reached production answering 500 to anyone
who opened it.
"""
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.inventario.models import MovimientoInventario, Producto

from .test_sku_constraint import make_branch, make_product


@pytest.fixture(autouse=True)
def plain_static(settings):
    """WhiteNoise's manifest storage needs a `collectstatic` no test run does."""
    settings.STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }


@pytest.mark.django_db
class TestInventoryAdminRenders:

    def test_the_product_list_renders_with_products_in_it(self, admin_client):
        branch = make_branch('Ame', 'Banfield')
        make_product(branch, 'PROD-1', name='Crema Gel AH')

        response = admin_client.get(reverse('admin:inventario_producto_changelist'))

        assert response.status_code == 200
        assert 'Crema Gel AH' in response.content.decode()

    def test_a_product_on_offer_renders_both_prices(self, admin_client):
        """The offer branch formats two numbers instead of one."""
        branch = make_branch('Ame', 'Banfield')
        producto = make_product(branch, 'PROD-1')
        producto.en_oferta = True
        producto.precio_oferta = Decimal('150.00')
        producto.save()

        response = admin_client.get(reverse('admin:inventario_producto_changelist'))

        assert response.status_code == 200
        assert '150.00' in response.content.decode()

    def test_the_movement_list_renders_a_sale(self, admin_client):
        branch = make_branch('Ame', 'Banfield')
        producto = make_product(branch, 'PROD-1')
        Producto.objects.filter(pk=producto.pk).update(stock_actual=10)
        MovimientoInventario.objects.create(
            producto=producto, tipo='SALIDA', cantidad=2,
            stock_anterior=10, stock_nuevo=8,
            precio_unitario=Decimal('200.00'),
        )

        response = admin_client.get(
            reverse('admin:inventario_movimientoinventario_changelist')
        )

        assert response.status_code == 200
        assert '200.00' in response.content.decode()

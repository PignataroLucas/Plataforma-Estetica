"""
Tests de la atribución de ventas a la app (COMPRA_EN_APP_SPEC.md §5.6).

Una venta hecha desde la app llega por Conto **igual que una del navegador**:
`origen_venta` dice `store` en los dos casos (§6.3). El único rastro es el
código del cupón, y como los únicos que emitimos esos códigos somos nosotros,
una venta que trae uno es por definición una venta de la app.

De acá sale la métrica que justifica el proyecto entero, así que lo que se cuida
es que no se atribuya de más ni de menos:

- de menos, y en tres meses no se puede decir si la app vendió algo;
- de más, y el número dice que sí cuando no.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.integraciones.models import ContoSale, CuponApp, TiendanubeIntegration
from apps.integraciones.sync import SalesImporter

from .test_sync import (
    FakeClient,
    make_product,
    make_syncable_center,
    product_line,
    voucher,
)


def hacer_cupon(centro, codigo='APP-K3F9XQ7M', cliente=None, **extra):
    integracion, _ = TiendanubeIntegration.objects.get_or_create(
        center=centro,
        defaults={'store_id': f'store-{centro.pk}', 'token': 'tok'},
    )
    datos = {
        'integration': integracion,
        'cliente': cliente,
        'code': codigo,
        'percentage': Decimal('15.00'),
        'tiendanube_coupon_id': '999',
        'expires_at': timezone.now() + timedelta(hours=1),
    }
    datos.update(extra)
    return CuponApp.objects.create(**datos)


def venta_con_cupon(codigo, **extra):
    datos = {'cupon': codigo, 'descuento_cupon': '1875.00'}
    datos.update(extra)
    payload = voucher()
    payload.update(datos)
    return payload


@pytest.mark.django_db
class TestAtribucion:

    def test_una_venta_con_nuestro_codigo_queda_atribuida(self):
        centro, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')
        clienta = Cliente.objects.create(
            centro_estetica=centro, nombre='Ana', apellido='Gómez', telefono='11',
        )
        cupon = hacer_cupon(centro, cliente=clienta)

        client = FakeClient(sales=[venta_con_cupon(cupon.code)])
        SalesImporter(integration, client=client).run()

        sale = ContoSale.objects.get()
        cupon.refresh_from_db()
        assert sale.cupon_app == cupon
        assert sale.es_venta_de_la_app
        # El cupón queda marcado como usado: es lo que lo saca de la limpieza.
        assert cupon.used_at is not None

    def test_una_venta_sin_cupon_no_es_de_la_app(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        SalesImporter(integration, client=FakeClient(sales=[voucher()])).run()

        assert not ContoSale.objects.get().es_venta_de_la_app

    def test_un_cupon_ajeno_no_atribuye(self):
        """
        El centro puede emitir sus propias promociones desde el panel de Tienda
        Nube. Solo cuentan como venta de la app los códigos que emitimos.
        """
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        client = FakeClient(sales=[venta_con_cupon('BIENVENIDA10')])
        SalesImporter(integration, client=client).run()

        assert not ContoSale.objects.get().es_venta_de_la_app

    def test_el_cupon_de_otro_centro_no_atribuye(self):
        """
        Aislamiento entre inquilinos: los códigos son únicos, pero la venta de
        un centro no puede quedar atribuida a la clienta de otro.
        """
        centro_a, branch_a, integration_a = make_syncable_center('A', 'cnt_aaa')
        centro_b, _, _ = make_syncable_center('B', 'cnt_bbb')
        make_product(branch_a, 'SER-VITC-30')
        cupon_b = hacer_cupon(centro_b, codigo='APP-DEOTROXX')

        client = FakeClient(sales=[venta_con_cupon(cupon_b.code)])
        SalesImporter(integration_a, client=client).run()

        assert not ContoSale.objects.get().es_venta_de_la_app

    def test_con_varios_cupones_encuentra_el_nuestro(self):
        """Conto manda los códigos separados por coma cuando hay más de uno."""
        centro, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')
        cupon = hacer_cupon(centro)

        client = FakeClient(sales=[venta_con_cupon(f'ENVIOGRATIS,{cupon.code}')])
        SalesImporter(integration, client=client).run()

        assert ContoSale.objects.get().cupon_app == cupon

    def test_la_clienta_del_cupon_se_usa_si_el_comprador_no_matcheo(self):
        """
        La venta puede venir sin datos de comprador o con un email que no está
        en la base. El cupón dice a quién se lo dimos, y eso es mejor que nada.
        """
        centro, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')
        clienta = Cliente.objects.create(
            centro_estetica=centro, nombre='Ana', apellido='Gómez', telefono='11',
        )
        cupon = hacer_cupon(centro, cliente=clienta)

        payload = venta_con_cupon(cupon.code)
        payload['cliente'] = None
        SalesImporter(integration, client=FakeClient(sales=[payload])).run()

        sale = ContoSale.objects.get()
        assert sale.transactions.first().client == clienta

    def test_reprocesar_no_vuelve_a_marcar_el_cupon(self):
        """
        Reprocesar un voucher es normal —se hace después de arreglar un mapeo—
        y no puede mover la fecha de uso: es de lo que sale cuánto tardó una
        clienta entre que tocó "Comprar" y que pagó.
        """
        centro, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')
        cupon = hacer_cupon(centro)

        payload = venta_con_cupon(cupon.code)
        SalesImporter(integration, client=FakeClient(sales=[payload])).run()
        cupon.refresh_from_db()
        usado_original = cupon.used_at

        SalesImporter(integration, client=FakeClient(sales=[payload])).run()

        cupon.refresh_from_db()
        assert cupon.used_at == usado_original

    def test_una_venta_de_un_canal_que_no_importamos_igual_se_atribuye(self):
        """
        El cupón se usó igual. Marcarlo saca al código de la limpieza, que si no
        lo borraría de Tienda Nube creyendo que venció sin usarse.
        """
        centro, branch, integration = make_syncable_center('A', 'cnt_aaa')
        cupon = hacer_cupon(centro)

        payload = venta_con_cupon(cupon.code, canal='presencial')
        SalesImporter(integration, client=FakeClient(sales=[payload])).run()

        sale = ContoSale.objects.get()
        cupon.refresh_from_db()
        assert sale.status == ContoSale.Status.SKIPPED
        assert sale.cupon_app == cupon
        assert cupon.used_at is not None

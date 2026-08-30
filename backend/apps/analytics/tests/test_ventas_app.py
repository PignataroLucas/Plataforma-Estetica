"""
Tests de la medición de ventas de la app (COMPRA_EN_APP_SPEC.md §5.7).

Esta es la métrica que decide si el proyecto valió la pena, así que lo que se
cuida es que **no cuente de más ni de menos**:

- de menos, y en tres meses no se puede decir si la app vendió algo;
- de más, y el número dice que sí cuando no.

Los dos modos de contar de más que tiene esta forma de calcular:

1. **El many-to-many entre venta y transacción.** Una transacción ligada a dos
   comprobantes aparece dos veces en el join si falta el `distinct`, y el
   facturado por producto sale inflado.
2. **Mezclar centros.** El endpoint saca el centro del usuario, nunca del
   pedido: sumar las ventas de otro inquilino no es un error de redondeo.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.clientes.models import Cliente
from apps.empleados.models import Usuario
from apps.finanzas.models import Transaction, TransactionCategory
from apps.integraciones.models import ContoSale, CuponApp, TiendanubeIntegration

from apps.integraciones.tests.test_services import make_center, make_product

URL = reverse('dashboard-ventas-app')


def escenario(nombre='Ame', cuenta='acc-app'):
    centro, sucursal, conto = make_center(nombre, cuenta)
    tienda = TiendanubeIntegration.objects.create(
        center=centro, store_id=f'store-{cuenta}', token='tok',
    )
    return centro, sucursal, conto, tienda


def hacer_cupon(tienda, cliente=None, codigo='APP-AAA11111', usado=True):
    return CuponApp.objects.create(
        integration=tienda,
        cliente=cliente,
        code=codigo,
        percentage=Decimal('15.00'),
        tiendanube_coupon_id='1',
        expires_at=timezone.now() + timedelta(hours=1),
        used_at=timezone.now() if usado else None,
    )


def hacer_venta(conto, total, cupon=None, voucher='v1', dias_atras=1):
    """Un comprobante ya importado, con o sin cupón de la app."""
    return ContoSale.objects.create(
        integration=conto,
        voucher_id=voucher,
        type=ContoSale.VoucherType.SALE,
        status=ContoSale.Status.PROCESSED,
        channel='tiendanube',
        date=timezone.localdate() - timedelta(days=dias_atras),
        total=Decimal(total),
        cupon_app=cupon,
        coupon_code=cupon.code if cupon else '',
        coupon_discount=Decimal('1875.00') if cupon else None,
        payload={},
    )


def hacer_transaccion(sucursal, producto, monto, venta, dias_atras=1):
    categoria, _ = TransactionCategory.objects.get_or_create(
        branch=sucursal, name='Productos', type='INCOME',
        defaults={'is_system_category': True},
    )
    t = Transaction.objects.create(
        branch=sucursal,
        category=categoria,
        product=producto,
        type='INCOME_PRODUCT',
        amount=Decimal(monto),
        payment_method='CASH',
        date=timezone.localdate() - timedelta(days=dias_atras),
        description=producto.nombre,
        auto_generated=True,
    )
    venta.transactions.add(t)
    return t


def api(centro, rol='ADMIN'):
    usuario = Usuario.objects.create_user(
        username=f'u-{centro.pk}-{rol}', password='x',
        rol=rol, centro_estetica=centro, sucursal=centro.sucursales.first(),
    )
    cliente = APIClient()
    cliente.force_authenticate(user=usuario)
    return cliente


@pytest.mark.django_db
class TestResumen:

    def test_separa_lo_que_vendio_la_app_de_lo_demas(self):
        """
        Es la pregunta que justifica el proyecto entero: si esto no separa, en
        tres meses no se puede decir si la app sirvió.
        """
        centro, _, conto, tienda = escenario()
        hacer_venta(conto, '10625.00', cupon=hacer_cupon(tienda), voucher='app-1')
        hacer_venta(conto, '20000.00', voucher='web-1')
        hacer_venta(conto, '30000.00', voucher='web-2')

        datos = api(centro).get(URL).json()['resumen']

        assert datos['app']['ventas'] == 1
        assert datos['app']['facturado'] == 10625.0
        assert datos['resto']['ventas'] == 2
        assert datos['resto']['facturado'] == 50000.0
        # 10625 sobre 60625
        assert datos['participacion_app'] == 17.53

    def test_el_ticket_promedio_se_compara_de_los_dos_lados(self):
        """
        La pregunta que propuso Conto y que el §5.7 adopta, porque distingue las
        compras que el descuento trajo de las que iban a pasar igual y solo le
        costaron margen al centro.
        """
        centro, _, conto, tienda = escenario()
        hacer_venta(conto, '10000.00', cupon=hacer_cupon(tienda, codigo='APP-A'), voucher='a1')
        hacer_venta(conto, '20000.00', cupon=hacer_cupon(tienda, codigo='APP-B'), voucher='a2')
        hacer_venta(conto, '60000.00', voucher='w1')

        datos = api(centro).get(URL).json()['resumen']

        assert datos['app']['ticket_promedio'] == 15000.0
        assert datos['resto']['ticket_promedio'] == 60000.0

    def test_suma_el_descuento_que_costo(self):
        centro, _, conto, tienda = escenario()
        hacer_venta(conto, '10625.00', cupon=hacer_cupon(tienda), voucher='a1')

        datos = api(centro).get(URL).json()['resumen']

        assert datos['app']['descuento_otorgado'] == 1875.0

    def test_las_ventas_que_no_se_importaron_no_cuentan(self):
        """
        Una venta omitida o con error no es plata que entró. Contarlas infla el
        número que se va a usar para decidir si el proyecto sigue.
        """
        centro, _, conto, tienda = escenario()
        rota = hacer_venta(conto, '99999.00', cupon=hacer_cupon(tienda), voucher='a1')
        rota.status = ContoSale.Status.ERROR
        rota.save(update_fields=['status'])

        datos = api(centro).get(URL).json()['resumen']

        assert datos['app']['ventas'] == 0
        assert datos['app']['facturado'] == 0.0

    def test_fuera_del_periodo_no_cuenta(self):
        centro, _, conto, tienda = escenario()
        hacer_venta(conto, '10000.00', cupon=hacer_cupon(tienda),
                    voucher='a1', dias_atras=200)

        datos = api(centro).get(URL).json()['resumen']

        assert datos['app']['ventas'] == 0


@pytest.mark.django_db
class TestProductosYClientas:

    def test_lista_los_productos_que_vende_la_app(self):
        centro, sucursal, conto, tienda = escenario()
        producto = make_product(sucursal, sku='BS-1', name='Body Splash Amour')
        venta = hacer_venta(conto, '10625.00', cupon=hacer_cupon(tienda), voucher='a1')
        hacer_transaccion(sucursal, producto, '10625.00', venta)

        datos = api(centro).get(URL).json()['productos']

        assert len(datos) == 1
        assert datos[0]['producto'] == 'Body Splash Amour'
        assert datos[0]['facturado'] == 10625.0

    def test_una_transaccion_ligada_a_dos_ventas_no_se_cuenta_dos_veces(self):
        """
        `conto_sales` es un many-to-many. Sin `distinct`, el join la devuelve una
        vez por cada venta y el facturado sale al doble.
        """
        centro, sucursal, conto, tienda = escenario()
        producto = make_product(sucursal, sku='BS-1', name='Body Splash Amour')
        v1 = hacer_venta(conto, '10625.00', cupon=hacer_cupon(tienda, codigo='APP-A'), voucher='a1')
        v2 = hacer_venta(conto, '10625.00', cupon=hacer_cupon(tienda, codigo='APP-B'), voucher='a2')
        t = hacer_transaccion(sucursal, producto, '10625.00', v1)
        v2.transactions.add(t)

        datos = api(centro).get(URL).json()['productos']

        assert datos[0]['ventas'] == 1
        assert datos[0]['facturado'] == 10625.0

    def test_las_clientas_salen_del_cupon_y_no_del_comprador(self):
        """
        El cupón dice a quién se lo dimos, que es la clienta de la plataforma.
        El comprador de Tienda Nube puede ser la misma persona con otro mail.
        """
        centro, _, conto, tienda = escenario()
        clienta = Cliente.objects.create(
            centro_estetica=centro, nombre='Ana', apellido='Gómez', telefono='11',
        )
        hacer_venta(conto, '10625.00',
                    cupon=hacer_cupon(tienda, cliente=clienta), voucher='a1')

        datos = api(centro).get(URL).json()['clientas']

        assert datos == [{
            'cliente_id': clienta.id, 'cliente': 'Gómez, Ana',
            'compras': 1, 'gastado': 10625.0,
        }]


@pytest.mark.django_db
class TestCupones:

    def test_cuenta_cuantas_compras_se_empezaron_y_no_se_terminaron(self):
        """
        La métrica que solo nosotros podemos calcular: Tienda Nube no sabe que
        un cupón se emite al tocar «Comprar». Cada uno sin usar es un carrito
        abandonado en el checkout.
        """
        centro, _, _, tienda = escenario()
        hacer_cupon(tienda, codigo='APP-A', usado=True)
        hacer_cupon(tienda, codigo='APP-B', usado=False)
        hacer_cupon(tienda, codigo='APP-C', usado=False)
        hacer_cupon(tienda, codigo='APP-D', usado=False)

        datos = api(centro).get(URL).json()['cupones']

        assert datos == {
            'emitidos': 4, 'usados': 1, 'sin_usar': 3, 'conversion': 25.0,
        }

    def test_sin_cupones_no_divide_por_cero(self):
        centro, _, _, _ = escenario()

        datos = api(centro).get(URL).json()['cupones']

        assert datos['conversion'] == 0.0


@pytest.mark.django_db
class TestAislamiento:

    def test_no_se_ven_las_ventas_de_otro_centro(self):
        """
        El centro sale del usuario, nunca del pedido. Sumar las ventas de otro
        inquilino no es un error de redondeo.
        """
        centro_a, _, conto_a, tienda_a = escenario('A', 'acc-a')
        _, _, conto_b, tienda_b = escenario('B', 'acc-b')
        hacer_venta(conto_a, '1000.00', cupon=hacer_cupon(tienda_a, codigo='APP-A'), voucher='a1')
        hacer_venta(conto_b, '9999.00', cupon=hacer_cupon(tienda_b, codigo='APP-B'), voucher='b1')

        datos = api(centro_a).get(URL).json()

        assert datos['resumen']['app']['facturado'] == 1000.0
        assert datos['cupones']['emitidos'] == 1

    def test_una_sucursal_ajena_se_rechaza(self):
        centro_a, _, _, _ = escenario('A', 'acc-a')
        _, sucursal_b, _, _ = escenario('B', 'acc-b')

        respuesta = api(centro_a).get(URL, {'sucursal_id': sucursal_b.id})

        assert respuesta.status_code == 404

    def test_un_empleado_no_ve_la_medicion(self):
        """Analytics global es de Admin y Manager, como el resto del módulo."""
        centro, _, _, _ = escenario()

        respuesta = api(centro, rol='EMPLEADO').get(URL)

        assert respuesta.status_code == 403

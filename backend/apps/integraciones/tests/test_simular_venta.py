"""
Tests del comando que ensaya la vuelta de una compra de la app.

El comando existe porque los pasos 10 y 11 del §4 —Conto importa la venta y la
atribución la marca como de la app— **no se pueden ejercitar contra la tienda de
demostración**: Conto mira la cuenta del centro, atada a la tienda real, así que
una compra en la demo nunca vuelve por ahí.

Un ensayo que miente es peor que no ensayar, así que lo que se cuida es eso:

1. **Que el comprobante simulado sea coherente.** El importador compara la suma
   de las líneas contra el total declarado y marca un descuadre si no dan. Un
   ensayo que arranca descuadrado no prueba nada de lo que dice probar.

2. **Que no deje ingresos huérfanos.** `_process_sale` hace
   `transactions.set(...)`, que reemplaza el vínculo pero no borra la fila
   anterior: reimportar el mismo comprobante deja una transacción colgada en el
   módulo financiero. Es plata que no entró contaminando justo los números de
   analytics que este comando ayuda a construir, y fue un defecto real de la
   primera versión.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoSale, CuponApp, TiendanubeIntegration

from .test_sync import make_product, make_syncable_center


@pytest.fixture(autouse=True)
def modo_desarrollo(settings):
    """El comando se niega a correr con DEBUG apagado; acá se da por prendido."""
    settings.DEBUG = True


def escenario(porcentaje='15.00', precio='19000.00'):
    """Un centro que puede recibir una venta simulada: Conto, tienda y cupón."""
    centro, sucursal, conto = make_syncable_center('Ame', 'acc-sim')
    make_product(sucursal, sku='CRM-1', name='Crema Hidratante', price=precio)

    tienda = TiendanubeIntegration.objects.create(
        center=centro, store_id='8100688', token='tok',
    )
    clienta = Cliente.objects.create(
        centro_estetica=centro, nombre='Ana', apellido='Gómez', telefono='11',
    )
    cupon = CuponApp.objects.create(
        integration=tienda,
        cliente=clienta,
        code='APP-K3F9XQ7M',
        percentage=Decimal(porcentaje),
        tiendanube_coupon_id='999',
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return centro, conto, cupon, clienta


@pytest.mark.django_db
class TestSimulacion:

    def test_el_comprobante_cuadra_con_el_descuento_del_cupon(self):
        """
        $19.000 con 15% son $16.150. Si el total y las líneas no cuadraran, el
        importador marcaría un descuadre y el ensayo estaría reportando un
        problema que inventó él mismo.
        """
        _, _, cupon, _ = escenario(porcentaje='15.00', precio='19000.00')

        call_command('simular_venta_app', cupon=cupon.code)

        venta = ContoSale.objects.get(voucher_id=f'SIM-{cupon.code}')
        assert venta.status == ContoSale.Status.PROCESSED
        assert venta.total_discrepancy is None
        assert venta.total == Decimal('16150.00')

        transaccion = venta.transactions.get()
        assert transaccion.amount == Decimal('16150.00')

    def test_la_venta_queda_atribuida_a_la_app_y_a_la_clienta(self):
        """Es lo único que el comando existe para mostrar."""
        _, _, cupon, clienta = escenario()

        call_command('simular_venta_app', cupon=cupon.code)

        venta = ContoSale.objects.get(voucher_id=f'SIM-{cupon.code}')
        assert venta.es_venta_de_la_app
        assert venta.cupon_app == cupon
        assert venta.coupon_code == cupon.code
        # El comprobante no trae comprador, así que gana la clienta del cupón.
        assert venta.transactions.get().client == clienta

        cupon.refresh_from_db()
        assert cupon.used_at is not None

    def test_un_cupon_del_cero_por_ciento_no_arma_linea_de_descuento(self):
        """
        A una clienta sin descuento le corresponde pagar precio de lista. Una
        línea de descuento en cero haría que el importador intente prorratear
        nada y no aporta.
        """
        _, _, cupon, _ = escenario(porcentaje='0.00', precio='19000.00')

        call_command('simular_venta_app', cupon=cupon.code)

        venta = ContoSale.objects.get(voucher_id=f'SIM-{cupon.code}')
        tipos = [i['tipo'] for i in venta.payload['items']]
        assert 'DESCUENTO' not in tipos
        assert venta.total == Decimal('19000.00')
        assert venta.total_discrepancy is None


@pytest.mark.django_db
class TestNoDejaBasura:

    def test_no_se_puede_ensayar_dos_veces_sin_deshacer(self):
        """
        El defecto que este guard previene: la segunda corrida reimportaba el
        comprobante, y como `transactions.set(...)` reemplaza el vínculo sin
        borrar la fila, quedaba un ingreso huérfano por corrida.
        """
        _, _, cupon, _ = escenario()
        call_command('simular_venta_app', cupon=cupon.code)

        with pytest.raises(CommandError) as exc:
            call_command('simular_venta_app', cupon=cupon.code)

        assert '--deshacer' in str(exc.value)
        assert Transaction.objects.count() == 1
        assert ContoSale.objects.count() == 1

    def test_deshacer_borra_la_venta_las_transacciones_y_libera_el_cupon(self):
        _, _, cupon, _ = escenario()
        call_command('simular_venta_app', cupon=cupon.code)

        call_command('simular_venta_app', cupon=cupon.code, deshacer=True)

        assert not ContoSale.objects.filter(voucher_id__startswith='SIM-').exists()
        assert not Transaction.objects.exists()
        cupon.refresh_from_db()
        assert cupon.used_at is None

    def test_despues_de_deshacer_se_puede_volver_a_ensayar(self):
        """Liberar el cupón es lo que hace repetible el ensayo."""
        _, _, cupon, _ = escenario()
        call_command('simular_venta_app', cupon=cupon.code)
        call_command('simular_venta_app', cupon=cupon.code, deshacer=True)

        call_command('simular_venta_app', cupon=cupon.code)

        assert ContoSale.objects.get(voucher_id=f'SIM-{cupon.code}').es_venta_de_la_app
        assert Transaction.objects.count() == 1


@pytest.mark.django_db
class TestGuardas:

    def test_con_debug_apagado_no_corre(self, settings):
        """
        Crea ingresos en el módulo financiero. En la base del centro eso es
        plata que no entró, y desde adentro nadie distingue un ensayo de un
        error.
        """
        settings.DEBUG = False
        _, _, cupon, _ = escenario()

        with pytest.raises(CommandError) as exc:
            call_command('simular_venta_app', cupon=cupon.code)

        assert '--forzar' in str(exc.value)
        assert not Transaction.objects.exists()

    def test_con_forzar_corre_igual(self, settings):
        settings.DEBUG = False
        _, _, cupon, _ = escenario()

        call_command('simular_venta_app', cupon=cupon.code, forzar=True)

        assert ContoSale.objects.get(voucher_id=f'SIM-{cupon.code}').es_venta_de_la_app

    def test_un_cupon_que_no_existe_se_explica(self):
        escenario()

        with pytest.raises(CommandError) as exc:
            call_command('simular_venta_app', cupon='APP-NOEXISTE')

        assert 'APP-NOEXISTE' in str(exc.value)

    def test_un_producto_de_otro_centro_se_rechaza(self):
        """
        La barrera de siempre: un id de otro centro no es un error de tipeo
        inocente, es la línea entre los datos de dos inquilinos.
        """
        _, _, cupon, _ = escenario()
        _, otra_sucursal, _ = make_syncable_center('Otro', 'acc-otro')
        ajeno = make_product(otra_sucursal, sku='AJENO-1', name='Ajeno')

        with pytest.raises(CommandError) as exc:
            call_command('simular_venta_app', cupon=cupon.code, productos=[ajeno.id])

        assert str(ajeno.id) in str(exc.value)
        assert not Transaction.objects.exists()

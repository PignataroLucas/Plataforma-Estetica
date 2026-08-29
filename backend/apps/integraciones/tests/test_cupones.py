"""
Tests de la emisión y la limpieza de cupones de la app.

Dos cosas se cuidan acá, y las dos son plata:

1. **Que el porcentaje del cupón sea el mismo que la app mostró.** Sale de
   `Cliente.descuento_app` y de ningún otro lado (COMPRA_EN_APP_SPEC.md §5.8).
   En cuanto se recalcule por otro camino, la clienta ve un precio y paga otro,
   que es la trampa del §6.1.
2. **Que un cupón que no se pudo crear en Tienda Nube no quede guardado como si
   existiera.** La atribución del §5.6 busca códigos contra esta tabla: una fila
   fantasma es una venta que después no se puede explicar.
"""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.clientes.models import Cliente, SegmentoApp
from apps.empleados.models import CentroEstetica
from apps.integraciones.cupones import (
    PREFIJO,
    SinDescuento,
    SinIntegracion,
    emitir_cupon,
    generar_codigo,
    limpiar_vencidos,
)
from apps.integraciones.models import CuponApp, TiendanubeIntegration
from apps.integraciones.tiendanube import TiendanubeError


def hacer_centro(nombre='Ame'):
    return CentroEstetica.objects.create(
        nombre=nombre, telefono='1', email=f'{nombre}@test.local'
    )


def hacer_clienta(centro, porcentaje='15.00'):
    if porcentaje is not None:
        SegmentoApp.objects.create(
            centro_estetica=centro, nombre='General de la app',
            porcentaje_descuento=Decimal(porcentaje), es_predeterminado=True,
        )
    return Cliente.objects.create(
        centro_estetica=centro, nombre='Ana', apellido='Gómez', telefono='11',
    )


def hacer_integracion(centro, **extra):
    datos = {'store_id': '8100688', 'token': 'tok', 'is_active': True}
    datos.update(extra)
    return TiendanubeIntegration.objects.create(center=centro, **datos)


@pytest.mark.django_db
class TestEmision:

    def test_el_cupon_lleva_el_descuento_de_la_clienta(self):
        centro = hacer_centro()
        hacer_integracion(centro)
        clienta = hacer_clienta(centro, '15.00')

        with patch('apps.integraciones.cupones.TiendanubeClient.create_coupon',
                   return_value={'id': 67713598}) as crear:
            cupon = emitir_cupon(clienta)

        assert cupon.percentage == Decimal('15.00')
        assert cupon.percentage == clienta.descuento_app
        # Y el mismo número viaja a Tienda Nube.
        assert crear.call_args.args[0]['value'] == '15.00'

    def test_el_segmento_propio_gana_sobre_el_general(self):
        centro = hacer_centro()
        hacer_integracion(centro)
        clienta = hacer_clienta(centro, '10.00')
        vip = SegmentoApp.objects.create(
            centro_estetica=centro, nombre='VIP', porcentaje_descuento=Decimal('20.00'),
        )
        clienta.segmento_app = vip
        clienta.save()

        with patch('apps.integraciones.cupones.TiendanubeClient.create_coupon',
                   return_value={'id': 1}):
            cupon = emitir_cupon(clienta)

        assert cupon.percentage == Decimal('20.00')

    def test_el_codigo_tiene_el_prefijo_y_no_es_secuencial(self):
        """
        El prefijo hace que los cupones de la app se puedan agrupar o excluir en
        el reporte de Conto (§5.7). Que sea impredecible es lo que evita que
        alguien adivine el próximo desde la tienda web (§3.2).
        """
        codigos = {generar_codigo() for _ in range(50)}

        assert len(codigos) == 50
        assert all(c.startswith(PREFIJO) for c in codigos)

    def test_un_solo_uso_y_vigencia_corta(self):
        """Es el candado del §3.2: un código filtrado sirve una vez y por una hora."""
        centro = hacer_centro()
        hacer_integracion(centro)
        clienta = hacer_clienta(centro)

        with patch('apps.integraciones.cupones.TiendanubeClient.create_coupon',
                   return_value={'id': 1}) as crear:
            cupon = emitir_cupon(clienta)

        payload = crear.call_args.args[0]
        assert payload['max_uses'] == 1
        assert cupon.expires_at - cupon.issued_at <= timedelta(hours=1)

    def test_el_apilado_sale_de_la_configuracion_del_centro(self):
        """
        La decisión del §7.2 es del centro y vive en la integración. Se manda
        explícita para no depender del default de Tienda Nube.
        """
        centro = hacer_centro()
        hacer_integracion(centro, coupons_combine_with_other_discounts=False)
        clienta = hacer_clienta(centro)

        with patch('apps.integraciones.cupones.TiendanubeClient.create_coupon',
                   return_value={'id': 1}) as crear:
            emitir_cupon(clienta)

        assert crear.call_args.args[0]['combines_with_other_discounts'] is False

    def test_sin_descuento_no_se_emite_nada(self):
        """
        Un cupón del 0% no descuenta y deja una fila por compra en el panel del
        centro. Es el estado de hoy: el segmento general arranca en 0.
        """
        centro = hacer_centro()
        hacer_integracion(centro)
        clienta = hacer_clienta(centro, '0.00')

        with pytest.raises(SinDescuento):
            emitir_cupon(clienta)

        assert not CuponApp.objects.exists()

    def test_sin_tienda_vinculada_lo_dice_con_todas_las_letras(self):
        centro = hacer_centro()
        clienta = hacer_clienta(centro)

        with pytest.raises(SinIntegracion) as exc:
            emitir_cupon(clienta)

        assert 'Tienda Nube' in str(exc.value)

    def test_si_tienda_nube_falla_no_queda_una_fila_fantasma(self):
        """
        Guardar el cupón antes de crearlo allá dejaría un código que la clienta
        no puede usar y que la atribución del §5.6 nunca va a encontrar.
        """
        centro = hacer_centro()
        hacer_integracion(centro)
        clienta = hacer_clienta(centro)

        with patch('apps.integraciones.cupones.TiendanubeClient.create_coupon',
                   side_effect=TiendanubeError('422')):
            with pytest.raises(TiendanubeError):
                emitir_cupon(clienta)

        assert not CuponApp.objects.exists()

    def test_la_tienda_de_otro_centro_no_se_usa(self):
        """Emitir en la tienda equivocada es descontarle plata a otro."""
        centro_a, centro_b = hacer_centro('A'), hacer_centro('B')
        hacer_integracion(centro_b)
        clienta_a = hacer_clienta(centro_a)

        with pytest.raises(SinIntegracion):
            emitir_cupon(clienta_a)


@pytest.mark.django_db
class TestLimpieza:

    def _cupon(self, centro, **extra):
        datos = {
            'integration': TiendanubeIntegration.objects.get(center=centro),
            'code': 'APP-XXXXXXXX',
            'percentage': Decimal('15.00'),
            'tiendanube_coupon_id': '999',
            'expires_at': timezone.now() - timedelta(hours=2),
        }
        datos.update(extra)
        return CuponApp.objects.create(**datos)

    def test_borra_los_vencidos_sin_usar(self):
        centro = hacer_centro()
        hacer_integracion(centro)
        cupon = self._cupon(centro)

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon') as borrar:
            borrados, errores = limpiar_vencidos()

        cupon.refresh_from_db()
        assert (borrados, errores) == (1, [])
        assert borrar.call_args.args[0] == '999'
        # La fila queda: es de lo que sale cuántas compras se empezaron y no
        # se terminaron (§5.7).
        assert cupon.revoked_at is not None

    def test_no_toca_los_que_todavia_no_vencieron(self):
        centro = hacer_centro()
        hacer_integracion(centro)
        self._cupon(centro, expires_at=timezone.now() + timedelta(minutes=30))

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon') as borrar:
            borrados, _ = limpiar_vencidos()

        assert borrados == 0
        assert not borrar.called

    def test_no_toca_los_usados(self):
        """
        Un cupón usado es una venta. Borrarlo de Tienda Nube dejaría la orden
        sin el descuento que la explica.
        """
        centro = hacer_centro()
        hacer_integracion(centro)
        self._cupon(centro, used_at=timezone.now())

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon') as borrar:
            borrados, _ = limpiar_vencidos()

        assert borrados == 0
        assert not borrar.called

    def test_no_reintenta_los_ya_borrados(self):
        centro = hacer_centro()
        hacer_integracion(centro)
        self._cupon(centro, revoked_at=timezone.now())

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon') as borrar:
            limpiar_vencidos()

        assert not borrar.called

    def test_un_error_no_frena_al_resto(self):
        """
        Con miles de cupones, uno que falla no puede dejar sin limpiar a los
        demás. Se reporta y se reintenta en la corrida siguiente.
        """
        centro = hacer_centro()
        hacer_integracion(centro)
        malo = self._cupon(centro, code='APP-MALO1234', tiendanube_coupon_id='1')
        bueno = self._cupon(centro, code='APP-BUENO123', tiendanube_coupon_id='2')

        def borrar(coupon_id):
            if coupon_id == '1':
                raise TiendanubeError('500')

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon',
                   side_effect=borrar):
            borrados, errores = limpiar_vencidos()

        malo.refresh_from_db()
        bueno.refresh_from_db()
        assert borrados == 1
        assert len(errores) == 1
        assert malo.revoked_at is None
        assert bueno.revoked_at is not None

    def test_si_el_centro_desinstalo_la_app_no_se_reintenta_para_siempre(self):
        """Sin token no hay a quién pedirle el borrado: los cupones allá ya no existen."""
        centro = hacer_centro()
        hacer_integracion(centro, is_active=False)
        cupon = self._cupon(centro)

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon') as borrar:
            borrados, errores = limpiar_vencidos()

        cupon.refresh_from_db()
        assert (borrados, errores) == (1, [])
        assert not borrar.called
        assert cupon.revoked_at is not None

    def test_el_comando_corre(self):
        centro = hacer_centro()
        hacer_integracion(centro)
        self._cupon(centro)

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon'):
            call_command('limpiar_cupones_app')

        assert CuponApp.objects.filter(revoked_at__isnull=False).count() == 1

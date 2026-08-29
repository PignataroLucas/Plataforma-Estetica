"""
Tests del emparejador de productos con sus variantes de Tienda Nube.

El emparejamiento es por nombre y el nombre miente seguido, así que lo que se
cuida acá es el criterio conservador: **ante la duda, no escribir**. Una
variante mal asignada manda al carrito un producto que la clienta no eligió, y
eso se descubre recién cuando llega el pedido.

Sin variante el producto no se puede comprar (COMPRA_EN_APP_SPEC.md §5.2), que
es un problema visible y arreglable a mano. Con la variante equivocada, no.
"""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.empleados.models import CentroEstetica, Sucursal
from apps.integraciones.models import TiendanubeIntegration
from apps.inventario.models import Producto


def hacer_centro(nombre='Ame'):
    centro = CentroEstetica.objects.create(
        nombre=nombre, telefono='1', email=f'{nombre}@test.local'
    )
    sucursal = Sucursal.objects.create(
        centro_estetica=centro, nombre=f'Suc {nombre}', direccion='x',
        telefono='1', ciudad='CABA', provincia='CABA',
    )
    TiendanubeIntegration.objects.create(
        center=centro, store_id=f'810{nombre}', token='tok', store_name='Ame Demo',
    )
    return centro, sucursal


def hacer_producto(sucursal, nombre, **extra):
    datos = {
        'nombre': nombre, 'precio_costo': Decimal('100'), 'precio_venta': Decimal('200'),
    }
    datos.update(extra)
    return Producto.objects.create(sucursal=sucursal, **datos)


def tn_producto(nombre, variantes=('1001',)):
    return {
        'id': '900',
        'name': {'es': nombre},
        'variants': [{'id': v, 'sku': ''} for v in variantes],
    }


def correr(catalogo, *args):
    with patch('apps.integraciones.tiendanube.TiendanubeClient.iter_products',
               return_value=iter(catalogo)):
        call_command('emparejar_variantes_tiendanube', *args)


@pytest.mark.django_db
class TestEmparejamiento:

    def test_no_escribe_nada_sin_aplicar(self):
        """El default es proponer. Escribir es una decisión explícita."""
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Serum Vitamina C 30ml')

        correr([tn_producto('Serum Vitamina C 30ml')])

        producto.refresh_from_db()
        assert producto.tiendanube_product_id == ''

    def test_un_nombre_igual_se_empareja_solo(self):
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Serum Vitamina C 30ml')

        correr([tn_producto('Serum Vitamina C 30ml')], '--aplicar')

        producto.refresh_from_db()
        # Los dos: el de producto arma el carrito, el de variante identifica cuál.
        assert producto.tiendanube_product_id == '900'
        assert producto.tiendanube_variant_id == '1001'

    def test_dos_candidatos_parecidos_quedan_para_una_persona(self):
        """
        "Body Splash Amour" y "Body Splash Brume" se parecen demasiado entre sí.
        Elegir por unos puntos de similitud es exactamente cómo se manda el
        perfume equivocado.
        """
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Body Splash 150 ml')

        correr([
            {'id': '1', 'name': {'es': 'Body Splash Amour 150 ml'},
             'variants': [{'id': '1001', 'sku': ''}]},
            {'id': '2', 'name': {'es': 'Body Splash Brume 150 ml'},
             'variants': [{'id': '1002', 'sku': ''}]},
        ], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_product_id == ''

    def test_un_producto_con_varias_variantes_no_se_resuelve_por_nombre(self):
        """
        Cuál de los dos tamaños es "el" producto no está en el nombre. Va a la
        lista de decisiones humanas en vez de elegir el primero.
        """
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Bruma Hidratante')

        correr([tn_producto('Bruma Hidratante', variantes=('1001', '1002'))], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_product_id == ''

    def test_una_variante_ya_usada_no_se_reasigna(self):
        """
        Dos productos nuestros apuntando a la misma variante mandan el artículo
        equivocado para uno de los dos.
        """
        _, sucursal = hacer_centro()
        hacer_producto(sucursal, 'Serum Vitamina C 30ml', tiendanube_variant_id='1001')
        otro = hacer_producto(sucursal, 'Serum Vitamina C 30 ml')

        correr([tn_producto('Serum Vitamina C 30ml')], '--aplicar')

        otro.refresh_from_db()
        assert otro.tiendanube_product_id == ''

    def test_no_toca_los_productos_de_otro_centro(self):
        _, sucursal_a = hacer_centro('A')
        _, sucursal_b = hacer_centro('B')
        ajeno = hacer_producto(sucursal_b, 'Serum Vitamina C 30ml')

        correr([tn_producto('Serum Vitamina C 30ml')], '--aplicar', '--centro',
               str(sucursal_a.centro_estetica_id))

        ajeno.refresh_from_db()
        assert ajeno.tiendanube_product_id == ''

    def test_sin_tienda_vinculada_no_corre(self):
        centro = CentroEstetica.objects.create(
            nombre='Sin tienda', telefono='1', email='x@test.local'
        )
        with pytest.raises(CommandError) as exc:
            call_command('emparejar_variantes_tiendanube', '--centro', str(centro.id))

        assert 'vincular_tiendanube' in str(exc.value)

    def test_un_nombre_en_otro_idioma_igual_se_lee(self):
        """
        Tienda Nube devuelve los textos por idioma. Si la tienda tiene cargado
        portugués además de español, el diccionario no puede dejar el producto
        sin emparejar.
        """
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Serum Vitamina C 30ml')

        correr([{
            'id': '1',
            'name': {'pt': 'Serum Vitamina C 30ml'},
            'variants': [{'id': '1001', 'sku': ''}],
        }], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == '1001'

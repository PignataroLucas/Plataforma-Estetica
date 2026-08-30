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


def tn_completo(nombre, variante_id='1001', sku='', precio='200', producto_id='900'):
    """Un producto de Tienda Nube con SKU y precio, que es lo que mira el emparejador."""
    return {
        'id': producto_id,
        'name': {'es': nombre},
        'variants': [{'id': variante_id, 'sku': sku, 'price': precio}],
    }


@pytest.mark.django_db
class TestEmparejaPorSku:
    """
    El SKU es la señal más fuerte que hay y estaba sin usar: el comando lo leía
    de Tienda Nube y solo lo imprimía en el reporte.

    Dos productos con el mismo SKU son el mismo producto, sin importar cómo esté
    escrito el nombre de cada lado. Eso resuelve el caso que el nombre no puede:
    catálogos donde varios artículos se llaman casi igual.
    """

    def test_un_sku_igual_empareja_aunque_el_nombre_no_se_parezca(self):
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Bruma Hidratante Y Calmante', sku='BRU-150')

        correr([tn_completo('Bruma Descongestiva x150ml', sku='BRU-150')], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == '1001'

    def test_el_sku_se_compara_normalizado(self):
        """Espacios y mayúsculas no pueden decidir si dos productos son el mismo."""
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Serum', sku=' bru-150 ')

        correr([tn_completo('Otra Cosa', sku='BRU-150')], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == '1001'

    def test_un_sku_repetido_en_tienda_nube_no_se_usa(self):
        """
        Si el identificador que tenía que ser único aparece dos veces, elegir uno
        es adivinar. Cae a la pasada por nombre, que en este caso tampoco
        encuentra nada parecido.
        """
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Zzz Producto Raro', sku='DUP-1')

        correr([
            tn_completo('Uno', variante_id='1001', sku='DUP-1', producto_id='900'),
            tn_completo('Dos', variante_id='1002', sku='DUP-1', producto_id='901'),
        ], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == ''

    def test_el_sku_gana_sobre_el_parecido_de_nombre(self):
        """
        Un producto que se llama igual que otro pero cuyo SKU apunta a un tercero
        tiene que ir donde dice el SKU. El nombre es una pista; el SKU, un dato.
        """
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Body Splash Amour', sku='AMOUR-1')

        correr([
            tn_completo('Body Splash Amour', variante_id='1001', sku='OTRO', producto_id='900'),
            tn_completo('Nombre Que No Se Parece', variante_id='1002', sku='AMOUR-1', producto_id='901'),
        ], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == '1002'


@pytest.mark.django_db
class TestElPrecioComoTestigo:
    """
    El precio no empareja: solo desconfía.

    Un nombre puede parecerse por casualidad, y ahí el precio es lo único que
    delata que son productos distintos. El caso que motivó esto es real: en la
    tienda de prueba todo costaba $100, y un producto nuestro de $19.000 se
    habría emparejado por nombre sin que nada lo frenara.
    """

    def test_un_precio_disparatado_baja_el_match_a_dudoso(self):
        _, sucursal = hacer_centro()
        producto = hacer_producto(
            sucursal, 'Serum Facial', precio_venta=Decimal('19000'),
        )

        correr([tn_completo('Serum Facial', precio='100')], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == ''

    def test_una_diferencia_razonable_no_frena_nada(self):
        """
        Los precios se desfasan solos: el sync corre cada tanto y en Tienda Nube
        puede haber una promoción. Si el testigo fuera estricto, no emparejaría
        casi nada.
        """
        _, sucursal = hacer_centro()
        producto = hacer_producto(
            sucursal, 'Serum Facial', precio_venta=Decimal('20000'),
        )

        correr([tn_completo('Serum Facial', precio='17000')], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == '1001'

    def test_sin_precio_del_otro_lado_no_bloquea(self):
        """
        Sin dato no se puede desconfiar. Bloquear por ausencia dejaría sin
        emparejar a productos perfectamente válidos.
        """
        _, sucursal = hacer_centro()
        producto = hacer_producto(sucursal, 'Serum Facial')

        correr([tn_completo('Serum Facial', precio=None)], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == '1001'

    def test_el_precio_no_frena_un_emparejamiento_por_sku(self):
        """
        El SKU es certeza y el precio solo una sospecha: una promoción agresiva
        no puede desarmar una coincidencia de identificador.
        """
        _, sucursal = hacer_centro()
        producto = hacer_producto(
            sucursal, 'Serum Facial', sku='SER-1', precio_venta=Decimal('19000'),
        )

        correr([tn_completo('Cualquier Cosa', sku='SER-1', precio='100')], '--aplicar')

        producto.refresh_from_db()
        assert producto.tiendanube_variant_id == '1001'

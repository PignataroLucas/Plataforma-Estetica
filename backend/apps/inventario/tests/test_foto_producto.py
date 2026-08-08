"""
Tests de la foto de producto: storage público y miniatura.

Dos cosas se cuidan acá:

1. Que la foto de producto use el storage `publico` y que los campos sensibles
   sigan en `default`. Es el corazón de la decisión de no apuntar `default` a
   S3: un campo nuevo que nadie pensó tiene que nacer privado.
2. Que la miniatura se genere al subir y solo al subir. Regenerarla en cada
   guardado significaría bajar el original de S3 cada vez que alguien ajusta el
   stock.
"""
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.clientes.models import Cliente, HistorialCliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.inventario.models import Producto
from apps.inventario.serializers import ProductoCreateUpdateSerializer
from config.storage import storage_publico


@pytest.fixture(autouse=True)
def media_aislada(settings, tmp_path):
    """Las fotos de los tests no tienen por qué aterrizar en backend/media."""
    settings.MEDIA_ROOT = tmp_path


def foto_de_prueba(nombre='crema.jpg', ancho=1200, alto=1600):
    """Una imagen vertical y grande, como las que saca un celular."""
    imagen = Image.new('RGB', (ancho, alto))
    # Ruido suave para que el JPEG no comprima a nada y la comparación de
    # tamaños contra la miniatura signifique algo.
    for x in range(0, ancho, 4):
        for y in range(0, alto, 4):
            imagen.putpixel((x, y), ((x * 7) % 256, (y * 13) % 256, (x + y) % 256))

    buffer = BytesIO()
    imagen.save(buffer, format='JPEG', quality=95)
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/jpeg')


def make_center(name='Ame'):
    center = CentroEstetica.objects.create(
        nombre=name, telefono='1', email=f'{name}@test.local'
    )
    branch = Sucursal.objects.create(
        centro_estetica=center, nombre=f'Sucursal {name}',
        direccion='x', telefono='1', ciudad='CABA', provincia='CABA',
    )
    user = Usuario.objects.create_user(
        username=f'admin_{name}', password='x', rol='ADMIN',
        centro_estetica=center, sucursal=branch,
    )
    return center, branch, user


def make_product(branch, **overrides):
    datos = {
        'sucursal': branch, 'nombre': 'Crema Multivitamínica',
        'precio_costo': Decimal('100.00'), 'precio_venta': Decimal('200.00'),
    }
    datos.update(overrides)
    return Producto.objects.create(**datos)


def api(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def storage_declarado(modelo, campo):
    """
    El storage tal como quedó declarado en el campo.

    Se pregunta por `deconstruct()` y no por `field.storage` a propósito: la
    instancia concreta se resuelve una sola vez al importar el modelo, así que
    compararla contra `storages['publico']` falla en cuanto otro test toca
    settings.STORAGES y el handler rearma su caché. Lo que importa igual es la
    declaración: de qué storage optó el campo.
    """
    return modelo._meta.get_field(campo).deconstruct()[3].get('storage')


class TestQueCamposUsanElBucket:
    """
    Estos no necesitan base de datos: preguntan por la configuración del campo.
    """

    @pytest.mark.parametrize('modelo, campo', [
        (Producto, 'foto'),
        (Producto, 'foto_thumb'),
        (CentroEstetica, 'logo'),
    ])
    def test_los_campos_del_catalogo_optan_por_el_storage_publico(self, modelo, campo):
        assert storage_declarado(modelo, campo) is storage_publico

    @pytest.mark.parametrize('modelo, campo', [
        (Cliente, 'foto'),
        (HistorialCliente, 'foto_antes'),
        (HistorialCliente, 'foto_despues'),
        (Usuario, 'foto'),
    ])
    def test_los_campos_sensibles_siguen_en_el_storage_default(self, modelo, campo):
        """
        Son datos de salud de personas identificables. El día que se suban van a
        necesitar un bucket privado con URLs firmadas, no el bucket del
        catálogo, que es de lectura pública. Que el campo no declare storage es
        exactamente la propiedad que se quiere: lo que nadie pensó nace privado.
        """
        assert storage_declarado(modelo, campo) is None
        assert modelo._meta.get_field(campo).storage is default_storage


@pytest.mark.django_db
class TestMiniatura:

    def test_subir_una_foto_genera_la_miniatura(self):
        _, branch, _ = make_center()

        producto = make_product(branch, foto=foto_de_prueba())

        assert producto.foto_thumb
        assert producto.foto_thumb.name.endswith('.webp')

        with Image.open(producto.foto_thumb) as thumb:
            assert thumb.width == 400
            # Alto proporcional: la vertical de 1200x1600 no se deforma.
            assert thumb.height == 533

        assert producto.foto_thumb.size < producto.foto.size

    def test_la_miniatura_sobrevive_a_releer_el_producto(self):
        _, branch, _ = make_center()
        producto = make_product(branch, foto=foto_de_prueba())

        assert Producto.objects.get(pk=producto.pk).foto_thumb.name == producto.foto_thumb.name

    def test_guardar_sin_tocar_la_foto_no_regenera_la_miniatura(self):
        """
        Con `file_overwrite=False` regenerar deja un archivo nuevo cada vez. Si
        se regenerara en cada guardado, un ajuste de stock ensuciaría el bucket
        y pagaría una descarga del original.
        """
        _, branch, _ = make_center()
        producto = make_product(branch, foto=foto_de_prueba())
        miniatura = producto.foto_thumb.name

        producto.stock_actual = 5
        producto.save()

        assert producto.foto_thumb.name == miniatura

    def test_cambiar_la_foto_reemplaza_la_miniatura(self):
        _, branch, _ = make_center()
        producto = make_product(branch, foto=foto_de_prueba('primera.jpg'))
        miniatura_vieja = producto.foto_thumb.name

        producto.foto = foto_de_prueba('segunda.jpg')
        producto.save()

        assert producto.foto_thumb.name != miniatura_vieja
        assert 'segunda' in producto.foto_thumb.name
        # La vieja la generó este código y no la referencia nadie: se borra.
        assert not producto.foto_thumb.storage.exists(miniatura_vieja)

    def test_quitar_la_foto_deja_el_producto_sin_miniatura(self):
        _, branch, _ = make_center()
        producto = make_product(branch, foto=foto_de_prueba())

        producto.foto = None
        producto.save()

        assert not producto.foto_thumb

    def test_un_producto_sin_foto_no_rompe_al_guardar(self):
        _, branch, _ = make_center()
        producto = make_product(branch)

        producto.nombre = 'Otro nombre'
        producto.save()

        assert not producto.foto_thumb


@pytest.mark.django_db
class TestCargaDesdeLaApi:
    """
    El objetivo de la fase: que alguien del centro cargue foto y descripción
    desde el CRM, sin entrar al admin de Django.
    """

    def test_crear_un_producto_con_foto_por_multipart(self):
        _, branch, user = make_center()

        respuesta = api(user).post(
            reverse('producto-list'),
            {
                'nombre': 'Serum Vitamina C',
                'descripcion': 'Ilumina y unifica el tono.',
                'precio_costo': '100.00',
                'precio_venta': '200.00',
                'foto': foto_de_prueba(),
            },
            format='multipart',
        )

        assert respuesta.status_code == 201, respuesta.data
        producto = Producto.objects.get(pk=respuesta.data['id'])
        assert producto.descripcion == 'Ilumina y unifica el tono.'
        assert producto.foto
        assert producto.foto_thumb

    def test_editar_solo_la_descripcion_no_borra_la_foto(self):
        """
        El caso real: el centro carga la foto un día y la descripción al otro.
        """
        _, branch, user = make_center()
        producto = make_product(branch, foto=foto_de_prueba())
        foto = producto.foto.name

        respuesta = api(user).patch(
            reverse('producto-detail', args=[producto.pk]),
            {'descripcion': 'Textura ligera'},
            format='multipart',
        )

        assert respuesta.status_code == 200, respuesta.data
        producto.refresh_from_db()
        assert producto.foto.name == foto
        assert producto.descripcion == 'Textura ligera'

    def test_guardar_contenido_no_revierte_lo_que_dejo_el_sync_de_conto(self):
        """
        El defecto que arregla la fase 2, del lado del servidor.

        El formulario del CRM ya no manda stock ni precios, así que el guardado
        no puede pisar lo que el sync escribió mientras el formulario estaba
        abierto. Esta es la mitad que se puede verificar acá: que un guardado
        sin esos campos los deje intactos.
        """
        _, branch, user = make_center()
        producto = make_product(branch)

        # Lo que dejaría el sync entre que se abre el formulario y se guarda.
        Producto.objects.filter(pk=producto.pk).update(
            stock_actual=Decimal('9'),
            precio_costo=Decimal('777.00'),
            precio_venta=Decimal('1500.00'),
        )

        respuesta = api(user).patch(
            reverse('producto-detail', args=[producto.pk]),
            {'descripcion': 'Ilumina y unifica el tono.'},
            format='multipart',
        )

        assert respuesta.status_code == 200, respuesta.data
        producto.refresh_from_db()
        assert producto.descripcion == 'Ilumina y unifica el tono.'
        assert producto.stock_actual == Decimal('9')
        assert producto.precio_costo == Decimal('777.00')
        assert producto.precio_venta == Decimal('1500.00')

    def test_quitar_foto_limpia_la_foto_y_la_miniatura(self):
        """
        Un multipart no puede mandar un archivo vacío, así que sacar una foto
        equivocada necesita esta señal explícita. Sin ella habría que entrar al
        admin de Django, que es justo lo que esta fase viene a evitar.
        """
        _, branch, user = make_center()
        producto = make_product(branch, foto=foto_de_prueba())

        respuesta = api(user).patch(
            reverse('producto-detail', args=[producto.pk]),
            {'quitar_foto': True},
            format='multipart',
        )

        assert respuesta.status_code == 200, respuesta.data
        producto.refresh_from_db()
        assert not producto.foto
        assert not producto.foto_thumb


class TestTopeDeTamano:
    """
    Se prueba el validador directo y no por HTTP: DRF verifica que el archivo
    sea una imagen antes de llegar acá, así que un blob de 6 MB de basura
    fallaría por el motivo equivocado y armar un JPEG real de 6 MB para probar
    un `if` no vale la pena.
    """

    def test_una_foto_de_mas_de_5_mb_es_un_error_de_campo(self):
        gigante = SimpleUploadedFile('gigante.jpg', b'x' * (6 * 1024 * 1024))

        with pytest.raises(ValidationError) as error:
            ProductoCreateUpdateSerializer().validate_foto(gigante)

        assert '5 MB' in str(error.value)

    def test_una_foto_normal_pasa(self):
        assert ProductoCreateUpdateSerializer().validate_foto(foto_de_prueba())

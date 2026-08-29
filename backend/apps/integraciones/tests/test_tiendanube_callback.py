"""
Tests del callback de OAuth de Tienda Nube.

Todo lo de acá gira alrededor del mismo agujero: **Tienda Nube no acepta un
`state`**. Su URL de autorización recibe solo el id de la app y el callback
vuelve solo con `code` —verificado contra su documentación y contra su SDK
oficial de PHP—, así que cuando el token vuelve no hay nada en el pedido que
diga de qué centro es.

De ahí salen los dos defectos que estos tests previenen, y los dos son caros:

1. **Guardar la tienda de un centro contra otro.** El token autoriza a emitir
   cupones, o sea descuentos sobre ventas ajenas. Ante la duda el callback tiene
   que negarse, no elegir: por eso se prueba el caso de dos centros instalando a
   la vez y el de ninguno.
2. **Consumir la intención cuando la vinculación falló.** Dejaría al centro sin
   forma de reintentar sin volver a empezar de cero, con el código ya
   quemado — y el código dura cinco minutos.
"""
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from apps.empleados.models import CentroEstetica, Usuario
from apps.integraciones.instalacion import (
    VENTANA_DE_INSTALACION,
    TiendaDeOtroCentro,
    vincular,
)
from apps.integraciones.models import TiendanubeInstallIntent, TiendanubeIntegration
from apps.integraciones.tiendanube import TiendanubeAuthError

CALLBACK = reverse('tiendanube-oauth-callback')


@pytest.fixture(autouse=True)
def ventana_de_throttle_limpia():
    """
    Arrancar cada test con el contador del throttle en cero.

    El callback está limitado a 30 visitas por hora por IP, y ese contador vive
    en Redis: no lo limpia el rollback de la base. Corridos de a uno los tests
    pasan, y en la suite entera los últimos se comen un 429 por culpa de los
    primeros. Se limpia la ventana en vez de apagar el throttle, para que lo que
    corre en los tests sea lo mismo que corre en producción.
    """
    clave = 'throttle_tiendanube_oauth_127.0.0.1'
    cache.delete(clave)
    yield
    cache.delete(clave)


def abrir_intento(centro):
    """
    Declarar que este centro está instalando, como lo hace el admin.

    Es lo que reemplaza al `state` que Tienda Nube no tiene: sin una
    anotación previa, el token que vuelve no dice de qué centro es.
    """
    return TiendanubeInstallIntent.objects.create(
        center=centro, expires_at=timezone.now() + VENTANA_DE_INSTALACION,
    )


def hacer_centro(nombre='Ame'):
    return CentroEstetica.objects.create(
        nombre=nombre, telefono='1', email=f'{nombre}@test.local'
    )


def intercambio(store_id=8100688):
    return {
        'access_token': 'tok_nuevo',
        'user_id': store_id,
        'scope': 'read_products,write_coupons',
    }


def llamar_callback(client, code='abc', datos=None, **kwargs):
    """El callback, con el intercambio con Tienda Nube mockeado."""
    with patch('apps.integraciones.tiendanube_views.exchange_code_for_token',
               return_value=datos if datos is not None else intercambio(),
               **kwargs), \
         patch('apps.integraciones.instalacion.TiendanubeClient.get_store',
               return_value={'name': {'es': 'Ame Demo'},
                             'url_with_protocol': 'https://amedemo.mitiendanube.com'}):
        return client.get(CALLBACK, {'code': code})


@pytest.mark.django_db
class TestResolucionDelCentro:

    def test_una_reinstalacion_se_resuelve_sola_por_el_store_id(self, client):
        """
        El caso que más va a pasar y el único que no necesita ayuda: la tienda
        ya tiene integración, así que de qué centro es no está en discusión.
        Reinstalar emite un token nuevo, y sin esto el viejo queda guardado y
        los cupones fallan en silencio.
        """
        centro = hacer_centro()
        TiendanubeIntegration.objects.create(
            center=centro, store_id='8100688', token='tok_viejo', is_active=False,
        )

        respuesta = llamar_callback(client)

        assert respuesta.status_code == 200
        integracion = TiendanubeIntegration.objects.get(center=centro)
        assert integracion.token == 'tok_nuevo'
        assert integracion.is_active
        assert integracion.store_url == 'https://amedemo.mitiendanube.com'

    def test_una_primera_instalacion_se_resuelve_por_el_intento_abierto(self, client):
        centro = hacer_centro()
        intento = abrir_intento(centro)

        respuesta = llamar_callback(client)

        assert respuesta.status_code == 200
        integracion = TiendanubeIntegration.objects.get(center=centro)
        assert integracion.store_id == '8100688'
        assert integracion.token == 'tok_nuevo'

        intento.refresh_from_db()
        assert intento.consumed_at is not None

    def test_sin_intento_abierto_no_se_adivina_el_centro(self, client):
        """
        Llega un token válido de una tienda que no conocemos y nadie declaró
        estar instalando. El único centro de la base es un candidato tentador y
        adivinar sería exactamente el defecto: mañana hay dos.
        """
        hacer_centro()

        respuesta = llamar_callback(client)

        assert respuesta.status_code == 409
        assert not TiendanubeIntegration.objects.exists()

    def test_con_dos_centros_instalando_a_la_vez_se_niega(self, client):
        """
        Ambiguo de verdad: cualquiera de los dos podría ser. La respuesta
        correcta es no vincular. Que la operadora reintente cuesta un click;
        emitir cupones en la tienda del otro centro cuesta plata.
        """
        abrir_intento(hacer_centro('A'))
        abrir_intento(hacer_centro('B'))

        respuesta = llamar_callback(client)

        assert respuesta.status_code == 409
        assert not TiendanubeIntegration.objects.exists()

    def test_un_intento_vencido_no_sirve(self, client):
        centro = hacer_centro()
        intento = abrir_intento(centro)
        intento.expires_at = timezone.now() - VENTANA_DE_INSTALACION
        intento.save(update_fields=['expires_at'])

        respuesta = llamar_callback(client)

        assert respuesta.status_code == 409
        assert not TiendanubeIntegration.objects.exists()

    def test_una_tienda_ya_vinculada_no_se_la_lleva_el_intento_de_otro(self, client):
        """
        El store id ya es del centro A y hay un intento abierto del B. Gana el
        store id: la tienda se reautoriza contra su dueño y B no se lleva nada,
        que es el orden del §5.1 —quien autorizó tenía permisos sobre esa
        tienda, y esa tienda es de A—.

        El intento de B queda abierto: no se consumió con una vinculación que no
        fue suya.
        """
        centro_a, centro_b = hacer_centro('A'), hacer_centro('B')
        TiendanubeIntegration.objects.create(
            center=centro_a, store_id='8100688', token='tok_a',
        )
        intento_b = abrir_intento(centro_b)

        respuesta = llamar_callback(client)

        assert respuesta.status_code == 200
        assert not TiendanubeIntegration.objects.filter(center=centro_b).exists()

        integracion = TiendanubeIntegration.objects.get(center=centro_a)
        assert integracion.token == 'tok_nuevo'

        intento_b.refresh_from_db()
        assert intento_b.esta_abierta

    def test_vincular_no_le_roba_la_tienda_a_otro_centro(self):
        """
        Unitario sobre `vincular`, que es el guard del que también depende el
        comando: el callback resuelve el centro por store id y nunca llega acá
        con uno equivocado, pero `vincular_tiendanube --centro N` sí puede.

        La intención tiene que seguir abierta después del rechazo: consumirla
        dejaría al centro sin poder reintentar con el código ya quemado.
        """
        centro_a, centro_b = hacer_centro('A'), hacer_centro('B')
        TiendanubeIntegration.objects.create(
            center=centro_a, store_id='8100688', token='tok_a',
        )
        intento = abrir_intento(centro_b)

        with pytest.raises(TiendaDeOtroCentro) as exc:
            vincular(centro_b, intercambio(), intento)

        assert 'A' in str(exc.value)
        assert not TiendanubeIntegration.objects.filter(center=centro_b).exists()

        intento.refresh_from_db()
        assert intento.esta_abierta



@pytest.mark.django_db
class TestErroresDelCallback:

    def test_sin_code_no_se_llama_a_tienda_nube(self, client):
        with patch('apps.integraciones.tiendanube_views.exchange_code_for_token') as cambio:
            respuesta = client.get(CALLBACK)

        assert respuesta.status_code == 400
        cambio.assert_not_called()

    def test_un_codigo_vencido_se_explica_en_la_pagina(self, client):
        """
        El código dura 5 minutos y este es el error más frecuente. La página la
        lee una persona, así que el mensaje tiene que decirle qué hacer.
        """
        abrir_intento(hacer_centro())

        with patch('apps.integraciones.tiendanube_views.exchange_code_for_token',
                   side_effect=TiendanubeAuthError('El código venció, volvé a instalar')):
            respuesta = client.get(CALLBACK, {'code': 'vencido'})

        assert respuesta.status_code == 400
        assert 'volvé a instalar' in respuesta.content.decode('utf-8')
        assert not TiendanubeIntegration.objects.exists()

    def test_si_el_intercambio_falla_el_intento_sigue_abierto(self, client):
        """
        Tienda Nube rechaza el código y el centro tiene que poder reintentar
        desde donde estaba. Consumir la intención antes de tener el token lo
        obligaría a volver a empezar de cero.
        """
        centro = hacer_centro()
        intento = abrir_intento(centro)

        with patch('apps.integraciones.tiendanube_views.exchange_code_for_token',
                   side_effect=TiendanubeAuthError('venció')):
            client.get(CALLBACK, {'code': 'vencido'})

        intento.refresh_from_db()
        assert intento.esta_abierta

    def test_si_la_tienda_no_responde_igual_queda_vinculada(self, client):
        """
        El token ya es válido —el intercambio lo devolvió—. Tirarlo por una
        lectura que puede fallar por red obligaría a reinstalar de gusto.
        """
        centro = hacer_centro()
        abrir_intento(centro)

        from apps.integraciones.tiendanube import TiendanubeError
        with patch('apps.integraciones.tiendanube_views.exchange_code_for_token',
                   return_value=intercambio()), \
             patch('apps.integraciones.instalacion.TiendanubeClient.get_store',
                   side_effect=TiendanubeError('sin red')):
            respuesta = client.get(CALLBACK, {'code': 'abc'})

        assert respuesta.status_code == 200
        integracion = TiendanubeIntegration.objects.get(center=centro)
        assert integracion.token == 'tok_nuevo'
        assert integracion.store_name == ''

    def test_el_nombre_de_la_tienda_se_escapa(self, client):
        """
        El nombre lo escribe el comerciante del otro lado y esto se sirve desde
        nuestro dominio. Sin escapar, es un XSS regalado.
        """
        centro = hacer_centro()
        abrir_intento(centro)

        with patch('apps.integraciones.tiendanube_views.exchange_code_for_token',
                   return_value=intercambio()), \
             patch('apps.integraciones.instalacion.TiendanubeClient.get_store',
                   return_value={'name': '<script>alert(1)</script>',
                                 'url_with_protocol': 'https://x.mitiendanube.com'}):
            respuesta = client.get(CALLBACK, {'code': 'abc'})

        cuerpo = respuesta.content.decode('utf-8')
        assert '<script>alert(1)</script>' not in cuerpo
        assert '&lt;script&gt;' in cuerpo


@pytest.mark.django_db
class TestInstalacionDesdeElAdmin:
    """
    El camino que se usa de verdad hoy: el CRM no tiene pantalla de
    integraciones, así que la instalación se arranca desde el admin de Django,
    igual que se carga el token de Conto.
    """

    @pytest.fixture(autouse=True)
    def static_simple(self, settings):
        # El admin sirve estáticos por WhiteNoise con manifest, que exige un
        # collectstatic que ningún test corre.
        settings.STORAGES = {
            'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'
            },
        }

    def _admin_logueado(self, client):
        usuario = Usuario.objects.create_superuser(
            username='jefa', password='x', email='jefa@test.local', rol='ADMIN',
        )
        client.force_login(usuario)
        return usuario

    def test_guardar_una_instalacion_manda_derecho_a_tienda_nube(
        self, client, settings
    ):
        settings.TIENDANUBE_CLIENT_ID = '39429'
        centro = hacer_centro()
        self._admin_logueado(client)

        respuesta = client.post(
            reverse('admin:integraciones_tiendanubeinstallintent_add'),
            {'center': centro.pk},
        )

        assert respuesta.status_code == 302
        assert respuesta['Location'] == 'https://www.tiendanube.com/apps/39429/authorize'

        intento = TiendanubeInstallIntent.objects.get()
        assert intento.center == centro
        assert intento.esta_abierta

    def test_arrancar_dos_veces_no_deja_al_centro_ambiguo_contra_si_mismo(
        self, client, settings
    ):
        """
        Apretar «Guardar» dos veces dejaría dos intentos abiertos, y el callback
        se negaría por ambigüedad contra un solo centro. La segunda cierra la
        primera.
        """
        settings.TIENDANUBE_CLIENT_ID = '39429'
        centro = hacer_centro()
        self._admin_logueado(client)
        url = reverse('admin:integraciones_tiendanubeinstallintent_add')

        client.post(url, {'center': centro.pk})
        client.post(url, {'center': centro.pk})

        abiertos = TiendanubeInstallIntent.objects.filter(
            consumed_at__isnull=True, expires_at__gt=timezone.now()
        )
        assert abiertos.count() == 1

    def test_sin_client_id_no_redirige_a_una_url_rota(self, client, settings):
        """
        Sin el id de la app, la URL de autorización no existe. Mandar igual
        dejaría a la persona en un 404 de Tienda Nube sin saber por qué.
        """
        settings.TIENDANUBE_CLIENT_ID = ''
        centro = hacer_centro()
        self._admin_logueado(client)

        respuesta = client.post(
            reverse('admin:integraciones_tiendanubeinstallintent_add'),
            {'center': centro.pk},
            follow=True,
        )

        assert 'tiendanube.com' not in respuesta.request['PATH_INFO']
        assert 'TIENDANUBE_CLIENT_ID' in respuesta.content.decode('utf-8')

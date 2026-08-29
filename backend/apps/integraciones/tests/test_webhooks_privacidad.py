"""
Tests de los tres webhooks de privacidad que Tienda Nube exige para homologar.

Tres defectos concretos se cuidan acá:

1. **Que cualquiera pueda desactivar una integración.** El endpoint es público
   y `store/redact` mata el token del centro. Lo único que separa a Tienda Nube
   de un desconocido es la firma HMAC, así que se prueba que sin firma, con
   firma mal, y sin secreto configurado, no pasa nada.

2. **Firmar sobre el JSON re-serializado en vez de sobre el cuerpo crudo.** Es
   el error clásico: parsear y volver a volcar cambia espacios y orden de
   claves, y pedidos perfectamente válidos empiezan a rebotar. Rebotar además
   no es gratis — Tienda Nube reintenta hasta 16 veces durante 48 horas.

3. **Borrar de más.** Un `customers/redact` que arrastre la ficha de la clienta
   del CRM, o un `store/redact` que se lleve los `CuponApp` por el CASCADE,
   destruye datos del centro por un pedido de un tercero. Esta app nunca leyó
   clientes de la tienda: no hay nada suyo que borrar.
"""
import hashlib
import hmac
import json

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.empleados.models import CentroEstetica
from apps.integraciones.models import (
    CuponApp,
    TiendanubeIntegration,
    TiendanubePrivacyRequest,
)

SECRETO = 'secreto-de-la-app'

STORE_REDACT = reverse('tiendanube-webhook-store-redact')
CUSTOMERS_REDACT = reverse('tiendanube-webhook-customers-redact')
DATA_REQUEST = reverse('tiendanube-webhook-customers-data-request')


@pytest.fixture
def credenciales(settings):
    settings.TIENDANUBE_CLIENT_SECRET = SECRETO


def hacer_centro(nombre='Ame'):
    return CentroEstetica.objects.create(
        nombre=nombre, telefono='1', email=f'{nombre}@test.local'
    )


def hacer_integracion(centro, store_id='8100688'):
    return TiendanubeIntegration.objects.create(
        center=centro, store_id=store_id, token='tok_vivo',
        scope='read_products,write_coupons', is_active=True,
    )


def firmar(cuerpo, secreto=SECRETO):
    return hmac.new(secreto.encode('utf-8'), cuerpo, hashlib.sha256).hexdigest()


def postear(client, url, payload, firma=None, cuerpo=None):
    """
    Mandar el webhook tal como lo manda Tienda Nube.

    `cuerpo` permite mandar bytes distintos de `json.dumps(payload)`, que es lo
    que hace falta para probar que la firma se valida sobre lo que llegó.
    """
    crudo = cuerpo if cuerpo is not None else json.dumps(payload).encode('utf-8')
    return client.post(
        url,
        data=crudo,
        content_type='application/json',
        HTTP_X_LINKEDSTORE_HMAC_SHA256=firma if firma is not None else firmar(crudo),
    )


@pytest.mark.django_db
class TestFirma:

    def test_sin_firma_no_se_toca_nada(self, client, credenciales):
        integracion = hacer_integracion(hacer_centro())

        respuesta = postear(client, STORE_REDACT, {'store_id': 8100688}, firma='')

        assert respuesta.status_code == 401
        integracion.refresh_from_db()
        assert integracion.token == 'tok_vivo'
        assert integracion.is_active
        assert not TiendanubePrivacyRequest.objects.exists()

    def test_una_firma_de_otro_secreto_se_rechaza(self, client, credenciales):
        integracion = hacer_integracion(hacer_centro())
        cuerpo = json.dumps({'store_id': 8100688}).encode('utf-8')

        respuesta = postear(
            client, STORE_REDACT, None,
            cuerpo=cuerpo, firma=firmar(cuerpo, 'otro-secreto'),
        )

        assert respuesta.status_code == 401
        integracion.refresh_from_db()
        assert integracion.is_active

    def test_sin_secreto_configurado_se_rechaza_en_vez_de_dejar_pasar(
        self, client, settings
    ):
        """
        Falta la variable de entorno: no hay forma de verificar nada. Un
        endpoint que desactiva integraciones no se deja abierto porque falte una
        variable — «no puedo verificar» tiene que ser «no».
        """
        settings.TIENDANUBE_CLIENT_SECRET = ''
        integracion = hacer_integracion(hacer_centro())

        respuesta = postear(client, STORE_REDACT, {'store_id': 8100688},
                            firma='cualquier-cosa')

        assert respuesta.status_code == 401
        integracion.refresh_from_db()
        assert integracion.is_active

    def test_la_firma_se_valida_sobre_el_cuerpo_crudo(self, client, credenciales):
        """
        El mismo objeto con otro espaciado y otro orden de claves: la firma es
        de esos bytes y tiene que valer. Si la validación reconstruyera el JSON,
        esto rebotaría siendo legítimo, y Tienda Nube lo reintentaría 16 veces.
        """
        hacer_integracion(hacer_centro())
        crudo = b'{"store_id"  :  8100688,\n  "extra": "z"}'

        respuesta = postear(client, STORE_REDACT, None, cuerpo=crudo)

        assert respuesta.status_code == 200
        assert TiendanubePrivacyRequest.objects.count() == 1

    def test_un_cuerpo_que_no_es_json_no_rompe(self, client, credenciales):
        respuesta = postear(client, DATA_REQUEST, None, cuerpo=b'esto no es json')

        assert respuesta.status_code == 400
        assert not TiendanubePrivacyRequest.objects.exists()


@pytest.mark.django_db
class TestStoreRedact:

    def test_desinstalar_mata_el_token_y_apaga_la_integracion(self, client, credenciales):
        integracion = hacer_integracion(hacer_centro())

        respuesta = postear(client, STORE_REDACT, {'store_id': 8100688})

        assert respuesta.status_code == 200
        integracion.refresh_from_db()
        assert integracion.token == ''
        assert integracion.scope == ''
        assert not integracion.is_active
        assert not integracion.can_issue_coupons
        assert integracion.uninstalled_at is not None

    def test_no_se_lleva_puestos_los_cupones_emitidos(self, client, credenciales):
        """
        `CuponApp.integration` es CASCADE: borrar la fila de la integración
        borraría qué código se emitió, a qué clienta y cuándo, que es sobre lo
        que se apoya la atribución de ventas de la app (§5.7). Lo que Tienda
        Nube pide borrar es su dato —la credencial—, no nuestra historia.
        """
        centro = hacer_centro()
        integracion = hacer_integracion(centro)
        clienta = Cliente.objects.create(
            centro_estetica=centro, nombre='Ana', apellido='Gómez', telefono='11',
        )
        CuponApp.objects.create(
            integration=integracion, cliente=clienta, code='APP-ABC23456',
            percentage='15.00', tiendanube_coupon_id='67713598',
            expires_at=timezone.now() + timezone.timedelta(hours=1),
        )

        postear(client, STORE_REDACT, {'store_id': 8100688})

        assert TiendanubeIntegration.objects.filter(pk=integracion.pk).exists()
        assert CuponApp.objects.filter(code='APP-ABC23456').exists()

    def test_queda_registrado_y_resuelto_solo(self, client, credenciales):
        hacer_integracion(hacer_centro())

        postear(client, STORE_REDACT, {'store_id': 8100688})

        pedido = TiendanubePrivacyRequest.objects.get()
        assert pedido.event == TiendanubePrivacyRequest.Event.STORE_REDACT
        assert pedido.store_id == '8100688'
        # Este no necesita a nadie: la acción ya se hizo.
        assert pedido.handled_at is not None

    def test_una_tienda_que_no_conocemos_contesta_igual(self, client, credenciales):
        """
        Un 200 igual: no tenemos nada de esa tienda, y contestar cualquier otra
        cosa la haría reintentar durante 48 horas por un pedido ya cumplido.
        """
        respuesta = postear(client, STORE_REDACT, {'store_id': 999999})

        assert respuesta.status_code == 200
        pedido = TiendanubePrivacyRequest.objects.get()
        assert pedido.integration is None
        assert pedido.handled_at is not None


@pytest.mark.django_db
class TestPedidosDeComprador:

    def _payload(self):
        return {
            'store_id': 8100688,
            'customer': {'id': 1, 'email': 'ana@test.local',
                         'phone': '11', 'identification': '123'},
            'orders_to_redact': [213, 3415],
        }

    def test_borrar_datos_de_un_comprador_no_borra_la_ficha_del_crm(
        self, client, credenciales
    ):
        """
        La ficha de la clienta es dato del centro, cargado en esta plataforma:
        no salió de la tienda. Esta app pide leer productos y escribir cupones,
        nunca leyó clientes de Tienda Nube, así que no hay dato suyo para
        borrar. Borrar la ficha sería destruir datos del centro por un pedido
        que Tienda Nube reenvió.
        """
        centro = hacer_centro()
        hacer_integracion(centro)
        clienta = Cliente.objects.create(
            centro_estetica=centro, nombre='Ana', apellido='Gómez',
            telefono='11', email='ana@test.local',
        )

        respuesta = postear(client, CUSTOMERS_REDACT, self._payload())

        assert respuesta.status_code == 200
        assert Cliente.objects.filter(pk=clienta.pk).exists()

    def test_el_pedido_queda_abierto_para_que_lo_conteste_una_persona(
        self, client, credenciales
    ):
        """
        Los dos pedidos de comprador los tiene que contestar alguien: Tienda
        Nube dice que mandarle el informe al centro es responsabilidad de la
        app. Cerrarlos solos los haría indistinguibles de los atendidos.
        """
        hacer_integracion(hacer_centro())

        postear(client, CUSTOMERS_REDACT, self._payload())
        postear(client, DATA_REQUEST, {**self._payload(),
                                       'data_request': {'id': 456}})

        pedidos = TiendanubePrivacyRequest.objects.order_by('event')
        assert [p.event for p in pedidos] == [
            TiendanubePrivacyRequest.Event.CUSTOMERS_DATA_REQUEST,
            TiendanubePrivacyRequest.Event.CUSTOMERS_REDACT,
        ]
        assert all(p.handled_at is None for p in pedidos)

    def test_se_guarda_el_payload_entero(self, client, credenciales):
        """
        Es lo que después le permite a una persona contestar: qué comprador,
        qué órdenes. Sin eso el pedido queda registrado y sin forma de atenderlo.
        """
        hacer_integracion(hacer_centro())

        postear(client, CUSTOMERS_REDACT, self._payload())

        pedido = TiendanubePrivacyRequest.objects.get()
        assert pedido.payload['customer']['email'] == 'ana@test.local'
        assert pedido.payload['orders_to_redact'] == [213, 3415]
        assert pedido.integration is not None


@pytest.mark.django_db
def test_la_firma_en_mayusculas_tambien_vale(client, credenciales):
    """
    `AB` y `ab` son el mismo byte. El ejemplo de Tienda Nube es el `hash_hmac`
    de PHP, que devuelve minúscula, pero rechazar por el caseo sería decirle que
    no a un pedido legítimo — y hacerlo reintentar 16 veces.
    """
    hacer_integracion(hacer_centro())
    cuerpo = json.dumps({'store_id': 8100688}).encode('utf-8')

    respuesta = postear(client, STORE_REDACT, None,
                        cuerpo=cuerpo, firma=firmar(cuerpo).upper())

    assert respuesta.status_code == 200

"""
The whole HTTP surface facing Tienda Nube: the install flow and the webhooks.

Separate from `views.py`, which is the Conto integration. They are different
channels with different audiences — that one answers the CRM, this one answers
a merchant's browser and Tienda Nube's servers — and only the endpoints here
are reachable without a session.
"""
import json
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.renderers import StaticHTMLRenderer
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .instalacion import (
    CentroSinResolver,
    TiendaDeOtroCentro,
    completar_datos_tienda,
    resolver_centro,
    vincular,
)
from .models import TiendanubePrivacyRequest
from .privacidad import procesar
from .tiendanube import (
    TiendanubeError,
    exchange_code_for_token,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)

# El header viene así de Tienda Nube; Django lo normaliza a este nombre en META.
FIRMA_HEADER = 'HTTP_X_LINKEDSTORE_HMAC_SHA256'


class OAuthCallbackView(APIView):
    """
    GET /api/integraciones/tiendanube/oauth/callback/?code=...

    Donde Tienda Nube deja al comerciante después de que autoriza la app. Cambia
    el código por el token y guarda la vinculación.

    Público porque lo abre el navegador del comerciante, sin sesión nuestra. Lo
    que lo hace seguro no es la autenticación sino que el código **dura cinco
    minutos** y solo vale contra nuestro `client_secret`: sin él no hay token, y
    el token no elige a qué centro se guarda (`resolver_centro`).

    Contesta HTML porque lo lee una persona, no un programa.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    # Explícito y no heredado: DRF negocia el contenido antes de entrar acá, así
    # que sin un renderer de HTML declarado, el `Accept` de un navegador
    # dependería de que `BrowsableAPIRenderer` siga estando en los defaults del
    # proyecto. El día que alguien los limite a JSON, esto contestaría 406 y la
    # instalación se rompería sin que nadie toque este archivo.
    renderer_classes = [StaticHTMLRenderer]
    # Cada visita dispara un POST a Tienda Nube. El throttle acota que alguien
    # use este endpoint para hacernos llamar a un tercero en loop.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'tiendanube_oauth'

    def get(self, request):
        code = (request.query_params.get('code') or '').strip()
        if not code:
            return _pagina(
                'Falta el código de instalación',
                'Tienda Nube tenía que redirigir acá con un código y no llegó '
                'ninguno. Volvé a empezar la instalación.',
                ok=False,
                status_code=400,
            )

        try:
            datos = exchange_code_for_token(code)
        except TiendanubeError as exc:
            return _pagina('No se pudo completar la instalación', str(exc),
                           ok=False, status_code=400)

        store_id = str(datos['user_id'])

        try:
            centro, intento = resolver_centro(store_id)
        except CentroSinResolver as exc:
            # El token se descarta a propósito. Guardarlo sin saber de quién es
            # sería dejar una credencial de la tienda de alguien colgando de un
            # centro elegido a dedo; reinstalar cuesta un click.
            logger.warning("Instalación sin centro resoluble (tienda %s)", store_id)
            return _pagina('Falta decir de qué centro es esta tienda', str(exc),
                           ok=False, status_code=409)

        try:
            integracion, creada = vincular(centro, datos, intento)
        except TiendaDeOtroCentro as exc:
            return _pagina('Esa tienda ya es de otro centro', str(exc),
                           ok=False, status_code=409)

        aviso = completar_datos_tienda(integracion)

        detalle = [
            f'Centro: {centro.nombre}',
            f'Tienda: {integracion.store_name or store_id}',
            f'Permisos: {integracion.scope or "s/d"}',
        ]
        if aviso:
            detalle.append(
                f'El token se guardó, pero no se pudo leer la tienda: {aviso}'
            )

        return _pagina(
            'Listo, la tienda quedó vinculada' if creada
            else 'Listo, se actualizó la vinculación',
            'Ya podés cerrar esta pestaña.',
            detalle=detalle,
        )


@method_decorator(csrf_exempt, name='dispatch')
class WebhookPrivacidadView(View):
    """
    Base de los tres webhooks obligatorios de privacidad.

    Cada subclase fija su `event`. Van en URLs separadas porque el panel de
    partners pide una por evento.

    **Vista de Django y no de DRF**, que es la excepción en este proyecto y
    tiene dos motivos concretos:

    - DRF negocia el contenido antes de entrar al método. Un `Accept` que no
      matchee ningún renderer da 406, y para Tienda Nube un 406 no es un no:
      es un fallo, y reintenta hasta 16 veces durante 48 horas.
    - Lo que se firma es el cuerpo crudo, así que el parseo de DRF no aporta
      nada acá.

    Las otras dos reglas de Tienda Nube que se ven en la forma de esto: hay que
    contestar 2xx en **3 segundos**, así que no se llama a nadie por red — solo
    se escribe en la base (`privacidad.py`).
    """
    event = None

    def post(self, request, *args, **kwargs):
        # El cuerpo crudo: volver a serializar el JSON cambiaría los espacios y
        # el orden de las claves, y la firma dejaría de coincidir para pedidos
        # que eran válidos.
        raw = request.body

        if not verify_webhook_signature(raw, request.META.get(FIRMA_HEADER, '')):
            logger.warning("Webhook %s con firma inválida, descartado", self.event)
            return JsonResponse({'detail': 'Firma inválida'}, status=401)

        try:
            payload = json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'detail': 'El cuerpo no es JSON'}, status=400)
        if not isinstance(payload, dict):
            return JsonResponse({'detail': 'El cuerpo no es un objeto JSON'}, status=400)

        pedido = procesar(self.event, payload)
        logger.info(
            "Webhook %s recibido de la tienda %s (pedido %s)",
            self.event, pedido.store_id or 's/d', pedido.pk,
        )
        return JsonResponse({'received': True}, status=200)


class StoreRedactView(WebhookPrivacidadView):
    """POST .../webhooks/store-redact/ — el centro desinstaló la app."""
    event = TiendanubePrivacyRequest.Event.STORE_REDACT


class CustomersRedactView(WebhookPrivacidadView):
    """POST .../webhooks/customers-redact/ — pedido de borrado de un comprador."""
    event = TiendanubePrivacyRequest.Event.CUSTOMERS_REDACT


class CustomersDataRequestView(WebhookPrivacidadView):
    """POST .../webhooks/customers-data-request/ — pedido de datos de un comprador."""
    event = TiendanubePrivacyRequest.Event.CUSTOMERS_DATA_REQUEST


def _pagina(titulo, mensaje, detalle=None, ok=True, status_code=200):
    """
    La página que ve el comerciante al volver de Tienda Nube.

    Todo lo variable pasa por `escape`: el nombre de la tienda y los mensajes de
    error traen texto de un tercero, y esto se sirve desde nuestro dominio.
    """
    color = '#1f7a4d' if ok else '#a3271f'
    filas = ''.join(
        f'<li>{escape(item)}</li>' for item in (detalle or [])
    )
    lista = f'<ul>{filas}</ul>' if filas else ''

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<style>
  body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         background: #faf7f4; color: #2b2b2b; margin: 0;
         display: flex; align-items: center; justify-content: center;
         min-height: 100vh; padding: 24px; }}
  main {{ background: #fff; border-radius: 12px; padding: 32px;
          max-width: 480px; box-shadow: 0 2px 16px rgba(0,0,0,.06); }}
  h1 {{ font-size: 20px; margin: 0 0 12px; color: {color}; }}
  p {{ line-height: 1.5; margin: 0 0 16px; }}
  ul {{ margin: 0; padding-left: 20px; color: #555; font-size: 14px; line-height: 1.7; }}
</style>
</head>
<body>
<main>
  <h1>{escape(titulo)}</h1>
  <p>{escape(mensaje)}</p>
  {lista}
</main>
</body>
</html>"""
    return HttpResponse(html, status=status_code, content_type='text/html; charset=utf-8')

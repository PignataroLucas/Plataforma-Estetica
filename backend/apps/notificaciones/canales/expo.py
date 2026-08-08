"""
Canal de entrega sobre la Expo Push API.

Contrato de https://docs.expo.dev/push-notifications/sending-notifications/ :

- ``/push/send`` acepta hasta **100 mensajes** por request y devuelve un *ticket*
  por mensaje, en el mismo orden. Que el ticket venga ``ok`` significa que Expo lo
  aceptó, no que llegó.
- ``/push/getReceipts`` acepta hasta **1000 ids** y devuelve el veredicto final.
  La doc recomienda consultarlo **15 minutos** después; los recibos se borran a
  las 24 horas.
- El payload total no puede pasar de 4096 bytes.

No usamos ``exponent-server-sdk`` a propósito: son dos endpoints HTTP y el SDK
agregaría una dependencia para envolver lo que ya hace ``requests``, que el
proyecto tiene por la integración con Conto.
"""
import logging

import requests
from django.conf import settings

from .base import MensajeSaliente, Resultado

logger = logging.getLogger(__name__)

URL_ENVIO = 'https://exp.host/--/api/v2/push/send'
URL_RECIBOS = 'https://exp.host/--/api/v2/push/getReceipts'

# Topes del proveedor. No son configurables: los define Expo.
MAX_MENSAJES_POR_REQUEST = 100
MAX_RECIBOS_POR_REQUEST = 1000

TIMEOUT = 30

# Errores de Expo que significan "no le mandes más a este token".
ERRORES_DESTINO_MUERTO = frozenset({'DeviceNotRegistered'})

# Errores que se resuelven solos con el tiempo: conviene reintentar.
ERRORES_REINTENTABLES = frozenset({'MessageRateExceeded'})

# Errores de configuración del proyecto. No se reintentan: hasta que alguien
# arregle las credenciales, reintentar solo gasta requests.
ERRORES_DE_CONFIGURACION = frozenset({'MismatchSenderId', 'InvalidCredentials'})


def _headers():
    cabeceras = {
        'accept': 'application/json',
        'accept-encoding': 'gzip, deflate',
        'content-type': 'application/json',
    }
    # Solo hace falta si el proyecto tiene activada la seguridad de push en Expo.
    token = getattr(settings, 'EXPO_ACCESS_TOKEN', '')
    if token:
        cabeceras['authorization'] = f'Bearer {token}'
    return cabeceras


def _lotes(secuencia, tamano):
    for inicio in range(0, len(secuencia), tamano):
        yield secuencia[inicio:inicio + tamano]


def _a_payload(mensaje: MensajeSaliente) -> dict:
    return {
        'to': mensaje.destino,
        'title': mensaje.titulo,
        'body': mensaje.cuerpo,
        'data': mensaje.datos,
        'sound': 'default',
        'channelId': mensaje.canal_android,
        'priority': 'high',
    }


def _resultado_de_ticket(destino: str, ticket: dict) -> Resultado:
    if ticket.get('status') == 'ok':
        return Resultado(destino=destino, ok=True, ticket_id=ticket.get('id', ''))

    codigo = (ticket.get('details') or {}).get('error', '')
    detalle = ticket.get('message') or codigo or 'Expo rechazó el mensaje'
    if codigo in ERRORES_DE_CONFIGURACION:
        # Esto no se arregla reintentando: lo tiene que ver una persona.
        logger.error("Credenciales de push mal configuradas (%s): %s", codigo, detalle)
    return Resultado(
        destino=destino,
        ok=False,
        error=detalle[:300],
        destino_muerto=codigo in ERRORES_DESTINO_MUERTO,
        reintentable=codigo in ERRORES_REINTENTABLES,
    )


def enviar(mensajes: list[MensajeSaliente]) -> list[Resultado]:
    """
    Entrega una lista de mensajes y devuelve un resultado por mensaje.

    Nunca levanta excepción: un corte de red o un 500 de Expo se traducen a
    resultados reintentables, porque quien llama está adentro de un ciclo de cola
    y tiene que poder seguir con el resto.
    """
    if not mensajes:
        return []

    resultados: list[Resultado] = []

    for lote in _lotes(mensajes, MAX_MENSAJES_POR_REQUEST):
        payload = [_a_payload(m) for m in lote]
        try:
            respuesta = requests.post(
                URL_ENVIO, json=payload, headers=_headers(), timeout=TIMEOUT
            )
            respuesta.raise_for_status()
            tickets = respuesta.json().get('data') or []
        except requests.RequestException as exc:
            # Expo no contestó o contestó mal: todo el lote queda para reintentar.
            logger.warning("Falló el envío push a Expo: %s", exc)
            resultados.extend(
                Resultado(destino=m.destino, ok=False, error=str(exc)[:300], reintentable=True)
                for m in lote
            )
            continue
        except ValueError as exc:
            logger.error("Expo devolvió una respuesta ilegible: %s", exc)
            resultados.extend(
                Resultado(destino=m.destino, ok=False, error='Respuesta ilegible de Expo',
                          reintentable=True)
                for m in lote
            )
            continue

        if len(tickets) != len(lote):
            # No debería pasar; si pasa, no podemos aparear ticket con mensaje.
            logger.error(
                "Expo devolvió %d tickets para %d mensajes", len(tickets), len(lote)
            )
            resultados.extend(
                Resultado(destino=m.destino, ok=False,
                          error='Expo devolvió una cantidad de tickets inesperada',
                          reintentable=True)
                for m in lote
            )
            continue

        resultados.extend(
            _resultado_de_ticket(mensaje.destino, ticket)
            for mensaje, ticket in zip(lote, tickets)
        )

    return resultados


def consultar_recibos(ticket_ids: list[str]) -> dict[str, Resultado]:
    """
    Pide el veredicto final de tickets ya aceptados.

    Devuelve un diccionario por ticket. Los tickets que Expo todavía no resolvió
    simplemente no aparecen: quien llama los deja como están y vuelve a
    preguntar en la corrida siguiente.
    """
    if not ticket_ids:
        return {}

    recibos: dict[str, Resultado] = {}

    for lote in _lotes(ticket_ids, MAX_RECIBOS_POR_REQUEST):
        try:
            respuesta = requests.post(
                URL_RECIBOS, json={'ids': lote}, headers=_headers(), timeout=TIMEOUT
            )
            respuesta.raise_for_status()
            datos = respuesta.json().get('data') or {}
        except (requests.RequestException, ValueError) as exc:
            logger.warning("No se pudieron consultar recibos de push: %s", exc)
            continue

        for ticket_id, recibo in datos.items():
            # El destino no viaja en el recibo; lo resuelve quien llama por ticket.
            recibos[ticket_id] = _resultado_de_ticket('', recibo)

    return recibos

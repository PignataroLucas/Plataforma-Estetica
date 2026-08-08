"""
Canales de entrega.

Un canal sabe una sola cosa: cómo poner un mensaje en un dispositivo. No conoce
eventos, plantillas ni preferencias --de eso se encarga ``despacho.py``--, así que
sumar email o volver a levantar WhatsApp es escribir otro módulo acá y elegirlo
desde ``NOTIFICACIONES_CANAL``, sin tocar el resto.

Canales disponibles:

- ``expo``    — el real, contra la Expo Push API.
- ``consola`` — simulación: imprime en vez de enviar. Deja correr toda la tubería
  sin cuenta de Expo ni teléfono.
"""
from django.conf import settings

from . import consola, expo
from .base import MensajeSaliente, Resultado

__all__ = ['MensajeSaliente', 'Resultado', 'activo', 'nombre_activo']

CANALES = {
    'expo': expo,
    'consola': consola,
}

POR_DEFECTO = 'expo'


def nombre_activo() -> str:
    return getattr(settings, 'NOTIFICACIONES_CANAL', POR_DEFECTO)


def activo():
    """
    Módulo de canal según la configuración.

    Se resuelve en cada llamada y no al importar, para que ``override_settings``
    funcione en los tests y para poder cambiar de canal por variable de entorno
    sin reconstruir la imagen.
    """
    nombre = nombre_activo()
    try:
        return CANALES[nombre]
    except KeyError:
        raise ValueError(
            f"NOTIFICACIONES_CANAL='{nombre}' no existe. "
            f"Opciones: {', '.join(sorted(CANALES))}."
        ) from None

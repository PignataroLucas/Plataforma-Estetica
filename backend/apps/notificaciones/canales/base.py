"""Contrato que cumple cualquier canal de entrega."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MensajeSaliente:
    """Un mensaje listo para entregar a un destino concreto."""
    destino: str                      # token, teléfono o dirección, según el canal
    titulo: str
    cuerpo: str
    datos: dict[str, Any] = field(default_factory=dict)
    canal_android: str = 'default'    # notification channel de Android


@dataclass(frozen=True)
class Resultado:
    """
    Qué pasó con un mensaje.

    ``ok`` es "el proveedor lo aceptó", no "llegó al teléfono": para eso está el
    recibo, que se consulta más tarde.

    ``destino_muerto`` es la señal de que hay que dejar de mandarle a ese destino
    (app desinstalada, token revocado). Es la que mantiene la tabla de
    dispositivos limpia sola.
    """
    destino: str
    ok: bool
    ticket_id: str = ''
    error: str = ''
    destino_muerto: bool = False
    reintentable: bool = False

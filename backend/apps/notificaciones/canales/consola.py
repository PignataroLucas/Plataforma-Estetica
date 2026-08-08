"""
Canal de simulación: imprime en vez de enviar.

Sirve para correr la tubería entera --disparadores, cola, recibos, estados,
idempotencia-- sin cuenta de Expo, sin development build y sin un teléfono real.
Todo lo que en producción termina en un aparato acá termina en el log, y los
``Aviso`` y ``EnvioPush`` quedan guardados igual que siempre.

Se activa con ``NOTIFICACIONES_CANAL=consola``.

Lo que este canal NO prueba es lo que pasa del lado del teléfono (permisos,
banner, tap, deep link). Para eso está el simulador de notificaciones locales de
la app, que sí anda en Expo Go.
"""
import logging
import uuid

from .base import MensajeSaliente, Resultado

logger = logging.getLogger(__name__)

# Se replican del canal real para que la cola se comporte igual en simulación.
MAX_MENSAJES_POR_REQUEST = 100
MAX_RECIBOS_POR_REQUEST = 1000


def _dibujar(mensaje: MensajeSaliente) -> str:
    """Una notificación como se vería en la pantalla, para revisar la redacción."""
    ruta = mensaje.datos.get('ruta', '—')
    ancho = max(len(mensaje.titulo), len(mensaje.cuerpo), len(mensaje.destino), 40)
    borde = '─' * (ancho + 2)
    return (
        f"\n┌{borde}┐\n"
        f"│ {mensaje.titulo.ljust(ancho)} │\n"
        f"│ {mensaje.cuerpo.ljust(ancho)} │\n"
        f"├{borde}┤\n"
        f"│ {('→ ' + ruta).ljust(ancho)} │\n"
        f"│ {('canal: ' + mensaje.canal_android).ljust(ancho)} │\n"
        f"│ {mensaje.destino[:ancho].ljust(ancho)} │\n"
        f"└{borde}┘"
    )


def enviar(mensajes: list[MensajeSaliente]) -> list[Resultado]:
    """Acepta todo y devuelve tickets falsos, respetando el orden de entrada."""
    resultados = []
    for mensaje in mensajes:
        logger.info("[push simulado]%s", _dibujar(mensaje))
        resultados.append(
            Resultado(destino=mensaje.destino, ok=True, ticket_id=f'simulado-{uuid.uuid4().hex[:12]}')
        )
    return resultados


def consultar_recibos(ticket_ids: list[str]) -> dict[str, Resultado]:
    """En simulación todo se da por entregado."""
    return {ticket: Resultado(destino='', ok=True) for ticket in ticket_ids}

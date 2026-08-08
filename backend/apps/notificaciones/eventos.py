"""
Catálogo de eventos que pueden generar un aviso.

Cada evento se declara acá una sola vez, con su categoría, su texto por defecto y
la pantalla de la app a la que lleva el tap. **Sumar un aviso nuevo al sistema es
sumar una entrada a ``EVENTOS``**: no hay que tocar el despacho, la cola ni el
canal de envío. Esa es toda la modularidad del módulo.

Este archivo no importa modelos a propósito: es datos puros, se puede leer sin
base y los tests lo usan directo.
"""
import logging
from dataclasses import dataclass, field

from django.db import models

logger = logging.getLogger(__name__)


class Categoria(models.TextChoices):
    """
    Unidad de opt-out. La clienta no apaga eventos sueltos sino categorías: es
    lo que se puede explicar en una pantalla de preferencias sin marearla.
    """
    TURNOS = 'TURNOS', 'Turnos'
    RUTINA = 'RUTINA', 'Mi rutina'
    NOVEDADES = 'NOVEDADES', 'Novedades'
    PROMOCIONES = 'PROMOCIONES', 'Promociones'


@dataclass(frozen=True)
class Evento:
    """
    Definición de un tipo de aviso.

    ``transaccional`` marca los avisos que son consecuencia directa de algo que
    la clienta hizo o que le hicieron a su turno. Esos se mandan aunque tenga la
    categoría apagada: apagar "Turnos" silencia los recordatorios, no el aviso de
    que le cancelaron el turno de mañana.

    ``variables`` es solo documentación: qué claves espera el texto. Sirve para
    la pantalla del CRM donde el centro edita la plantilla.

    ``ejemplo`` son valores de muestra para esas variables. Con eso el texto se
    puede previsualizar sin datos reales --``manage.py simular_notificacion
    --listar``-- que es como se revisa la redacción con el centro antes de que
    exista un teléfono al que mandarle nada.
    """
    clave: str
    categoria: str
    titulo: str
    cuerpo: str
    ruta: str = ''
    transaccional: bool = False
    variables: tuple[str, ...] = field(default_factory=tuple)
    ejemplo: dict = field(default_factory=dict)


# --------------------------------------------------------------------- #
# Claves de evento. Se usan como string en la base, así que NO se renombran
# una vez que hay avisos guardados; se agregan nuevas y se deprecan viejas.
# --------------------------------------------------------------------- #

TURNO_CONFIRMADO = 'turno_confirmado'
TURNO_RECORDATORIO_24H = 'turno_recordatorio_24h'
TURNO_RECORDATORIO_2H = 'turno_recordatorio_2h'
TURNO_CANCELADO = 'turno_cancelado'
RUTINA_ACTUALIZADA = 'rutina_actualizada'
RUTINA_RECORDATORIO = 'rutina_recordatorio'
CUMPLEANOS = 'cumpleanos'
OFERTA_NUEVA = 'oferta_nueva'
FECHAS_NUEVAS = 'fechas_nuevas'


EVENTOS: dict[str, Evento] = {
    e.clave: e
    for e in [
        # ---------------- Turnos ----------------
        Evento(
            clave=TURNO_CONFIRMADO,
            categoria=Categoria.TURNOS,
            titulo='Turno confirmado',
            cuerpo='{servicio} el {fecha} a las {hora}. Te esperamos.',
            ruta='/turnos',
            transaccional=True,
            variables=('servicio', 'fecha', 'hora', 'centro'),
            ejemplo={'servicio': 'Limpieza facial', 'fecha': '12 de agosto',
                     'hora': '15:00', 'centro': 'AME'},
        ),
        Evento(
            clave=TURNO_RECORDATORIO_24H,
            categoria=Categoria.TURNOS,
            titulo='Mañana tenés turno',
            cuerpo='{servicio} a las {hora}. Si no llegás, avisanos con tiempo.',
            ruta='/turnos',
            variables=('servicio', 'fecha', 'hora', 'centro'),
            ejemplo={'servicio': 'Limpieza facial', 'fecha': '12 de agosto',
                     'hora': '15:00', 'centro': 'AME'},
        ),
        Evento(
            clave=TURNO_RECORDATORIO_2H,
            categoria=Categoria.TURNOS,
            titulo='Tu turno es en un rato',
            cuerpo='{servicio} a las {hora}.',
            ruta='/turnos',
            variables=('servicio', 'hora', 'centro'),
            ejemplo={'servicio': 'Limpieza facial', 'hora': '15:00', 'centro': 'AME'},
        ),
        Evento(
            clave=TURNO_CANCELADO,
            categoria=Categoria.TURNOS,
            titulo='Turno cancelado',
            cuerpo='Se canceló tu turno de {servicio} del {fecha}. Escribinos y lo reprogramamos.',
            ruta='/turnos',
            transaccional=True,
            variables=('servicio', 'fecha', 'hora', 'centro'),
            ejemplo={'servicio': 'Limpieza facial', 'fecha': '12 de agosto',
                     'hora': '15:00', 'centro': 'AME'},
        ),

        # ---------------- Rutina ----------------
        Evento(
            clave=RUTINA_ACTUALIZADA,
            categoria=Categoria.RUTINA,
            titulo='Actualizamos tu rutina',
            cuerpo='Tenés cambios en tu rutina de cuidado. Entrá a verlos.',
            ruta='/mi-rutina',
            variables=('centro',),
            ejemplo={'centro': 'AME'},
        ),
        Evento(
            clave=RUTINA_RECORDATORIO,
            categoria=Categoria.RUTINA,
            titulo='Tu rutina de la {momento}',
            cuerpo='Son unos minutos. Entrá y mirá los pasos.',
            ruta='/mi-rutina',
            variables=('momento',),
            ejemplo={'momento': 'noche'},
        ),

        # ---------------- Novedades ----------------
        Evento(
            clave=CUMPLEANOS,
            categoria=Categoria.NOVEDADES,
            titulo='¡Feliz cumple, {nombre}!',
            cuerpo='Que lo pases hermoso. Te esperamos en {centro}.',
            ruta='/promos',
            variables=('nombre', 'centro'),
            ejemplo={'nombre': 'Sofía', 'centro': 'AME'},
        ),
        Evento(
            clave=FECHAS_NUEVAS,
            categoria=Categoria.NOVEDADES,
            titulo='Se abrieron fechas',
            cuerpo='{servicio} ya tiene fechas para reservar.',
            ruta='/servicio/{servicio_id}',
            variables=('servicio', 'servicio_id'),
            ejemplo={'servicio': 'Depilación láser', 'servicio_id': 7},
        ),

        # ---------------- Promociones ----------------
        Evento(
            clave=OFERTA_NUEVA,
            categoria=Categoria.PROMOCIONES,
            titulo='Nueva promo en {centro}',
            cuerpo='{oferta}. Hasta el {vence}.',
            ruta='/promos',
            variables=('centro', 'oferta', 'vence'),
            ejemplo={'centro': 'AME', 'oferta': '2x1 en faciales', 'vence': '30 de agosto'},
        ),
    ]
}


def obtener(clave: str) -> Evento:
    """Devuelve la definición de un evento. Explota fuerte si la clave no existe."""
    try:
        return EVENTOS[clave]
    except KeyError:
        raise ValueError(
            f"Evento de notificación desconocido: '{clave}'. "
            f"Los definidos son: {', '.join(sorted(EVENTOS))}."
        ) from None


def claves() -> list[str]:
    """Claves de todos los eventos, para choices de formularios y del admin."""
    return sorted(EVENTOS)


def opciones() -> list[tuple[str, str]]:
    """``choices`` con etiqueta legible, para el CRM y el admin."""
    return [(clave, EVENTOS[clave].titulo) for clave in claves()]


class _ContextoTolerante(dict):
    """
    Un dato que falta no puede romper un envío ni dejar un ``{servicio}`` crudo en
    el teléfono de la clienta: se reemplaza por vacío y queda registrado.
    """

    def __missing__(self, clave):
        logger.warning("Falta la variable '%s' al renderizar una notificación", clave)
        return ''


def renderizar(plantilla: str, contexto: dict) -> str:
    """
    Reemplaza las variables ``{asi}`` de una plantilla.

    Tolera variables faltantes y plantillas mal escritas: el centro edita estos
    textos desde el CRM y una llave sin cerrar no puede tumbar el envío.
    """
    try:
        return plantilla.format_map(_ContextoTolerante(contexto)).strip()
    except (ValueError, IndexError):
        logger.exception("Plantilla de notificación mal formada: %r", plantilla)
        return plantilla

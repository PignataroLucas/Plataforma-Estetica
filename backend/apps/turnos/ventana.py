"""
La ventana de respuesta del centro y el vencimiento de los pedidos de turno.

Todo lo de acá es **función pura**: recibe datetimes y configuración, devuelve
datetimes. No toca la base ni importa modelos. Es a propósito —es la lógica más
fácil de arruinar de todo el circuito y la que más barato sale testear— y por eso
vive en su propio módulo en vez de adentro de ``services.py``.

**Qué resuelve.** Un pedido de turno vence si el centro no lo contesta, pero el
plazo no puede correr de madrugada: un pedido hecho a las 23:10 con tres horas de
plazo vencería a las 02:10, y a la mañana el centro encontraría un rechazo
automático de algo que habría aceptado. Eso es peor que no tener vencimiento,
porque le dice "no" a una clienta cuando la respuesta era "sí".

Entonces el reloj corre **solo dentro de la franja de respuesta** de la sucursal
—no el horario del local, sino la franja en la que alguien mira los pedidos— y
todo lo demás se deriva de ahí (APROBACION_TURNOS_SPEC.md §2.2 y §2.3).

**La franja es de todos los días**, incluidos los que el local no abre. Es
deliberado: lo que se modela es cuándo alguien mira el teléfono, no cuándo se
atiende. Si algún día hace falta distinguirlo, la sucursal necesita sus propios
días laborales —hoy los días están en la ficha de cada profesional, que es otra
cosa— y este módulo recibiría un predicado más.
"""
from datetime import datetime, timedelta

from django.utils import timezone

# Tope de seguridad del bucle. Con los valores reales (3 horas de plazo sobre una
# franja de 11) alcanza con una o dos vueltas; esto solo ataja una configuración
# absurda, como 500 horas de plazo sobre una franja de una hora.
MAX_DIAS = 370


class VentanaInvalida(ValueError):
    """La franja de respuesta no es una franja: el plazo nunca avanzaría."""


def _franja_del_dia(fecha, hora_inicio, hora_fin):
    """(apertura, cierre) de la franja de ese día, como datetimes aware."""
    return (
        timezone.make_aware(datetime.combine(fecha, hora_inicio)),
        timezone.make_aware(datetime.combine(fecha, hora_fin)),
    )


def _apertura_del_dia_siguiente(cursor, hora_inicio, hora_fin):
    """
    Apertura de la franja del día siguiente al de ``cursor``.

    Se arma desde la fecha y no sumándole un día al datetime: sumar 24 horas a un
    instante aware es correcto solo donde no hay cambio de hora, y atar la lógica
    a esa suposición es gratis de evitar.
    """
    apertura, _ = _franja_del_dia(cursor.date() + timedelta(days=1), hora_inicio, hora_fin)
    return apertura


def sumar_horas_de_respuesta(desde, horas, *, hora_inicio, hora_fin):
    """
    Avanza ``horas`` desde ``desde``, contando solo el tiempo dentro de la franja.

    Si ``desde`` cae fuera de la franja, el reloj arranca en la próxima apertura:
    un pedido de las 23:10 con la franja 09:00–20:00 empieza a correr a las 09:00
    del día siguiente.

    Devuelve un datetime aware. ``horas`` en 0 devuelve el primer instante
    *dentro* de la franja, que no es lo mismo que ``desde`` —y es lo correcto:
    el plazo no empezó a correr todavía.
    """
    if hora_inicio >= hora_fin:
        raise VentanaInvalida(
            f'La franja de respuesta {hora_inicio}–{hora_fin} está invertida o vacía'
        )

    restante = timedelta(hours=horas)
    # La aritmética va en hora local: la franja está expresada en horas de pared
    # y la base guarda UTC. Sin esto, 09:00 se convierte en otra cosa.
    cursor = timezone.localtime(desde)

    for _ in range(MAX_DIAS):
        apertura, cierre = _franja_del_dia(cursor.date(), hora_inicio, hora_fin)

        if cursor < apertura:
            cursor = apertura
        elif cursor >= cierre:
            # Ya pasó la franja de hoy: se sigue mañana.
            cursor = _apertura_del_dia_siguiente(cursor, hora_inicio, hora_fin)
            continue

        disponible = cierre - cursor
        if disponible >= restante:
            return cursor + restante

        restante -= disponible
        cursor = _apertura_del_dia_siguiente(cursor, hora_inicio, hora_fin)

    raise VentanaInvalida(
        f'No se pudo agotar un plazo de {horas} h en {MAX_DIAS} días de franja '
        f'{hora_inicio}–{hora_fin}: revisá la configuración de la sucursal'
    )


def vencimiento_de(inicio_turno, *, pedido_en, sucursal):
    """
    Hasta cuándo el centro puede resolver este pedido.

    Lo que pase primero entre agotar el plazo de respuesta y que empiece el turno.
    El segundo término importa: un pedido para mañana a las 10 no puede seguir
    abierto a las 11.

    El resultado se **guarda** en ``Turno.vence_en`` y no se recalcula. Así el
    barrido queda en una consulta indexada, el CRM puede mostrar cuánto falta sin
    repetir esta lógica, y si mañana cambia la política los pedidos vivos
    conservan el plazo con el que nacieron, que es lo justo.
    """
    natural = sumar_horas_de_respuesta(
        pedido_en,
        sucursal.horas_para_responder,
        hora_inicio=sucursal.respuesta_hora_inicio,
        hora_fin=sucursal.respuesta_hora_fin,
    )
    return min(natural, inicio_turno)


def hay_ventana_suficiente(inicio_turno, *, ahora, sucursal):
    """
    ¿Le queda tiempo al centro para contestar antes de que empiece el turno?

    Es el predicado que filtra los horarios que la app ofrece. La antelación
    mínima de reserva es por día de calendario, así que el margen real puede ser
    de ocho horas —reserva a las 23:59, turno al día siguiente a las 08:00— y hay
    combinaciones sin salida: pedido el lunes 23:30 para el martes 08:00, con la
    franja abriendo a las 09:00. No existe ningún momento en que alguien pudiera
    aprobarlo.

    **Se deriva del vencimiento en vez de ser una constante aparte.** Si mañana el
    plazo baja a una hora, lo que se ofrece se ajusta solo; dos reglas
    independientes se contradicen tarde o temprano.
    """
    plazo_completo = sumar_horas_de_respuesta(
        ahora,
        sucursal.horas_para_responder,
        hora_inicio=sucursal.respuesta_hora_inicio,
        hora_fin=sucursal.respuesta_hora_fin,
    )
    # Alcanza si el plazo entero entra antes de que empiece el turno. Ojo que no
    # se puede usar `vencimiento_de`, que ya viene acotado por `inicio_turno` y
    # haría que la comparación diera siempre verdadera.
    return plazo_completo <= inicio_turno

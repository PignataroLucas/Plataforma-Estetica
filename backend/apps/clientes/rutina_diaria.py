"""
Rutina diaria: qué pasos tocan hoy, el check-in de la clienta y su constancia.

Tres ideas sostienen todo lo de acá:

1. **"Hoy" es el día local del centro** (``timezone.localdate``). La clienta no
   elige la fecha: marca lo que hizo hoy.
2. **Un momento está cumplido** cuando se tildaron todos los pasos que tocaban
   ese día. Se asienta en ``RutinaDiaCumplido`` en el instante en que pasa, así
   la historia no cambia cuando el staff edita la rutina.
3. **La racha perdona**: un día cuenta si se cumplió la rutina de la mañana o la
   de la noche. Exigir las dos hace que una sola noche cansada borre semanas, y
   una racha que castiga es una razón para dejar de abrir la app.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import RutinaDiaCumplido, RutinaItem, RutinaPasoHecho

MOMENTOS = (RutinaItem.Momento.DIURNA, RutinaItem.Momento.NOCTURNA)

# Hasta dónde mira hacia atrás el cálculo de la racha. Más allá de esto la
# racha se informa topeada: nadie distingue 365 de 400 días seguidos.
DIAS_MAXIMOS_DE_RACHA = 365


def clave_recordatorio(rutina_id, fecha, momento) -> str:
    """
    Clave del recordatorio push de un momento de un día.

    Vive acá y no en notificaciones porque el check-in la necesita para
    descartar el recordatorio cuando la clienta ya cumplió.
    """
    return f"rutina:{rutina_id}:{fecha.isoformat()}:{momento.lower()}"


def rutina_activa(cliente):
    """La rutina que ve la clienta en la app: la activa más reciente."""
    return (
        cliente.rutinas_cuidado
        .filter(activa=True)
        .prefetch_related('items__producto')
        .order_by('-creado_en')
        .first()
    )


def pasos_del_dia(rutina, fecha, momento=None) -> list[RutinaItem]:
    """
    Los pasos que tocan en ``fecha``, en orden.

    Usa ``rutina.items.all()`` para aprovechar un ``prefetch_related`` del
    llamador: el disparador de recordatorios recorre todas las rutinas activas.
    """
    return [
        item for item in rutina.items.all()
        if item.va_el(fecha) and (momento is None or item.momento == momento)
    ]


def _actualizar_cumplimiento(rutina, fecha, momento) -> bool:
    """Asienta o borra el cumplimiento de un momento. Devuelve si quedó cumplido."""
    pasos = pasos_del_dia(rutina, fecha, momento)
    hechos = set(
        RutinaPasoHecho.objects
        .filter(item__in=pasos, fecha=fecha)
        .values_list('item_id', flat=True)
    )
    cumplido = bool(pasos) and all(p.id in hechos for p in pasos)

    if cumplido:
        RutinaDiaCumplido.objects.get_or_create(
            cliente_id=rutina.cliente_id, fecha=fecha, momento=momento,
        )
    else:
        RutinaDiaCumplido.objects.filter(
            cliente_id=rutina.cliente_id, fecha=fecha, momento=momento,
        ).delete()
    return cumplido


class PasoInvalido(Exception):
    """El paso no se puede marcar hoy (no es de la rutina activa o no toca)."""


def marcar_paso(rutina, item, hecho: bool, fecha=None) -> bool:
    """
    Tilda o destilda un paso. Es idempotente en las dos direcciones.

    Cuando el tilde completa el momento, descarta el recordatorio de ese momento
    si todavía no salió: avisarle "hacé tu rutina" a quien ya la hizo es la forma
    más rápida de que apague las notificaciones. Si después destilda, el próximo
    barrido lo vuelve a encolar solo.

    Devuelve si el momento del paso quedó cumplido.
    """
    from apps.notificaciones.despacho import descartar_pendientes

    fecha = fecha or timezone.localdate()
    if item.rutina_id != rutina.id:
        raise PasoInvalido('Ese paso no es de tu rutina.')
    if not item.va_el(fecha):
        raise PasoInvalido('Ese paso no toca hoy.')

    with transaction.atomic():
        if hecho:
            RutinaPasoHecho.objects.get_or_create(item=item, fecha=fecha)
        else:
            RutinaPasoHecho.objects.filter(item=item, fecha=fecha).delete()
        cumplido = _actualizar_cumplimiento(rutina, fecha, item.momento)

    if cumplido:
        descartar_pendientes(clave_prefijo=clave_recordatorio(rutina.id, fecha, item.momento))
    return cumplido


def racha(cliente, hoy=None) -> int:
    """
    Días seguidos con al menos un momento cumplido.

    Si hoy todavía no cumplió, la racha cuenta hasta ayer: a las 8 de la mañana
    nadie perdió nada todavía.
    """
    hoy = hoy or timezone.localdate()
    fechas = set(
        cliente.rutina_cumplimientos
        .filter(fecha__gt=hoy - timedelta(days=DIAS_MAXIMOS_DE_RACHA + 1), fecha__lte=hoy)
        .values_list('fecha', flat=True)
    )
    dia = hoy if hoy in fechas else hoy - timedelta(days=1)
    total = 0
    while dia in fechas and total < DIAS_MAXIMOS_DE_RACHA:
        total += 1
        dia -= timedelta(days=1)
    return total


def dias_cumplidos(cliente, hasta, dias: int) -> list[bool]:
    """Para cada uno de los ``dias`` que terminan en ``hasta``, si cumplió."""
    desde = hasta - timedelta(days=dias - 1)
    fechas = set(
        cliente.rutina_cumplimientos
        .filter(fecha__gte=desde, fecha__lte=hasta)
        .values_list('fecha', flat=True)
    )
    return [(desde + timedelta(days=i)) in fechas for i in range(dias)]


def estado_del_dia(rutina, fecha=None) -> dict:
    """
    Todo lo que la app necesita para pintar "tu rutina de hoy".

    La semana va de lunes a domingo, la semana calendario que la clienta tiene
    en la cabeza, y no los últimos siete días.
    """
    fecha = fecha or timezone.localdate()
    cliente = rutina.cliente

    pasos = pasos_del_dia(rutina, fecha)
    hechos = set(
        RutinaPasoHecho.objects
        .filter(item__in=pasos, fecha=fecha)
        .values_list('item_id', flat=True)
    )

    momentos = {}
    for momento in MOMENTOS:
        del_momento = [p for p in pasos if p.momento == momento]
        hechos_momento = sum(1 for p in del_momento if p.id in hechos)
        momentos[momento] = {
            'total': len(del_momento),
            'hechos': hechos_momento,
            'cumplido': bool(del_momento) and hechos_momento == len(del_momento),
        }

    lunes = fecha - timedelta(days=fecha.weekday())
    cumplidos = dias_cumplidos(cliente, lunes + timedelta(days=6), 7)

    return {
        'fecha': fecha.isoformat(),
        'pasos_hechos': sorted(hechos),
        'momentos': momentos,
        'semana': [
            {'fecha': (lunes + timedelta(days=i)).isoformat(), 'cumplido': cumplidos[i]}
            for i in range(7)
        ],
        'racha': racha(cliente, fecha),
    }


def constancia(cliente, hoy=None, dias: int = 7) -> dict:
    """Resumen para el CRM: cuántos de los últimos ``dias`` hizo la rutina."""
    hoy = hoy or timezone.localdate()
    ultimos = dias_cumplidos(cliente, hoy, dias)
    return {
        'dias': dias,
        'cumplidos': sum(ultimos),
        'ultimos': ultimos,
        'racha': racha(cliente, hoy),
    }

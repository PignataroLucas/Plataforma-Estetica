"""
Disparadores programados.

Lo que no nace de una acción del staff sino del paso del tiempo: recordatorios de
turno, cumpleaños, rutina. Cada función es idempotente y se puede correr todas las
veces que haga falta --la clave del aviso se encarga de que no salga dos veces--,
así que el cron puede solaparse, atrasarse o repetirse sin consecuencias.

Los recordatorios **no se mandan al detectarlos**: se encolan con
``programado_para`` en el momento exacto. Por eso el barrido mira una ventana
amplia hacia adelante y no una franja angosta alrededor del ahora: si el cron no
corre por tres horas, el aviso ya estaba encolado y sale igual.
"""
import logging
from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import formats, timezone

from apps.clientes import rutina_diaria
from apps.clientes.models import (
    Cliente,
    RutinaCuidado,
    RutinaDiaCumplido,
    RutinaItem,
    VinculacionCliente,
)
from apps.turnos.models import Turno

from . import cola, eventos
from .despacho import crear_aviso_para_cliente

logger = logging.getLogger(__name__)

# Hasta dónde mira hacia adelante el barrido de turnos. Tiene que superar con
# holgura la anticipación del recordatorio más lejano (24 h).
DIAS_DE_PROGRAMACION = 3

# Cuánto atraso se tolera antes de descartar un recordatorio. Sin esto, un turno
# reservado para dentro de 5 horas dispararía un "mañana tenés turno".
TOLERANCIA_ATRASO = timedelta(minutes=30)

# Los recordatorios de turno, con su anticipación.
RECORDATORIOS_DE_TURNO = (
    (eventos.TURNO_RECORDATORIO_24H, timedelta(hours=24)),
    (eventos.TURNO_RECORDATORIO_2H, timedelta(hours=2)),
)

ESTADOS_QUE_RECIBEN_RECORDATORIO = (Turno.Estado.PENDIENTE, Turno.Estado.CONFIRMADO)

# Hora local en la que sale el saludo de cumpleaños.
HORA_CUMPLEANOS = 10

# Hora local de los recordatorios de rutina, por momento.
HORAS_RUTINA = {
    RutinaItem.Momento.DIURNA: 9,
    RutinaItem.Momento.NOCTURNA: 21,
}

# Cuánto atraso se tolera antes de dar por perdido un recordatorio de rutina.
TOLERANCIA_ATRASO_RUTINA = timedelta(hours=2)

# Cómo se nombra cada momento en el texto del aviso ("tu rutina de la ...").
NOMBRE_DEL_MOMENTO = {
    RutinaItem.Momento.DIURNA: 'mañana',
    RutinaItem.Momento.NOCTURNA: 'noche',
}


def contexto_de_turno(turno) -> dict:
    """Variables disponibles en las plantillas de los eventos de turno."""
    inicio = timezone.localtime(turno.fecha_hora_inicio)
    return {
        'servicio': turno.servicio.nombre if turno.servicio else 'tu turno',
        'fecha': formats.date_format(inicio, r'j \d\e F'),
        'hora': formats.time_format(inicio, 'H:i'),
        'centro': turno.sucursal.centro_estetica.nombre,
        'profesional': turno.profesional.get_full_name() if turno.profesional else '',
    }


def clave_de_turno(turno_id, evento) -> str:
    """Prefijo estable, para poder cancelar de una todos los avisos de un turno."""
    return f"turno:{turno_id}:{evento}"


def programar_recordatorios_de_turnos(ahora=None) -> dict:
    """
    Encola los recordatorios de todos los turnos próximos.

    Se apoya solo en la base: no depende de que ninguna señal haya corrido al
    reservar, así que también cubre los turnos cargados a mano en el CRM y los
    que existían antes de que este sistema estuviera.
    """
    ahora = ahora or timezone.now()
    hasta = ahora + timedelta(days=DIAS_DE_PROGRAMACION)

    # Solo turnos de clientas con cuenta de app: al resto no hay cómo avisarles.
    tiene_cuenta = VinculacionCliente.objects.filter(cliente_id=OuterRef('cliente_id'))
    turnos = (
        Turno.objects
        .filter(
            fecha_hora_inicio__gt=ahora,
            fecha_hora_inicio__lte=hasta,
            estado__in=ESTADOS_QUE_RECIBEN_RECORDATORIO,
        )
        .annotate(notificable=Exists(tiene_cuenta))
        .filter(notificable=True)
        .select_related('cliente', 'servicio', 'sucursal__centro_estetica', 'profesional')
    )

    creados = 0
    for turno in turnos:
        contexto = contexto_de_turno(turno)
        for evento, anticipacion in RECORDATORIOS_DE_TURNO:
            momento = turno.fecha_hora_inicio - anticipacion
            if momento < ahora - TOLERANCIA_ATRASO:
                continue  # se reservó demasiado sobre la hora para este recordatorio
            avisos = crear_aviso_para_cliente(
                evento=evento,
                cliente=turno.cliente,
                contexto=contexto,
                clave=clave_de_turno(turno.id, evento),
                programado_para=max(momento, ahora),
                datos_extra={'turnoId': turno.id},
            )
            creados += len(avisos)

    return {'recordatorios_encolados': creados}


def saludar_cumpleanos(ahora=None) -> dict:
    """
    Encola el saludo de las clientas que cumplen años hoy.

    La clave lleva el año, así que se puede correr veinte veces en el día y sale
    una sola, pero vuelve a salir el año que viene.
    """
    ahora = ahora or timezone.now()
    hoy = timezone.localdate(ahora)

    momento = timezone.make_aware(datetime.combine(hoy, time(HORA_CUMPLEANOS)))

    tiene_cuenta = VinculacionCliente.objects.filter(cliente_id=OuterRef('id'))
    cumpleaneras = (
        Cliente.objects
        .filter(
            fecha_nacimiento__month=hoy.month,
            fecha_nacimiento__day=hoy.day,
            activo=True,
        )
        .annotate(notificable=Exists(tiene_cuenta))
        .filter(notificable=True)
        .select_related('centro_estetica')
    )

    creados = 0
    for cliente in cumpleaneras:
        avisos = crear_aviso_para_cliente(
            evento=eventos.CUMPLEANOS,
            cliente=cliente,
            contexto={
                'nombre': cliente.nombre,
                'centro': cliente.centro_estetica.nombre,
            },
            clave=f"cumple:{cliente.id}:{hoy.year}",
            programado_para=max(momento, ahora),
        )
        creados += len(avisos)

    return {'cumpleanos_encolados': creados}


def _resumen_de_pasos(pasos) -> str:
    """
    El cuerpo del recordatorio: qué tiene que hacer, en una línea.

    Lo que no va todos los días es lo que la clienta se olvida, así que si hoy
    toca algo así se nombra primero. Si no, con pocos pasos alcanza con
    listarlos; con muchos, la cuenta.
    """
    nombres = [p.etiqueta for p in pasos if p.etiqueta]
    cantidad = 'Es un solo paso.' if len(pasos) == 1 else f'Son {len(pasos)} pasos.'

    especiales = [p.etiqueta.lower() for p in pasos if p.dias and p.etiqueta]
    if especiales:
        verbo = 'toca' if len(especiales) == 1 else 'tocan'
        return f'Hoy {verbo} {_enumerar(especiales)}. {cantidad}'
    if 0 < len(nombres) <= 3 and len(nombres) == len(pasos):
        lista = _enumerar([nombres[0]] + [n.lower() for n in nombres[1:]])
        return f'{lista}. {cantidad if len(pasos) == 1 else "Son unos minutos."}'
    return f'{cantidad} Unos minutos para tu piel.'


def _enumerar(palabras) -> str:
    if len(palabras) == 1:
        return palabras[0]
    return f"{', '.join(palabras[:-1])} y {palabras[-1]}"


def contexto_de_rutina(momento, pasos) -> dict:
    """Variables disponibles en la plantilla del recordatorio de rutina."""
    return {
        'momento': NOMBRE_DEL_MOMENTO[momento],
        'pasos': len(pasos),
        'resumen': _resumen_de_pasos(pasos),
    }


def recordar_rutina(ahora=None) -> dict:
    """
    Encola los recordatorios de rutina de hoy: mañana (9 h) y noche (21 h).

    Solo a quien tiene pasos para ese momento **hoy** (un paso de martes y
    viernes no hace sonar el teléfono un lunes) y todavía no lo cumplió. Cuando
    la clienta completa el momento, el check-in descarta el aviso pendiente; el
    filtro de acá evita que el barrido siguiente lo vuelva a encolar.

    Si el barrido corre con mucho atraso, el recordatorio de ese momento se
    pierde: "tu rutina de la mañana" a las tres de la tarde es ruido.
    """
    if not getattr(settings, 'NOTIFICACIONES_RUTINA_DIARIA', False):
        return {'rutina_encolados': 0, 'apagado': True}

    ahora = ahora or timezone.now()
    hoy = timezone.localdate(ahora)

    momentos = []
    for momento, hora in HORAS_RUTINA.items():
        cuando = timezone.make_aware(datetime.combine(hoy, time(hora)))
        if ahora <= cuando + TOLERANCIA_ATRASO_RUTINA:
            momentos.append((momento, cuando))
    if not momentos:
        return {'rutina_encolados': 0}

    tiene_cuenta = VinculacionCliente.objects.filter(cliente_id=OuterRef('cliente_id'))
    rutinas = (
        RutinaCuidado.objects
        .filter(activa=True)
        .annotate(notificable=Exists(tiene_cuenta))
        .filter(notificable=True)
        .select_related('cliente__centro_estetica')
        .prefetch_related('items__producto')
        .order_by('cliente_id', '-creado_en')
    )
    cumplidos = set(
        RutinaDiaCumplido.objects
        .filter(fecha=hoy)
        .values_list('cliente_id', 'momento')
    )

    creados = 0
    vistos = set()
    for rutina in rutinas:
        # Con más de una rutina activa, la app muestra la más nueva: esa manda.
        if rutina.cliente_id in vistos:
            continue
        vistos.add(rutina.cliente_id)

        for momento, cuando in momentos:
            if (rutina.cliente_id, momento) in cumplidos:
                continue
            pasos = rutina_diaria.pasos_del_dia(rutina, hoy, momento)
            if not pasos:
                continue
            avisos = crear_aviso_para_cliente(
                evento=eventos.RUTINA_RECORDATORIO,
                cliente=rutina.cliente,
                contexto=contexto_de_rutina(momento, pasos),
                clave=rutina_diaria.clave_recordatorio(rutina.id, hoy, momento),
                programado_para=max(cuando, ahora),
            )
            creados += len(avisos)

    return {'rutina_encolados': creados}


def enviar_recordatorio_de_prueba(rutina, momento) -> list:
    """
    Manda ya mismo el recordatorio de un momento, para mostrarlo en una demo.

    Va sin clave, así que se puede repetir. Si hoy no toca ningún paso de ese
    momento, usa todos los del momento: el objetivo es ver cómo llega el aviso.
    Respeta las preferencias: si la clienta apagó "Mi rutina", no se crea.
    """
    hoy = timezone.localdate()
    pasos = rutina_diaria.pasos_del_dia(rutina, hoy, momento) or [
        item for item in rutina.items.all() if item.momento == momento
    ]
    avisos = crear_aviso_para_cliente(
        evento=eventos.RUTINA_RECORDATORIO,
        cliente=rutina.cliente,
        contexto=contexto_de_rutina(momento, pasos),
    )
    if avisos:
        transaction.on_commit(lambda: cola.despachar_ahora())
    return avisos


def _vencer_pedidos_de_turno(ahora=None) -> dict:
    """
    Cierra los pedidos de turno a los que se les pasó el plazo.

    Vive en `apps.turnos.services` y se llama desde acá porque el barrido es el
    único proceso programado que hay: sumar otro cron para esto sería sumar otro
    servicio que mantener.

    Va **antes** del envío de avisos internos: así un pedido que vence en esta
    misma corrida alcanza a disparar su aviso y sale en la misma pasada.
    """
    from apps.turnos.services import vencer_pedidos

    return vencer_pedidos(ahora)


def _avisar_pedidos_por_vencer(ahora=None) -> dict:
    """
    Segundo aviso a los pedidos a los que les queda poco.

    Va **antes** de `_vencer_pedidos_de_turno` en la lista: de otro modo, un
    pedido que entra a la ventana de aviso y vence en la misma corrida se
    cerraría sin que el centro llegara a enterarse de que estaba por vencer.
    """
    from .internas import avisar_los_que_vencen

    return avisar_los_que_vencen(ahora)


def _enviar_avisos_internos(ahora=None) -> dict:
    """
    Despacha los mails que esperan en la bandeja del centro.

    No programa nada: los avisos los escriben la señal de turnos al reservar y el
    disparador de los que están por vencer. Acá solo salen. Va último en la lista
    para que lo que se haya creado en esta misma corrida salga en esta misma
    corrida y no en la siguiente.
    """
    from .internas import enviar_pendientes

    return enviar_pendientes()


DISPARADORES = (
    programar_recordatorios_de_turnos,
    saludar_cumpleanos,
    recordar_rutina,
    # El orden importa: avisar que está por vencer, después vencer lo que se
    # pasó, y recién entonces mandar todo lo que quedó escrito en esta corrida.
    _avisar_pedidos_por_vencer,
    _vencer_pedidos_de_turno,
    _enviar_avisos_internos,
)


def correr_todos(ahora=None) -> dict:
    """
    Corre todos los disparadores y junta los resúmenes.

    Que uno falle no puede impedir que corran los demás: un error en cumpleaños
    no debería dejar sin recordatorio a los turnos de mañana.
    """
    resumen = {}
    for disparador in DISPARADORES:
        try:
            resumen.update(disparador(ahora))
        except Exception:
            logger.exception("Falló el disparador %s", disparador.__name__)
            resumen[f'{disparador.__name__}_error'] = True
    return resumen

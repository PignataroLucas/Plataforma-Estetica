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
from django.db.models import Exists, OuterRef
from django.utils import formats, timezone

from apps.clientes.models import Cliente, RutinaCuidado, RutinaItem, VinculacionCliente
from apps.turnos.models import Turno

from . import eventos
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

# Hora local del recordatorio de rutina nocturna.
HORA_RUTINA = 21


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


def recordar_rutina(ahora=None) -> dict:
    """
    Encola el recordatorio diario de rutina nocturna.

    Apagado por defecto (``NOTIFICACIONES_RUTINA_DIARIA``). Es un push por día:
    conviene encenderlo recién cuando exista frecuencia por paso, porque hoy la
    rutina no distingue lo que va todas las noches de lo que va dos veces por
    semana y el recordatorio sería impreciso para la mitad de los pasos.
    """
    if not getattr(settings, 'NOTIFICACIONES_RUTINA_DIARIA', False):
        return {'rutina_encolados': 0, 'apagado': True}

    ahora = ahora or timezone.now()
    hoy = timezone.localdate(ahora)
    momento = timezone.make_aware(datetime.combine(hoy, time(HORA_RUTINA)))

    con_pasos = RutinaItem.objects.filter(
        rutina_id=OuterRef('id'), momento=RutinaItem.Momento.NOCTURNA
    )
    rutinas = (
        RutinaCuidado.objects
        .filter(activa=True)
        .annotate(tiene_pasos=Exists(con_pasos))
        .filter(tiene_pasos=True)
        .select_related('cliente__centro_estetica')
    )

    creados = 0
    for rutina in rutinas:
        avisos = crear_aviso_para_cliente(
            evento=eventos.RUTINA_RECORDATORIO,
            cliente=rutina.cliente,
            contexto={'momento': 'noche'},
            clave=f"rutina:{rutina.id}:{hoy.isoformat()}:nocturna",
            programado_para=max(momento, ahora),
        )
        creados += len(avisos)

    return {'rutina_encolados': creados}


DISPARADORES = (
    programar_recordatorios_de_turnos,
    saludar_cumpleanos,
    recordar_rutina,
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

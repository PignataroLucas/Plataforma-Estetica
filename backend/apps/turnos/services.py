"""
Disponibilidad y reserva de turnos.

Fuente única de verdad del cálculo de slots libres y de la prevención de
doble-reserva, compartida entre el CRM del staff (``apps.empleados.views``) y la
app del cliente (``apps.client_api``). Antes esta lógica vivía inline en el
endpoint ``UsuarioViewSet.horarios_disponibles``; se extrajo acá para que la app
reserve con exactamente las mismas reglas y no haya dos implementaciones que
puedan divergir.
"""
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from apps.empleados.models import Usuario

from .models import Turno

# Horario asumido cuando el profesional no tiene agenda cargada en su ficha.
HORARIO_DEFAULT_INICIO = time(8, 0)
HORARIO_DEFAULT_FIN = time(22, 0)

# Antelación mínima para que el cliente pueda cancelar desde la app.
HORAS_MINIMAS_CANCELACION = 24

# Ventana que el cliente puede consultar y reservar desde la app.
DIAS_MAXIMOS_A_FUTURO = 90

# ---------------------------------------------------------------- #
# Política de reserva desde la app (NO aplica al staff en el CRM)
# ---------------------------------------------------------------- #

# Días en los que el cliente puede reservar por defecto. La precedencia va de más
# específico a más general: ``fechas_reserva`` del servicio (fechas puntuales) →
# ``dias_reserva`` del servicio (patrón semanal propio) → estos días generales.
# Cada nivel REEMPLAZA al siguiente, no lo complementa. Cuando haga falta que cada
# centro elija sus días, esto pasa a ser un campo de CentroEstetica y se lee acá.
DIAS_RESERVA_APP = ['lunes', 'martes', 'miercoles', 'jueves']

# Anticipación mínima en días: 1 = desde mañana (no se reserva el mismo día,
# porque el centro necesita preparar/pedir el servicio).
DIAS_MINIMOS_ANTICIPACION = 1

# Cuántas fechas concretas se le ofrecen al cliente en el calendario de la app.
FECHAS_A_OFRECER = 30

# Estados que ocupan la agenda (los demás liberan el horario).
ESTADOS_QUE_OCUPAN = [Turno.Estado.PENDIENTE, Turno.Estado.CONFIRMADO]

DIAS_SEMANA = {
    0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves',
    4: 'viernes', 5: 'sabado', 6: 'domingo',
}

# Los nombres internos van sin tilde (así están guardados en dias_laborales y
# dias_reserva); estos son para los mensajes que ve el cliente.
DIAS_DISPLAY = {
    'lunes': 'lunes', 'martes': 'martes', 'miercoles': 'miércoles',
    'jueves': 'jueves', 'viernes': 'viernes', 'sabado': 'sábados',
    'domingo': 'domingos',
}


class TurnoNoDisponible(Exception):
    """El horario pedido no se puede reservar (ocupado, fuera de agenda o pasado)."""


def nombre_dia(fecha):
    return DIAS_SEMANA[fecha.weekday()]


def dias_reserva_de(servicio):
    """
    Días de la semana en que el cliente puede reservar este servicio desde la app.

    Los días propios del servicio REEMPLAZAN a los generales (no se suman). Ojo:
    si el servicio tiene ``fechas_reserva``, esto no se usa — ver ``modo_reserva_de``.
    """
    return list(servicio.dias_reserva) if servicio.dias_reserva else list(DIAS_RESERVA_APP)


def fechas_reserva_de(servicio):
    """
    Fechas puntuales del servicio, parseadas, ordenadas y sin repetidos.

    Las entradas inválidas se descartan en silencio: es un JSONField y una fecha
    mal cargada no puede dejar el calendario de la app sin responder.
    """
    fechas = set()
    for valor in servicio.fechas_reserva or []:
        try:
            fechas.add(datetime.strptime(str(valor), '%Y-%m-%d').date())
        except ValueError:
            continue
    return sorted(fechas)


def modo_reserva_de(servicio):
    """
    Cómo se define la disponibilidad de este servicio:

    - ``'fechas'``: fechas puntuales cargadas a mano (la máquina viene el viernes 20).
    - ``'dias'``: patrón semanal (propio del servicio o el general de la app).

    Las fechas puntuales GANAN sobre los días de la semana. Es a propósito: quien
    carga "viernes 20" quiere ese día y ninguno más, y si se sumaran a los días
    generales el servicio quedaría reservable de lunes a jueves sin haberlo pedido.
    """
    return 'fechas' if fechas_reserva_de(servicio) else 'dias'


def primera_fecha_reservable(hoy=None):
    """Primer día que el cliente puede elegir en la app (por defecto, mañana)."""
    hoy = hoy or timezone.localdate()
    return hoy + timedelta(days=DIAS_MINIMOS_ANTICIPACION)


def fechas_reservables(servicio, *, hoy=None, limite=FECHAS_A_OFRECER):
    """
    Fechas concretas que el cliente puede elegir para este servicio.

    Resuelve acá las dos configuraciones (fechas puntuales o días de la semana)
    para que la app pinte el calendario con una lista lista para usar en vez de
    reimplementar la regla. Siempre dentro de la ventana reservable: nunca antes
    de ``primera_fecha_reservable`` ni más allá de ``DIAS_MAXIMOS_A_FUTURO``.
    """
    if not servicio.reservable_por_cliente:
        return []

    hoy = hoy or timezone.localdate()
    desde = primera_fecha_reservable(hoy)
    hasta = hoy + timedelta(days=DIAS_MAXIMOS_A_FUTURO)

    puntuales = fechas_reserva_de(servicio)
    if puntuales:
        return [fecha for fecha in puntuales if desde <= fecha <= hasta][:limite]

    dias = dias_reserva_de(servicio)
    fechas = []
    cursor = desde
    while cursor <= hasta and len(fechas) < limite:
        if nombre_dia(cursor) in dias:
            fechas.append(cursor)
        cursor += timedelta(days=1)
    return fechas


def motivo_fecha_no_reservable(servicio, fecha, *, hoy=None):
    """
    Devuelve el motivo por el que el cliente NO puede reservar ese día, o None
    si la fecha es válida. Se usa igual para filtrar el calendario y para
    rechazar el POST de reserva, así la app y el backend nunca discrepan.
    """
    if not servicio.reservable_por_cliente:
        return 'Este tratamiento se reserva directamente con el centro'

    if fecha < primera_fecha_reservable(hoy):
        return 'Los turnos se reservan con al menos un día de anticipación'

    # Fechas puntuales primero: cuando existen, reemplazan al patrón semanal.
    puntuales = fechas_reserva_de(servicio)
    if puntuales:
        if fecha not in puntuales:
            return 'Este tratamiento tiene fechas puntuales: elegí una de las disponibles'
        return None

    dias = dias_reserva_de(servicio)
    if nombre_dia(fecha) not in dias:
        return f'Este tratamiento se reserva los {_listado_de_dias(dias)}'

    return None


def _listado_de_dias(dias):
    """['lunes','martes','jueves'] → 'lunes, martes y jueves' (con tildes)."""
    nombres = [DIAS_DISPLAY.get(d, d) for d in DIAS_SEMANA.values() if d in dias]
    if len(nombres) <= 1:
        return ''.join(nombres)
    return f"{', '.join(nombres[:-1])} y {nombres[-1]}"


def horario_laboral(profesional):
    """Ventana laboral del profesional, con fallback si no tiene horario cargado."""
    if not profesional.horario_inicio or not profesional.horario_fin:
        return HORARIO_DEFAULT_INICIO, HORARIO_DEFAULT_FIN
    return profesional.horario_inicio, profesional.horario_fin


def trabaja_el_dia(profesional, fecha):
    """Sin días laborales cargados se asume que trabaja todos los días."""
    if not profesional.dias_laborales:
        return True
    return nombre_dia(fecha) in profesional.dias_laborales


def profesionales_de(sucursal):
    """Profesionales que pueden tomar turnos en la sucursal."""
    return Usuario.objects.filter(sucursal=sucursal, activo=True).order_by('id')


def _ventana_del_dia(profesional, fecha):
    """(inicio, fin) de la jornada como datetimes aware."""
    inicio_laboral, fin_laboral = horario_laboral(profesional)
    return (
        timezone.make_aware(datetime.combine(fecha, inicio_laboral)),
        timezone.make_aware(datetime.combine(fecha, fin_laboral)),
    )


def _turnos_que_ocupan(profesional, desde, hasta, excluir_turno_id=None):
    """Turnos del profesional que se solapan con la ventana [desde, hasta)."""
    qs = Turno.objects.filter(
        profesional=profesional,
        estado__in=ESTADOS_QUE_OCUPAN,
        fecha_hora_inicio__lt=hasta,
        fecha_hora_fin__gt=desde,
    )
    if excluir_turno_id:
        qs = qs.exclude(pk=excluir_turno_id)
    return qs.order_by('fecha_hora_inicio')


def calcular_slots(profesional, servicio, fecha, *, no_antes_de=None, excluir_turno_id=None):
    """
    Horarios libres del profesional para un servicio en una fecha.

    Recorre la jornada con la granularidad del profesional (``intervalo_minutos``)
    y descarta los solapamientos con turnos que ocupan la agenda. Cuando choca con
    un turno salta directo al fin de ese turno (en vez de avanzar de a un intervalo),
    para ofrecer el horario apenas se libera.

    ``no_antes_de``: descarta slots anteriores a ese instante (para no ofrecer
    horarios de hoy que ya pasaron).

    Devuelve una lista de ``{'inicio': datetime, 'fin': datetime}`` (aware).
    """
    if not trabaja_el_dia(profesional, fecha):
        return []

    apertura, cierre = _ventana_del_dia(profesional, fecha)
    duracion = timedelta(minutes=servicio.duracion_minutos)
    intervalo = timedelta(minutes=profesional.intervalo_minutos or 30)

    ocupados = list(_turnos_que_ocupan(profesional, apertura, cierre, excluir_turno_id))

    slots = []
    cursor = apertura
    while cursor + duracion <= cierre:
        slot_fin = cursor + duracion

        conflicto = next(
            (t for t in ocupados if cursor < t.fecha_hora_fin and slot_fin > t.fecha_hora_inicio),
            None,
        )
        if conflicto:
            # El fin del turno en conflicto siempre es > cursor, así que avanza sí o sí.
            # localtime() es necesario: la DB devuelve el datetime en UTC y el cursor
            # tiene que seguir en hora local para que los slots se formateen bien.
            cursor = timezone.localtime(conflicto.fecha_hora_fin)
            continue

        if no_antes_de is None or cursor >= no_antes_de:
            slots.append({'inicio': cursor, 'fin': slot_fin})
        cursor += intervalo

    return slots


def slots_agregados(servicio, fecha, *, no_antes_de=None):
    """
    Horarios libres del servicio combinando a todos los profesionales de la sucursal.

    Cada horario aparece UNA sola vez, con el primer profesional libre — así el
    cliente elige hora y el sistema resuelve con quién, sin exponer la agenda de
    cada empleado.
    """
    por_horario = {}
    for profesional in profesionales_de(servicio.sucursal):
        for slot in calcular_slots(profesional, servicio, fecha, no_antes_de=no_antes_de):
            por_horario.setdefault(slot['inicio'], {**slot, 'profesional': profesional})

    return [por_horario[inicio] for inicio in sorted(por_horario)]


def _entra_en_la_jornada(profesional, inicio, fin):
    """El turno completo tiene que caer dentro del horario laboral del profesional."""
    fecha = timezone.localtime(inicio).date()
    if not trabaja_el_dia(profesional, fecha):
        return False
    apertura, cierre = _ventana_del_dia(profesional, fecha)
    return apertura <= inicio and fin <= cierre


def reservar_turno(*, cliente, servicio, inicio, profesional=None, notas='',
                   estado=Turno.Estado.PENDIENTE, creado_por=None):
    """
    Crea un turno verificando la disponibilidad dentro de la transacción.

    Sin ``profesional`` asigna el primero libre de la sucursal. Toma un lock sobre
    la fila del profesional antes de re-chequear los conflictos: eso serializa dos
    reservas concurrentes del mismo profesional (el chequeo previo por sí solo no
    alcanza, porque ninguna de las dos ve el turno que la otra está insertando).

    Lanza ``TurnoNoDisponible`` si el horario ya no se puede tomar.
    """
    if inicio <= timezone.now():
        raise TurnoNoDisponible('Ese horario ya pasó')

    fin = inicio + timedelta(minutes=servicio.duracion_minutos)
    candidatos = [profesional] if profesional else list(profesionales_de(servicio.sucursal))
    if not candidatos:
        raise TurnoNoDisponible('El centro no tiene profesionales disponibles')

    with transaction.atomic():
        for candidato in candidatos:
            if not _entra_en_la_jornada(candidato, inicio, fin):
                continue

            # Lock de la fila del profesional: serializa reservas simultáneas.
            Usuario.objects.select_for_update().get(pk=candidato.pk)

            if _turnos_que_ocupan(candidato, inicio, fin).exists():
                continue

            return Turno.objects.create(
                sucursal=servicio.sucursal,
                cliente=cliente,
                servicio=servicio,
                profesional=candidato,
                fecha_hora_inicio=inicio,
                fecha_hora_fin=fin,
                estado=estado,
                monto_total=servicio.precio,
                notas=notas,
                creado_por=creado_por,
            )

    raise TurnoNoDisponible('Ese horario ya no está disponible')


def puede_cancelar(turno, *, ahora=None):
    """El cliente puede cancelar un turno vigente con la antelación mínima."""
    if turno.estado not in ESTADOS_QUE_OCUPAN:
        return False
    ahora = ahora or timezone.now()
    return turno.fecha_hora_inicio - ahora >= timedelta(hours=HORAS_MINIMAS_CANCELACION)

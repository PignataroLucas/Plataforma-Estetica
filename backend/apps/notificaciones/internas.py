"""
Avisos para el centro: crearlos y entregarlos por mail.

Es el gemelo de ``despacho.py`` + ``cola.py``, pero del lado del staff. Misma
disciplina —escribir la fila es todo el trabajo, el envío es de un barrido
aparte— y por los mismos motivos: el request de la clienta que reserva no espera
a SES, y un mail que no sale se reintenta en la corrida siguiente en vez de
perderse.

**Por qué no reusa el outbox de avisos:** ``cola.py`` resuelve destinatarios
buscando dispositivos push de una ``UsuarioCliente``. Acá el destinatario es una
dirección de mail de la sucursal. Ver ``NotificacionInterna`` y
APROBACION_TURNOS_SPEC.md §2.5.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone, formats

from .correo import CorreoNoEnviado, enviar_correo
from .models import NotificacionInterna

logger = logging.getLogger(__name__)

# Cuántas veces se reintenta un mail antes de darlo por perdido. Tres corridas
# del barrido alcanzan para cubrir un pico de SES; más que eso es insistir con
# algo que está roto de verdad.
MAX_INTENTOS = 3

LOTE_POR_CORRIDA = 50

# Cuánto antes del vencimiento sale el segundo aviso. Media hora es suficiente
# para que alguien salga de un box y conteste, y poco como para que no se
# confunda con el aviso original.
MARGEN_DE_AVISO = timedelta(minutes=30)


def clave_de_pedido(turno_id, tipo) -> str:
    """Clave de idempotencia. Mismo formato que la de los avisos a clientas."""
    return f"turno:{turno_id}:{tipo.lower()}"


def url_del_turno(turno_id) -> str:
    """
    Link al turno en el CRM, o cadena vacía si no hay URL configurada.

    Sin ``CRM_URL`` el mail sale igual, solo que sin el link. Es deliberado:
    preferimos un aviso sin link antes que ningún aviso, y la variable se puede
    cargar después sin tocar código.
    """
    base = (getattr(settings, 'CRM_URL', '') or '').rstrip('/')
    return f'{base}/turnos?turno={turno_id}' if base else ''


def _cuerpo_del_pedido(turno, *, por_vencer=False) -> str:
    """
    El mail que recibe el centro.

    Texto plano a propósito: lo va a leer alguien en el teléfono, entre clienta y
    clienta, y lo único que tiene que resolver es *si acepta o no*. Todo lo que
    necesita para decidir va arriba; el link, abajo.
    """
    inicio = timezone.localtime(turno.fecha_hora_inicio)
    cliente = turno.cliente

    # Los formatos se resuelven antes de las f-strings: el de fecha lleva `\d\e`
    # para que Django escriba el "de" literal, y en Python 3.11 una f-string no
    # admite backslashes en la expresión.
    dia = formats.date_format(inicio, r'l j \d\e F')
    hora = formats.time_format(inicio, 'H:i')
    telefono = cliente.telefono or '—'

    lineas = [
        'Pidieron un turno desde la app.' if not por_vencer
        else 'Este pedido está por vencer y todavía no lo resolviste.',
        '',
        f'Clienta:     {cliente.nombre_completo}',
        f'Teléfono:    {telefono}',
        f'Tratamiento: {turno.servicio.nombre}',
        f'Cuándo:      {dia} a las {hora}',
    ]

    # Por el nombre y no por el objeto: un profesional sin nombre ni apellido
    # cargados dejaba la línea en blanco, que lee como un dato que falta en vez
    # de como un dato que no aplica.
    profesional = turno.profesional.get_full_name().strip() if turno.profesional else ''
    if profesional:
        lineas.append(f'Profesional: {profesional}')
    if turno.notas:
        lineas.append(f'Nota:        {turno.notas}')

    if turno.vence_en:
        vence = timezone.localtime(turno.vence_en)
        vence_hora = formats.time_format(vence, 'H:i')
        vence_dia = formats.date_format(vence, r'j \d\e F')
        lineas += [
            '',
            f'Podés responder hasta las {vence_hora} del {vence_dia}. '
            'Si no, el horario se libera solo y la clienta puede elegir otro.',
        ]

    url = url_del_turno(turno.id)
    if url:
        lineas += ['', f'Aceptarlo o rechazarlo: {url}']

    return '\n'.join(lineas)


def avisar_pedido_de_turno(turno, *, por_vencer=False):
    """
    Deja el aviso listo para que el barrido lo mande. No envía nada.

    Devuelve la ``NotificacionInterna`` creada, o ``None`` si ya existía una con
    la misma clave —que es lo normal cuando el disparador corre de nuevo, no un
    error.

    El destinatario se **congela** en la fila: si mañana cambia el mail de la
    sucursal, esta fila sigue diciendo a dónde se mandó.
    """
    tipo = (
        NotificacionInterna.Tipo.TURNO_POR_VENCER if por_vencer
        else NotificacionInterna.Tipo.TURNO_SOLICITADO
    )
    inicio = timezone.localtime(turno.fecha_hora_inicio)
    destino = turno.sucursal.destino_avisos

    datos = {
        'turnoId': turno.id,
        'url': url_del_turno(turno.id),
        'venceEn': turno.vence_en.isoformat() if turno.vence_en else None,
    }

    try:
        with transaction.atomic():
            return NotificacionInterna.objects.create(
                sucursal=turno.sucursal,
                tipo=tipo,
                turno=turno,
                titulo=(
                    f'{turno.cliente.nombre_completo} pidió turno para '
                    f'{turno.servicio.nombre}'
                ),
                cuerpo=_cuerpo_del_pedido(turno, por_vencer=por_vencer),
                datos=datos,
                clave=clave_de_pedido(turno.id, tipo),
                email_destino=destino,
                # Sin destinatario no se intenta ni una vez: el barrido no tiene
                # a dónde mandarlo y reintentar no lo va a arreglar. Queda
                # visible en el admin para que se note que falta configurarlo.
                email_estado=(
                    NotificacionInterna.EstadoEntrega.PENDIENTE if destino
                    else NotificacionInterna.EstadoEntrega.SIN_DESTINO
                ),
            )
    except IntegrityError:
        # La clave ya existía: el aviso está hecho.
        return None


def avisar_los_que_vencen(ahora=None) -> dict:
    """
    Segundo aviso para los pedidos a punto de vencer.

    Es lo que hace que un plazo de tres horas sea un plazo y no una trampa. Sin
    esto, el centro se entera de que se le pasó cuando ya se le pasó; con esto,
    tiene media hora para atajarlo.

    La clave de idempotencia es la que hace que el aviso salga **una sola vez**
    por pedido, aunque el barrido corra cada cinco minutos durante esa media
    hora.
    """
    from apps.turnos.models import Turno

    ahora = ahora or timezone.now()
    por_vencer = Turno.objects.filter(
        estado=Turno.Estado.PENDIENTE,
        vence_en__isnull=False,
        vence_en__gt=ahora,
        vence_en__lte=ahora + MARGEN_DE_AVISO,
    ).select_related('cliente', 'servicio', 'sucursal', 'profesional')

    avisados = 0
    for turno in por_vencer:
        if avisar_pedido_de_turno(turno, por_vencer=True) is not None:
            avisados += 1

    return {'pedidos_por_vencer_avisados': avisados}


def enviar_ahora(limite=5) -> dict:
    """
    Intento de envío inmediato, para que el mail no espere al próximo cron.

    Esos minutos salen del plazo que el centro tiene para responder, así que
    conviene no regalarlos. **No reemplaza al barrido**: si SES no contesta, la
    fila queda pendiente y sale en la corrida siguiente.

    Se traga cualquier excepción a propósito: que el mail no salga en el acto no
    puede hacer fallar la reserva de la clienta, que ya está hecha.

    Va llamado desde ``transaction.on_commit``: antes del commit la fila todavía
    no existe para otra conexión.
    """
    try:
        return enviar_pendientes(limite=limite)
    except Exception:
        logger.exception('Falló el envío inmediato; queda para el barrido')
        return {}


def enviar_pendientes(limite=LOTE_POR_CORRIDA) -> dict:
    """
    Manda los avisos internos que esperan salir.

    No propaga: un mail que falla se anota y se reintenta en la corrida que
    viene. Que SES tosa no puede frenar al resto de la tanda ni al barrido.
    """
    pendientes = NotificacionInterna.objects.filter(
        email_estado=NotificacionInterna.EstadoEntrega.PENDIENTE,
        email_intentos__lt=MAX_INTENTOS,
    ).select_related('sucursal')[:limite]

    enviados = fallidos = 0

    for aviso in pendientes:
        aviso.email_intentos += 1
        try:
            enviar_correo(
                destinatario=aviso.email_destino,
                asunto=aviso.titulo,
                cuerpo=aviso.cuerpo,
            )
        except CorreoNoEnviado as exc:
            aviso.email_error = str(exc)[:1000]
            # Se marca FALLIDO solo al agotar los intentos: mientras queden, la
            # fila sigue PENDIENTE y el barrido la vuelve a tomar.
            if aviso.email_intentos >= MAX_INTENTOS:
                aviso.email_estado = NotificacionInterna.EstadoEntrega.FALLIDO
                logger.error(
                    'El aviso interno %s se dio por perdido tras %d intentos',
                    aviso.clave, aviso.email_intentos,
                )
            fallidos += 1
        else:
            aviso.email_estado = NotificacionInterna.EstadoEntrega.ENVIADO
            aviso.email_enviado_en = timezone.now()
            aviso.email_error = ''
            enviados += 1

        aviso.save(update_fields=[
            'email_estado', 'email_intentos', 'email_error', 'email_enviado_en',
        ])

    return {'internas_enviadas': enviados, 'internas_fallidas': fallidos}

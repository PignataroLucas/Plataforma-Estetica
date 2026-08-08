"""
Drenado de la cola de avisos.

Toma los avisos pendientes, los manda por el canal y anota qué pasó. Está pensado
para correr muchas veces, en paralelo y sin coordinación externa:

- **Toma en dos fases.** Primero marca las filas como ``PROCESANDO`` en una
  transacción corta con ``skip_locked``, y recién después habla con Expo. Así dos
  corridas simultáneas nunca agarran el mismo aviso, y ninguna sostiene un lock
  de base mientras espera una respuesta HTTP.
- **Se recupera sola.** Si un proceso se muere a mitad de camino, los avisos que
  quedaron ``PROCESANDO`` vuelven a la cola solos después de un rato.
- **Manda en lotes.** Quinientos avisos a un dispositivo cada uno son cinco
  requests a Expo, no quinientos.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from . import canales
from .canales import MensajeSaliente
from .models import Aviso, DispositivoPush, EnvioPush

logger = logging.getLogger(__name__)

# Cuántos avisos toma una corrida. Alto para que el cron se ponga al día tras un
# corte, acotado para que una corrida no se eternice.
LOTE_POR_CORRIDA = 500

# Cuántas veces se reintenta un aviso antes de darlo por perdido.
MAX_INTENTOS = 3

# Cuánto se espera antes de asumir que el proceso que lo tomó se murió.
MINUTOS_PARA_RESCATAR = 15

# La doc de Expo recomienda esperar 15 minutos antes de pedir el recibo.
MINUTOS_ANTES_DEL_RECIBO = 15

# Expo borra los recibos a las 24 horas: después de eso ya no hay qué preguntar.
HORAS_PARA_DESISTIR_DEL_RECIBO = 24

# Tope de recibos por corrida. Coincide con el máximo que acepta Expo por request.
MAX_RECIBOS_POR_CORRIDA = 1000


def _canal_android(aviso: Aviso) -> str:
    """
    Un canal de Android por categoría, para que el sistema operativo también deje
    silenciar promociones sin silenciar turnos.
    """
    return aviso.categoria.lower()


def rescatar_colgados(ahora=None) -> int:
    """Devuelve a la cola los avisos que quedaron tomados por un proceso muerto."""
    ahora = ahora or timezone.now()
    corte = ahora - timedelta(minutes=MINUTOS_PARA_RESCATAR)

    colgados = Aviso.objects.filter(estado=Aviso.Estado.PROCESANDO, creado_en__lte=corte)

    # Los que ya agotaron los intentos no vuelven: se dan por perdidos.
    agotados = colgados.filter(intentos__gte=MAX_INTENTOS).update(
        estado=Aviso.Estado.FALLIDO,
        error='Se agotaron los intentos tras quedar en curso',
    )
    rescatados = colgados.filter(intentos__lt=MAX_INTENTOS).update(
        estado=Aviso.Estado.PENDIENTE
    )

    if rescatados or agotados:
        logger.warning(
            "Avisos colgados: %d devueltos a la cola, %d dados por perdidos",
            rescatados, agotados,
        )
    return rescatados


def _tomar(limite: int, ahora) -> list[Aviso]:
    """
    Marca hasta ``limite`` avisos como en curso y los devuelve.

    Transacción corta a propósito: adentro no hay nada más lento que un UPDATE.
    """
    with transaction.atomic():
        ids = list(
            Aviso.objects
            .select_for_update(skip_locked=True)
            .filter(estado=Aviso.Estado.PENDIENTE, programado_para__lte=ahora)
            .order_by('programado_para')
            .values_list('id', flat=True)[:limite]
        )
        if not ids:
            return []
        Aviso.objects.filter(id__in=ids).update(estado=Aviso.Estado.PROCESANDO)

    return list(
        Aviso.objects
        .filter(id__in=ids)
        .select_related('usuario_cliente')
        .order_by('programado_para')
    )


def _dispositivos_por_usuario(avisos: list[Aviso]) -> dict[int, list[DispositivoPush]]:
    """Una sola consulta para todos los destinatarios de la tanda."""
    usuarios = {aviso.usuario_cliente_id for aviso in avisos}
    por_usuario: dict[int, list[DispositivoPush]] = {}
    for dispositivo in DispositivoPush.objects.filter(
        usuario_cliente_id__in=usuarios, activo=True
    ):
        por_usuario.setdefault(dispositivo.usuario_cliente_id, []).append(dispositivo)
    return por_usuario


def procesar_pendientes(limite: int = LOTE_POR_CORRIDA, ahora=None) -> dict:
    """
    Manda todo lo que esté vencido y devuelve un resumen de la corrida.

    El resumen es lo que imprime el comando de cron, así que sirve para saber de
    un vistazo si algo se está acumulando.
    """
    ahora = ahora or timezone.now()
    rescatados = rescatar_colgados(ahora)

    avisos = _tomar(limite, ahora)
    if not avisos:
        return {'tomados': 0, 'enviados': 0, 'sin_destino': 0, 'fallidos': 0,
                'reencolados': 0, 'rescatados': rescatados}

    dispositivos = _dispositivos_por_usuario(avisos)

    # Se arma una sola tanda de mensajes para todos los avisos: el canal la parte
    # en lotes de 100 y hace la menor cantidad de requests posible.
    pares: list[tuple[Aviso, DispositivoPush]] = []
    mensajes: list[MensajeSaliente] = []
    sin_destino: list[Aviso] = []

    for aviso in avisos:
        destinos = dispositivos.get(aviso.usuario_cliente_id, [])
        if not destinos:
            sin_destino.append(aviso)
            continue
        for dispositivo in destinos:
            pares.append((aviso, dispositivo))
            mensajes.append(MensajeSaliente(
                destino=dispositivo.token,
                titulo=aviso.titulo,
                cuerpo=aviso.cuerpo,
                datos={**aviso.datos, 'avisoId': aviso.id},
                canal_android=_canal_android(aviso),
            ))

    if sin_destino:
        Aviso.objects.filter(id__in=[a.id for a in sin_destino]).update(
            estado=Aviso.Estado.SIN_DESTINO
        )

    resultados = canales.activo().enviar(mensajes)

    if len(resultados) != len(pares):
        # El canal garantiza orden y cantidad; si se rompe esa promesa no podemos
        # aparear resultado con envío y es preferible reencolar todo.
        logger.error(
            "El canal devolvió %d resultados para %d mensajes: se reencola la tanda",
            len(resultados), len(pares),
        )
        Aviso.objects.filter(id__in=[a.id for a, _ in pares]).update(
            estado=Aviso.Estado.PENDIENTE
        )
        return {'tomados': len(avisos), 'enviados': 0, 'sin_destino': len(sin_destino),
                'fallidos': 0, 'reencolados': len(avisos) - len(sin_destino),
                'rescatados': rescatados}

    return _asentar(avisos, sin_destino, pares, resultados, ahora, rescatados)


def _asentar(avisos, sin_destino, pares, resultados, ahora, rescatados) -> dict:
    """Escribe el desenlace de cada envío y el estado final de cada aviso."""
    # aviso_id -> (hubo_alguno_ok, hubo_alguno_reintentable)
    balance: dict[int, list[bool]] = {}
    tokens_muertos: list[int] = []

    for (aviso, dispositivo), resultado in zip(pares, resultados):
        EnvioPush.objects.update_or_create(
            aviso=aviso,
            dispositivo=dispositivo,
            defaults={
                'estado': EnvioPush.Estado.ACEPTADO if resultado.ok else EnvioPush.Estado.FALLIDO,
                'ticket_id': resultado.ticket_id,
                'error': resultado.error,
                'confirmado_en': None if resultado.ok else ahora,
            },
        )
        if resultado.destino_muerto:
            tokens_muertos.append(dispositivo.id)

        estado = balance.setdefault(aviso.id, [False, False])
        estado[0] = estado[0] or resultado.ok
        estado[1] = estado[1] or resultado.reintentable

    if tokens_muertos:
        # La app se desinstaló o el token se revocó: se apaga y deja de gastar
        # requests en cada corrida.
        DispositivoPush.objects.filter(id__in=tokens_muertos).update(
            activo=False, motivo_baja=DispositivoPush.MotivoBaja.TOKEN_MUERTO
        )

    enviados, reencolados, fallidos = [], [], []
    for aviso in avisos:
        if aviso.id not in balance:
            continue  # sin dispositivos, ya quedó marcado
        alguno_ok, alguno_reintentable = balance[aviso.id]
        if alguno_ok:
            enviados.append(aviso.id)
        elif alguno_reintentable and aviso.intentos + 1 < MAX_INTENTOS:
            reencolados.append(aviso.id)
        else:
            fallidos.append(aviso.id)

    # El contador de intentos sube en el mismo UPDATE que el estado.
    if enviados:
        Aviso.objects.filter(id__in=enviados).update(
            estado=Aviso.Estado.ENVIADO, enviado_en=ahora, error='',
            intentos=F('intentos') + 1,
        )
    if reencolados:
        Aviso.objects.filter(id__in=reencolados).update(
            estado=Aviso.Estado.PENDIENTE, intentos=F('intentos') + 1
        )
    if fallidos:
        Aviso.objects.filter(id__in=fallidos).update(
            estado=Aviso.Estado.FALLIDO, intentos=F('intentos') + 1
        )

    resumen = {
        'tomados': len(avisos),
        'enviados': len(enviados),
        'sin_destino': len(sin_destino),
        'fallidos': len(fallidos),
        'reencolados': len(reencolados),
        'rescatados': rescatados,
        'tokens_dados_de_baja': len(tokens_muertos),
    }
    logger.info("Cola de avisos procesada: %s", resumen)
    return resumen


def procesar_recibos(limite: int = MAX_RECIBOS_POR_CORRIDA, ahora=None) -> dict:
    """
    Cierra el círculo: pregunta a Expo qué pasó de verdad con lo que aceptó.

    Es lo que detecta las apps desinstaladas. Sin esto la tabla de dispositivos
    se llena de tokens muertos a los que se les manda para siempre.
    """
    ahora = ahora or timezone.now()

    # Los que ya no tienen recibo posible se cierran sin veredicto.
    vencidos = EnvioPush.objects.filter(
        estado=EnvioPush.Estado.ACEPTADO,
        confirmado_en__isnull=True,
        creado_en__lte=ahora - timedelta(hours=HORAS_PARA_DESISTIR_DEL_RECIBO),
    ).update(confirmado_en=ahora)

    envios = list(
        EnvioPush.objects
        .filter(
            estado=EnvioPush.Estado.ACEPTADO,
            confirmado_en__isnull=True,
            creado_en__lte=ahora - timedelta(minutes=MINUTOS_ANTES_DEL_RECIBO),
        )
        .exclude(ticket_id='')
        .select_related('dispositivo')[:limite]
    )
    if not envios:
        return {'consultados': 0, 'entregados': 0, 'fallidos': 0,
                'tokens_dados_de_baja': 0, 'sin_recibo': vencidos}

    recibos = canales.activo().consultar_recibos([e.ticket_id for e in envios])

    entregados, fallidos, tokens_muertos = [], [], []
    for envio in envios:
        recibo = recibos.get(envio.ticket_id)
        if recibo is None:
            continue  # Expo todavía no lo resolvió; se vuelve a preguntar
        if recibo.ok:
            entregados.append(envio.id)
        else:
            envio.estado = EnvioPush.Estado.FALLIDO
            envio.error = recibo.error
            envio.confirmado_en = ahora
            envio.save(update_fields=['estado', 'error', 'confirmado_en'])
            fallidos.append(envio.id)
            if recibo.destino_muerto:
                tokens_muertos.append(envio.dispositivo_id)

    if entregados:
        EnvioPush.objects.filter(id__in=entregados).update(
            estado=EnvioPush.Estado.ENTREGADO, confirmado_en=ahora
        )
    if tokens_muertos:
        DispositivoPush.objects.filter(id__in=tokens_muertos).update(
            activo=False, motivo_baja=DispositivoPush.MotivoBaja.TOKEN_MUERTO
        )

    resumen = {
        'consultados': len(envios),
        'entregados': len(entregados),
        'fallidos': len(fallidos),
        'tokens_dados_de_baja': len(tokens_muertos),
        'sin_recibo': vencidos,
    }
    logger.info("Recibos de push procesados: %s", resumen)
    return resumen

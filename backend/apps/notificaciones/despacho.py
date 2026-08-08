"""
Creación de avisos.

Es la única puerta de entrada al sistema: todo lo que quiera notificar algo llama
a ``crear_aviso`` (o a ``crear_aviso_para_cliente``) y sigue con lo suyo. Acá se
resuelven las tres reglas que no queremos repetidas en cada llamador:

1. **Preferencias** — si la clienta apagó la categoría, el aviso no se crea.
2. **Plantilla** — texto propio del centro si existe, si no el del catálogo.
3. **Idempotencia** — con ``clave``, el mismo aviso no entra dos veces por más
   que el disparador corra de nuevo.

Nada de esto envía: escribir la fila es todo el trabajo. El envío es de
``cola.py``, y esa separación es la que hace que un pico de avisos no cuelgue un
request ni pierda mensajes si el proceso de envío está caído.
"""
import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from . import eventos
from .models import Aviso, PlantillaNotificacion, PreferenciaNotificacion

logger = logging.getLogger(__name__)


def categoria_habilitada(usuario_cliente, categoria) -> bool:
    """
    ¿La clienta quiere recibir esta categoría?

    Sin fila en la tabla, sí: las preferencias guardan solo lo que se apagó.
    """
    return not PreferenciaNotificacion.objects.filter(
        usuario_cliente=usuario_cliente,
        categoria=categoria,
        habilitada=False,
    ).exists()


def resolver_textos(evento: eventos.Evento, centro_estetica, contexto: dict):
    """
    Devuelve ``(titulo, cuerpo, ruta)`` ya renderizados.

    El centro puede pisar el texto por evento; si no lo hizo, o si desactivó su
    plantilla, se usa el del catálogo. La ruta no es editable: es navegación de
    la app, no contenido.
    """
    titulo_base, cuerpo_base = evento.titulo, evento.cuerpo

    if centro_estetica is not None:
        plantilla = PlantillaNotificacion.objects.filter(
            centro_estetica=centro_estetica,
            evento=evento.clave,
            activa=True,
        ).first()
        if plantilla:
            titulo_base, cuerpo_base = plantilla.titulo, plantilla.cuerpo

    return (
        eventos.renderizar(titulo_base, contexto),
        eventos.renderizar(cuerpo_base, contexto),
        eventos.renderizar(evento.ruta, contexto) if evento.ruta else '',
    )


def crear_aviso(
    *,
    evento: str,
    usuario_cliente,
    contexto: dict | None = None,
    centro_estetica=None,
    cliente=None,
    clave: str | None = None,
    programado_para=None,
    datos_extra: dict | None = None,
) -> Aviso | None:
    """
    Deja un aviso listo para que la cola lo mande.

    Devuelve el ``Aviso`` creado, o ``None`` si no correspondía crearlo: porque
    la clienta apagó la categoría o porque ya existía uno con la misma ``clave``.
    Las dos son situaciones normales, no errores.

    ``clave`` es lo que hace seguro reintentar un disparador. Usar algo estable y
    descriptivo: ``turno:12:recordatorio_24h``, ``cumple:45:2026``.
    """
    definicion = eventos.obtener(evento)
    contexto = contexto or {}

    if not definicion.transaccional and not categoria_habilitada(
        usuario_cliente, definicion.categoria
    ):
        logger.debug(
            "Aviso '%s' omitido: %s tiene apagada la categoría %s",
            evento, usuario_cliente.email, definicion.categoria,
        )
        return None

    titulo, cuerpo, ruta = resolver_textos(definicion, centro_estetica, contexto)

    datos = {'evento': definicion.clave}
    if ruta:
        datos['ruta'] = ruta
    if datos_extra:
        datos.update(datos_extra)

    try:
        # La transacción propia evita que un choque de clave --que es esperable--
        # marque como rota la transacción del llamador.
        with transaction.atomic():
            return Aviso.objects.create(
                evento=definicion.clave,
                categoria=definicion.categoria,
                usuario_cliente=usuario_cliente,
                centro_estetica=centro_estetica,
                cliente=cliente,
                titulo=titulo,
                cuerpo=cuerpo,
                datos=datos,
                clave=clave or None,
                programado_para=programado_para or timezone.now(),
            )
    except IntegrityError:
        # Ya existía uno con esta clave: el disparador volvió a correr.
        logger.debug("Aviso '%s' ya existía con clave %s", evento, clave)
        return None


def crear_aviso_para_cliente(*, evento: str, cliente, **kwargs) -> list[Aviso]:
    """
    Igual que ``crear_aviso`` pero partiendo de una ficha del CRM.

    El staff piensa en fichas ``Cliente``; el push viaja a cuentas de app. Una
    ficha puede no tener cuenta (no se notifica) o tenerla compartida entre
    varias cuentas, así que devuelve una lista.

    La ``clave`` recibida se sufija por cuenta para que la idempotencia siga
    siendo por destinatario y no bloquee a la segunda cuenta.
    """
    clave_base = kwargs.pop('clave', None)
    kwargs.setdefault('centro_estetica', cliente.centro_estetica)

    avisos = []
    for vinculacion in cliente.vinculaciones.select_related('usuario_cliente'):
        usuario = vinculacion.usuario_cliente
        if not usuario.activo:
            continue
        aviso = crear_aviso(
            evento=evento,
            usuario_cliente=usuario,
            cliente=cliente,
            clave=f"{clave_base}:u{usuario.id}" if clave_base else None,
            **kwargs,
        )
        if aviso:
            avisos.append(aviso)
    return avisos


def crear_avisos_masivos(
    *,
    evento: str,
    usuarios,
    contexto: dict | None = None,
    centro_estetica=None,
    clave_base: str | None = None,
    programado_para=None,
    datos_extra: dict | None = None,
) -> dict:
    """
    Crea el mismo aviso para muchas cuentas de una sola vez.

    Es el camino de las promociones y las novedades del centro, donde el
    destinatario se cuenta de a cientos. Hace tres consultas en total sin importar
    cuánta gente sea: una para descartar a quienes apagaron la categoría, un
    ``bulk_create`` y una para contar.

    El texto se renderiza una sola vez, así que **no admite variables por
    persona**: para saludar por el nombre está ``crear_aviso``.
    """
    definicion = eventos.obtener(evento)
    contexto = contexto or {}
    usuarios = list(usuarios)

    if not definicion.transaccional:
        apagaron = set(
            PreferenciaNotificacion.objects
            .filter(
                usuario_cliente__in=usuarios,
                categoria=definicion.categoria,
                habilitada=False,
            )
            .values_list('usuario_cliente_id', flat=True)
        )
        usuarios = [u for u in usuarios if u.id not in apagaron]

    if not usuarios:
        return {'creados': 0, 'omitidos': 0}

    titulo, cuerpo, ruta = resolver_textos(definicion, centro_estetica, contexto)
    datos = {'evento': definicion.clave}
    if ruta:
        datos['ruta'] = ruta
    if datos_extra:
        datos.update(datos_extra)

    momento = programado_para or timezone.now()
    Aviso.objects.bulk_create(
        [
            Aviso(
                evento=definicion.clave,
                categoria=definicion.categoria,
                usuario_cliente=usuario,
                centro_estetica=centro_estetica,
                titulo=titulo,
                cuerpo=cuerpo,
                datos=datos,
                clave=f"{clave_base}:u{usuario.id}" if clave_base else None,
                programado_para=momento,
            )
            for usuario in usuarios
        ],
        # Los repetidos se descartan solos: es lo que hace seguro reintentar un
        # envío masivo que se cortó a la mitad.
        ignore_conflicts=True,
    )

    creados = (
        Aviso.objects.filter(clave__startswith=f"{clave_base}:u").count()
        if clave_base else len(usuarios)
    )
    return {'creados': creados, 'omitidos': len(usuarios) - creados}


def descartar_pendientes(*, clave_prefijo: str) -> int:
    """
    Borra avisos que todavía no salieron.

    Sirve cuando el motivo del aviso desapareció o cambió: se canceló el turno y
    el recordatorio de mañana ya no tiene sentido, o se movió de hora y el texto
    quedó viejo.

    Se **borran** en lugar de marcarse cancelados a propósito. La ``clave`` es
    única, así que un aviso cancelado seguiría ocupando su lugar y el disparador
    no podría volver a crearlo: un turno que se cancela y se reactiva se quedaría
    sin recordatorio para siempre. Un aviso que nunca salió no es historia que
    valga la pena guardar; lo que sí queda registrado es lo que se envió.
    """
    borrados, _ = Aviso.objects.filter(
        clave__startswith=clave_prefijo,
        estado=Aviso.Estado.PENDIENTE,
    ).delete()
    return borrados

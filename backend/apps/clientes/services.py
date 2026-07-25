"""
Fusión de fichas de Cliente duplicadas.

Reasigna TODO lo que cuelga de la ficha duplicada a la ficha principal y borra
la duplicada, de forma atómica. Incluye un seguro: si aparece una relación nueva
hacia Cliente que este código no contempla, la fusión aborta (no se pierden datos
al borrar).
"""
from collections import defaultdict

from django.db import models, transaction

from .models import Cliente

# Campos escalares que NO se tocan al consolidar (se conserva el de la principal).
_NO_CONSOLIDAR = {
    'id', 'centro_estetica', 'creado_en', 'actualizado_en',
    'telefono_normalizado', 'ultima_visita', 'foto',
    'activo', 'acepta_promociones', 'acepta_whatsapp',
}


def _consolidar_campos(principal: Cliente, duplicado: Cliente) -> None:
    """
    Completa la ficha principal con datos de la duplicada SIN pisar lo que ya
    tiene: campos vacíos se rellenan; las flags booleanas (contraindicaciones,
    alergias, etc.) se combinan con OR para no perder una advertencia médica.
    """
    cambios = []
    for f in principal._meta.concrete_fields:
        if f.primary_key or f.is_relation or f.name in _NO_CONSOLIDAR:
            continue
        pv = getattr(principal, f.name)
        dv = getattr(duplicado, f.name)
        if isinstance(f, models.BooleanField):
            if dv and not pv:
                setattr(principal, f.name, True)
                cambios.append(f.name)
        elif pv in (None, '') and dv not in (None, ''):
            setattr(principal, f.name, dv)
            cambios.append(f.name)
    if cambios:
        principal.save(update_fields=cambios)


@transaction.atomic
def fusionar_clientes(principal: Cliente, duplicado: Cliente) -> Cliente:
    """
    Fusiona ``duplicado`` dentro de ``principal`` y borra ``duplicado``.
    Devuelve la ficha principal. Lanza ValueError si la fusión no es válida.
    """
    if principal.pk == duplicado.pk:
        raise ValueError('No se puede fusionar una ficha consigo misma')
    if principal.centro_estetica_id != duplicado.centro_estetica_id:
        raise ValueError('Solo se pueden fusionar fichas del mismo centro')

    # 1) Reasignar relaciones con FK directa a Cliente
    duplicado.historial.update(cliente=principal)
    duplicado.planes_tratamiento.update(cliente=principal)
    duplicado.rutinas_cuidado.update(cliente=principal)
    duplicado.notas.update(cliente=principal)
    duplicado.codigos_invitacion.update(cliente=principal)
    duplicado.turnos.update(cliente=principal)
    duplicado.notificaciones.update(cliente=principal)
    # finanzas usa el nombre de campo 'client' (en inglés)
    duplicado.transactions.update(client=principal)
    duplicado.accounts_receivable.update(client=principal)

    # 2) Vinculaciones de app: reasignar evitando duplicar un mismo usuario
    ya_vinculados = set(principal.vinculaciones.values_list('usuario_cliente_id', flat=True))
    for vinc in duplicado.vinculaciones.all():
        if vinc.usuario_cliente_id in ya_vinculados:
            vinc.delete()
        else:
            vinc.cliente = principal
            vinc.save(update_fields=['cliente'])

    # 3) Consolidar los datos de la ficha
    _consolidar_campos(principal, duplicado)

    # 4) Seguro: nada debe quedar apuntando a la ficha duplicada
    for rel in Cliente._meta.related_objects:
        accessor = rel.get_accessor_name()
        if not accessor:
            continue
        manager = getattr(duplicado, accessor, None)
        if manager is not None and hasattr(manager, 'exists') and manager.exists():
            raise RuntimeError(
                f"Relación '{accessor}' quedó sin reasignar en la fusión. "
                f"Actualizá apps/clientes/services.py:fusionar_clientes."
            )

    # 5) Borrar la ficha duplicada
    duplicado.delete()
    return principal


def detectar_duplicados(centro_estetica):
    """
    Encuentra grupos de fichas potencialmente duplicadas dentro de un centro,
    matcheando por teléfono normalizado (E.164) y por email.

    Confianza:
    - ALTA  → comparten teléfono normalizado Y email (candidato a auto-fusión).
    - MEDIA → comparten solo uno de los dos (va a revisión del staff).

    Devuelve una lista de dicts: {clave, valor, confianza, clientes:[Cliente]}.
    """
    clientes = list(Cliente.objects.filter(centro_estetica=centro_estetica))

    por_telefono = defaultdict(list)
    por_email = defaultdict(list)
    for c in clientes:
        if c.telefono_normalizado:
            por_telefono[c.telefono_normalizado].append(c)
        if c.email:
            por_email[c.email.strip().lower()].append(c)

    grupos = []
    ya_emitidos = set()  # frozensets de ids ya agrupados por teléfono

    for telefono, cs in por_telefono.items():
        if len(cs) < 2:
            continue
        emails = {c.email.strip().lower() for c in cs if c.email}
        comparten_email = len(emails) == 1 and all(c.email for c in cs)
        grupos.append({
            'clave': 'telefono',
            'valor': telefono,
            'confianza': 'ALTA' if comparten_email else 'MEDIA',
            'clientes': cs,
        })
        ya_emitidos.add(frozenset(c.id for c in cs))

    for email, cs in por_email.items():
        if len(cs) < 2:
            continue
        if frozenset(c.id for c in cs) in ya_emitidos:
            continue  # mismos miembros que un grupo de teléfono ya emitido
        grupos.append({
            'clave': 'email',
            'valor': email,
            'confianza': 'MEDIA',
            'clientes': cs,
        })

    # ALTA primero, luego los grupos más grandes
    grupos.sort(key=lambda g: (g['confianza'] != 'ALTA', -len(g['clientes'])))
    return grupos

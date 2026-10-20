"""Qué le falta aceptar a una cuenta, y registrar que lo aceptó."""
from . import documentos
from .models import AceptacionLegal


def pendientes(usuario) -> list[documentos.Documento]:
    """Los documentos vigentes que la cuenta todavía no aceptó en su versión actual."""
    aceptadas = set(
        AceptacionLegal.objects.filter(usuario_cliente=usuario)
        .values_list('documento', 'version')
    )
    return [d for d in documentos.A_ACEPTAR if (d.clave, d.version) not in aceptadas]


def aceptar(usuario, documento: documentos.Documento) -> None:
    """Idempotente: aceptar dos veces la misma versión deja una sola constancia."""
    AceptacionLegal.objects.get_or_create(
        usuario_cliente=usuario, documento=documento.clave, version=documento.version,
    )

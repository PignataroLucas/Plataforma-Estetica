"""Utilidades para el módulo de clientes."""
import phonenumbers


def normalizar_telefono(raw, region='AR'):
    """
    Devuelve el teléfono en formato canónico E.164 (ej: '+5491123456789').

    Es defensivo: si el número está vacío o no se puede parsear/validar,
    devuelve '' en lugar de lanzar una excepción, para no romper el save() de Cliente.

    Args:
        raw: teléfono crudo tal como lo cargó el staff.
        region: región por defecto para números sin prefijo internacional (default Argentina).
    """
    if not raw:
        return ''

    try:
        parsed = phonenumbers.parse(raw, region)
    except phonenumbers.NumberParseException:
        return ''

    if not phonenumbers.is_valid_number(parsed):
        return ''

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

"""
Storage de archivos públicos.

De los siete campos de archivo del proyecto solo dos son públicos (la foto de
producto y el logo del centro). Los otros cinco -- foto de cliente, antes,
después, foto de usuario y comprobante de transacción -- son datos sensibles y
siguen en el disco local.

Por eso el bucket NO es el storage `default`: es un storage con nombre al que
los campos públicos optan explícitamente. Así un campo de archivo nuevo que
nadie pensó nace privado en vez de aterrizar en un bucket de lectura pública sin
que nadie se entere. Falla cerrado, que es como tiene que fallar cuando hay
datos de salud de por medio.
"""
from django.core.files.storage import storages


def storage_publico():
    """
    Storage de los campos que se sirven al catálogo de la app.

    Es un callable y no la instancia porque Django serializa el argumento
    `storage` dentro de la migración: una instancia dejaría el bucket congelado
    en el historial de migraciones.
    """
    return storages['publico']

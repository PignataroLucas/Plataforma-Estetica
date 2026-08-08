"""
Generación de miniaturas para las fotos de producto.

S3 no transforma imágenes (Cloudinary sí; es la única ventaja que se resigna al
elegirlo). Servir el original de 3 MB que sale de un celular en una grilla de 31
productos, por datos móviles, es una mala experiencia, así que la miniatura se
genera al subir.
"""
import logging
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# 400 px de ancho alcanza para una grilla de dos columnas en pantalla retina.
ANCHO_MINIATURA = 400
# WebP a calidad 80 pesa cerca de la mitad que un JPEG equivalente y lo soportan
# todas las versiones de Android e iOS que la app targetea.
CALIDAD_MINIATURA = 80


def nombre_miniatura(nombre_original):
    """`productos/crema.jpg` -> `crema.webp` (el upload_to pone el directorio)."""
    return f"{Path(nombre_original).stem}.webp"


def generar_miniatura(archivo, ancho=ANCHO_MINIATURA, calidad=CALIDAD_MINIATURA):
    """
    Devuelve la miniatura WebP como ContentFile, o None si la imagen no se pudo
    procesar.

    Devolver None en vez de propagar el error es deliberado: la foto original ya
    está guardada cuando esto corre, y perder la miniatura de un producto no
    justifica voltear el guardado. La app cae al original.
    """
    try:
        archivo.open('rb')
        with Image.open(archivo) as imagen:
            # Las fotos de celular vienen rotadas por metadato EXIF: sin esto la
            # miniatura sale acostada aunque el original se vea bien.
            imagen = ImageOps.exif_transpose(imagen)

            if imagen.mode in ('P', 'LA', 'PA'):
                imagen = imagen.convert('RGBA')
            elif imagen.mode not in ('RGB', 'RGBA'):
                imagen = imagen.convert('RGB')

            if imagen.width > ancho:
                alto = max(1, round(imagen.height * ancho / imagen.width))
                imagen = imagen.resize((ancho, alto), Image.LANCZOS)

            buffer = BytesIO()
            imagen.save(buffer, format='WEBP', quality=calidad, method=6)
    except Exception:
        logger.warning(
            "No se pudo generar la miniatura de %r", getattr(archivo, 'name', archivo),
            exc_info=True,
        )
        return None

    return ContentFile(buffer.getvalue())

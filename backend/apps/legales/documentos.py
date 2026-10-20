"""
Los documentos legales de la app: qué hay, en qué versión y cómo se muestran.

El texto vive en ``documentos/*.md`` y es la única copia. De ahí salen las páginas
públicas que enlazan la app y Google Play: no hay una segunda versión en otro
sitio que se pueda desincronizar.

**La versión se sube a mano, con la fecha, solo cuando un cambio es de fondo.**
Al subirla, la app le vuelve a pedir la aceptación a cada cuenta, que es lo que
promete la sección "Modificaciones" de la política. Corregir un error de tipeo no
la sube: sería pedirle a todo el mundo que acepte de nuevo lo mismo.
"""
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

import markdown

CARPETA = Path(__file__).resolve().parent / 'documentos'

MESES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]


@dataclass(frozen=True)
class Documento:
    clave: str
    titulo: str
    archivo: str
    #: Ruta de la página pública. La app la concatena a la URL base del backend.
    ruta: str
    #: Fecha de la última versión de fondo. ``None`` si no se acepta, solo se publica.
    version: date | None = None


PRIVACIDAD = Documento(
    clave='PRIVACIDAD',
    titulo='Política de privacidad',
    archivo='politica_privacidad.md',
    ruta='/legales/privacidad/',
    version=date(2026, 10, 20),
)

ELIMINAR_CUENTA = Documento(
    clave='ELIMINAR_CUENTA',
    titulo='Eliminación de la cuenta',
    archivo='eliminar_cuenta.md',
    ruta='/legales/eliminar-cuenta/',
)

#: Lo que la clienta tiene que aceptar para usar la app. Los términos y
#: condiciones, cuando existan, se suman acá con su propia clave y versión.
A_ACEPTAR = (PRIVACIDAD,)


def por_clave(clave: str) -> Documento | None:
    return next((d for d in A_ACEPTAR if d.clave == clave), None)


def fecha_larga(fecha: date) -> str:
    return f'{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}'


@lru_cache(maxsize=None)
def html_de(documento: Documento) -> str:
    """
    El documento listo para la página pública.

    Se salta las líneas que empiezan con ``>``: son las notas de revisión del
    archivo, que no se publican. ``[FECHA]`` se reemplaza por la versión, para que
    la fecha que lee la clienta sea siempre la que aceptó.
    """
    texto = (CARPETA / documento.archivo).read_text(encoding='utf-8')
    lineas = [linea for linea in texto.splitlines() if not linea.startswith('>')]
    texto = '\n'.join(lineas).strip()
    if documento.version is not None:
        texto = texto.replace('[FECHA]', fecha_larga(documento.version))
    return markdown.markdown(texto, extensions=['tables'])

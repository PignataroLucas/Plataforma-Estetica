"""
Las rutas de los avisos tienen que existir en la app.

Cada ``Evento`` del catálogo lleva la ruta a la que navega el teléfono cuando
alguien toca la notificación. Nadie valida esa cadena: no la valida el despacho,
no la valida Expo, y el aviso se manda igual. El defecto aparece recién en el
teléfono de la clienta, que toca la notificación y no llega a ninguna parte.

Es lo que pasó con ``/promos``: cumpleaños y oferta nueva apuntaban a una
pantalla que nunca se construyó, y sobrevivió a todo el desarrollo del sistema
de avisos porque del lado del backend no hay forma de que se note.

El test arma el árbol de rutas leyendo ``client-app/src/app/``, que es de donde
expo-router saca las suyas, y compara. Se saltea entero si la app no está en
esta rama: el backend vive también en ``main``, donde ``client-app/`` no existe.

**Corriendo con docker-compose siempre se saltea**, y no es un defecto: el
contenedor del backend monta solo ``backend/``, así que desde adentro la app no
existe. Quien lo corre de verdad es CI, que hace checkout del repo entero.
"""
from pathlib import Path

import pytest
from django.conf import settings

from apps.notificaciones import eventos

APP_DIR = Path(settings.BASE_DIR).parent / 'client-app' / 'src' / 'app'

#: Marca con la que se comparan los segmentos variables. Da igual que la app
#: los llame ``[id]`` y el backend ``{servicio_id}``: lo que se compara es la
#: forma de la ruta, no el nombre del parámetro.
DINAMICO = '<dinámico>'


def _segmento(nombre: str) -> str:
    """``[id]`` y ``[...resto]`` son un segmento variable; el resto, literal."""
    return DINAMICO if nombre.startswith('[') and nombre.endswith(']') else nombre


def rutas_de_la_app() -> set[str]:
    """
    Las rutas que expo-router genera a partir de los archivos.

    Tres convenciones que hay que respetar para no comparar contra un árbol
    equivocado: los directorios entre paréntesis son grupos y **no** aparecen en
    la URL, ``index`` es la ruta del directorio que lo contiene, y los archivos
    que empiezan con ``_`` o ``+`` no son pantallas navegables (layouts,
    ``+not-found``, rutas de API).
    """
    rutas = set()
    for archivo in APP_DIR.rglob('*.tsx'):
        if archivo.stem.startswith(('_', '+')):
            continue

        partes = [
            _segmento(parte)
            for parte in archivo.relative_to(APP_DIR).parts[:-1]
            if not (parte.startswith('(') and parte.endswith(')'))
        ]
        if archivo.stem != 'index':
            partes.append(_segmento(archivo.stem))

        rutas.add('/' + '/'.join(partes))
    return rutas


def ruta_de_evento(ruta: str) -> str:
    """``/servicio/{servicio_id}`` -> ``/servicio/<dinámico>``."""
    return '/'.join(
        DINAMICO if p.startswith('{') and p.endswith('}') else p
        for p in ruta.split('/')
    )


@pytest.mark.skipif(not APP_DIR.is_dir(), reason='client-app no está en esta rama')
def test_toda_ruta_de_aviso_existe_en_la_app():
    disponibles = rutas_de_la_app()

    # Si el árbol se movió de lugar, el conjunto queda vacío o casi, y el test
    # pasaría por no encontrar nada que contradecirlo. Estas dos son de las
    # primeras pantallas que existieron y no se van a ir a ningún lado.
    assert {'/', '/turnos'} <= disponibles, (
        f'No se pudo leer el árbol de rutas de la app en {APP_DIR}. '
        f'Lo que se encontró: {sorted(disponibles)}'
    )

    faltantes = {
        evento.clave: evento.ruta
        for evento in eventos.EVENTOS.values()
        if evento.ruta and ruta_de_evento(evento.ruta) not in disponibles
    }

    assert not faltantes, (
        'Estos avisos llevan a una ruta que no existe en la app: '
        f'{faltantes}. Las que hay son: {sorted(disponibles)}.'
    )

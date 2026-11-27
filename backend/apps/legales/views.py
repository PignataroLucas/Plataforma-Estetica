from django.shortcuts import render
from django.views.decorators.cache import cache_page

from .documentos import ELIMINAR_CUENTA, PRIVACIDAD, html_de


def _pagina(request, documento):
    return render(request, 'legales/documento.html', {
        'titulo': documento.titulo,
        'contenido': html_de(documento),
    })


# Páginas públicas, sin sesión: las abre la app antes del registro y las revisa
# Google Play. El texto solo cambia con un deploy, así que se cachea.
@cache_page(60 * 60)
def privacidad(request):
    return _pagina(request, PRIVACIDAD)


@cache_page(60 * 60)
def eliminar_cuenta(request):
    return _pagina(request, ELIMINAR_CUENTA)

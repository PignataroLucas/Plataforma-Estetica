"""
Baja de una cuenta de la app a pedido de su titular.

Google Play exige que toda app que deja crear cuentas deje también borrarlas
desde adentro. Lo que importa acá es **qué se borra y qué no**, porque son dos
cosas distintas que conviven en la misma persona:

- **La cuenta de la app** (``UsuarioCliente``) es de la clienta: el login, los
  teléfonos registrados para push, sus preferencias de avisos, los avisos que se
  le mandaron, sus códigos de recuperación y los vínculos con cada centro. Todo
  eso se borra.
- **La ficha del CRM** (``Cliente``) es del centro: el historial de tratamientos,
  los turnos, los pagos, la rutina. Existía antes de la app y el centro la
  necesita para seguir atendiéndola. **No se toca.** La política de privacidad lo
  tiene que decir con estas palabras.

Lo que hace falta borrar cuelga de la cuenta con ``on_delete=CASCADE``, así que
alcanza con borrar la cuenta. Los códigos de invitación que usó no se borran:
son del centro, y su FK queda en ``NULL`` (``SET_NULL``). El test
``test_eliminar_cuenta.py`` fija la lista completa de relaciones: si aparece una
nueva, hay que decidir acá qué le pasa antes de que una baja se la lleve puesta
o la deje huérfana.
"""
import logging

from django.db import transaction

from .models import UsuarioCliente

logger = logging.getLogger(__name__)


@transaction.atomic
def eliminar_cuenta_app(usuario: UsuarioCliente) -> None:
    """Borra la cuenta y todo lo que es de la cuenta. Las fichas de los centros quedan."""
    pk = usuario.pk
    centros = list(usuario.vinculaciones.values_list('cliente__centro_estetica_id', flat=True))

    usuario.delete()

    # Sin email ni nombre: el log no puede guardar lo que la clienta pidió borrar.
    logger.info('Cuenta de app %s eliminada por su titular (centros %s)', pk, centros)

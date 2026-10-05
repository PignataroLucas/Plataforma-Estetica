"""
El admin de turnos tiene que renderizar *con turnos adentro*.

Mismo motivo que el de inventario: `check` valida la configuración pero no
ejecuta las columnas calculadas, así que un error en `plazo` o en
`estado_coloreado` aparece recién cuando hay una fila que formatear. Una lista
vacía renderiza bien, que es justo cómo una pantalla rota llega a producción.

Acá se cubren además los tres caminos de `plazo`, porque cada uno arma el HTML
distinto: sin plazo, pendiente con tiempo, y vencido.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.servicios.models import Servicio
from apps.turnos.models import Turno


@pytest.fixture(autouse=True)
def plain_static(settings):
    """WhiteNoise's manifest storage needs a `collectstatic` no test run does."""
    settings.STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'publico': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'
        },
    }


def hacer_turno(**extra):
    centro = CentroEstetica.objects.create(
        nombre='Ame', telefono='1', email='ame@test.local'
    )
    sucursal = Sucursal.objects.create(
        centro_estetica=centro, nombre='Banfield', direccion='Calle 1',
        telefono='1', ciudad='Banfield', provincia='BA',
    )
    profesional = Usuario.objects.create_user(
        username='ana', password='x', centro_estetica=centro, sucursal=sucursal,
    )
    servicio = Servicio.objects.create(
        sucursal=sucursal, nombre='Facial', duracion_minutos=60,
        precio=Decimal('20000'),
    )
    cliente = Cliente.objects.create(
        centro_estetica=centro, nombre='Flor', apellido='A', telefono='11',
    )
    inicio = timezone.now() + timedelta(days=3)

    datos = {
        'sucursal': sucursal, 'cliente': cliente, 'servicio': servicio,
        'profesional': profesional, 'fecha_hora_inicio': inicio,
        'fecha_hora_fin': inicio + timedelta(minutes=60),
        'monto_total': servicio.precio,
    }
    datos.update(extra)
    return Turno.objects.create(**datos)


@pytest.mark.django_db
class TestAdminDeTurnosRenderiza:

    def test_la_lista_renderiza_con_un_pedido_pendiente(self, admin_client):
        """El camino normal: pendiente con plazo por delante."""
        hacer_turno(
            estado=Turno.Estado.PENDIENTE,
            origen=Turno.Origen.APP,
            vence_en=timezone.now() + timedelta(hours=2, minutes=30),
        )

        respuesta = admin_client.get(reverse('admin:turnos_turno_changelist'))

        assert respuesta.status_code == 200
        assert b'faltan' in respuesta.content

    def test_la_lista_renderiza_un_pedido_ya_vencido(self, admin_client):
        """
        El barrido puede tardar en levantarlo, así que un pendiente con el plazo
        pasado es un estado real y la columna tiene que saber dibujarlo.
        """
        hacer_turno(
            estado=Turno.Estado.PENDIENTE,
            origen=Turno.Origen.APP,
            vence_en=timezone.now() - timedelta(minutes=5),
        )

        respuesta = admin_client.get(reverse('admin:turnos_turno_changelist'))

        assert respuesta.status_code == 200
        assert b'vencido' in respuesta.content

    def test_la_lista_renderiza_un_turno_sin_plazo(self, admin_client):
        """Los cargados en el CRM no vencen: `vence_en` es nulo."""
        hacer_turno(estado=Turno.Estado.CONFIRMADO, origen=Turno.Origen.CRM)

        respuesta = admin_client.get(reverse('admin:turnos_turno_changelist'))

        assert respuesta.status_code == 200

    def test_la_ficha_renderiza(self, admin_client):
        """
        Los fieldsets nombran campos a mano: un nombre mal escrito revienta acá y
        en ningún otro lado.
        """
        turno = hacer_turno(
            estado=Turno.Estado.RECHAZADO,
            origen=Turno.Origen.APP,
            vence_en=timezone.now() - timedelta(hours=1),
            motivo_rechazo=Turno.MotivoRechazo.VENCIDO,
        )

        respuesta = admin_client.get(
            reverse('admin:turnos_turno_change', args=[turno.pk])
        )

        assert respuesta.status_code == 200

    def test_no_se_pueden_crear_turnos_desde_el_admin(self, admin_client):
        """
        Crear un turno acá saltearía el lock de `reservar_turno`, que es lo que
        evita la doble reserva. Si alguien habilita esto sin querer, que falle un
        test y no la agenda de un sábado.
        """
        respuesta = admin_client.get(reverse('admin:turnos_turno_add'))

        assert respuesta.status_code == 403

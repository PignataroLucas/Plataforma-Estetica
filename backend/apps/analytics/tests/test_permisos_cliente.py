"""
Aislamiento multi-tenant de los analytics de cliente individual.

Lo que se cuida acá es un IDOR cross-tenant. Los 7 endpoints
`/api/analytics/client/<id>/...` comparten la permission class
`CanViewClientAnalytics`. La rama ADMIN devolvía `True` sin mirar el centro, así
que un ADMIN del centro A podía leer analytics (y PII) de clientes del centro B
con solo enumerar ids. Este test existe para que esa regresión no vuelva: ningún
rol puede salir de su propio centro, y el acceso legítimo dentro del centro sigue
funcionando.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.clientes.models import Cliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario


# Los 7 endpoints de cliente individual, todos detrás de CanViewClientAnalytics.
ENDPOINTS = [
    'client-summary',
    'client-spending',
    'client-patterns',
    'client-alerts',
    'client-products',
    'client-services',
    'client-behavior',
]


def hacer_centro(nombre):
    centro = CentroEstetica.objects.create(
        nombre=nombre, telefono='1', email=f'{nombre}@test.local',
    )
    sucursal = Sucursal.objects.create(
        centro_estetica=centro, nombre=f'Suc {nombre}', direccion='x',
        telefono='1', ciudad='CABA', provincia='CABA',
    )
    return centro, sucursal


def hacer_cliente(centro):
    return Cliente.objects.create(
        centro_estetica=centro, nombre='Ana', apellido='Gómez', telefono='11',
    )


def api_de(centro, sucursal, rol='ADMIN'):
    usuario = Usuario.objects.create_user(
        username=f'u-{centro.pk}-{rol}', password='x',
        rol=rol, centro_estetica=centro, sucursal=sucursal,
    )
    api = APIClient()
    api.force_authenticate(user=usuario)
    return api


@pytest.mark.django_db
class TestAislamientoAnalyticsCliente:
    """Un centro no puede leer analytics de clientes de otro centro."""

    def _centros(self):
        """Dos centros distintos; el cliente objetivo pertenece al centro B."""
        centro_a, suc_a = hacer_centro('A')
        centro_b, suc_b = hacer_centro('B')
        cliente_b = hacer_cliente(centro_b)
        return (centro_a, suc_a), (centro_b, suc_b), cliente_b

    def test_admin_no_ve_cliente_de_otro_centro(self):
        """La regresión concreta: el ADMIN ya no pasa sin check de centro."""
        (centro_a, suc_a), _, cliente_b = self._centros()
        api = api_de(centro_a, suc_a, rol='ADMIN')

        for nombre in ENDPOINTS:
            url = reverse(nombre, kwargs={'cliente_id': cliente_b.id})
            resp = api.get(url)
            assert resp.status_code == status.HTTP_403_FORBIDDEN, (
                f'{nombre} dejó pasar a un ADMIN de otro centro (IDOR) '
                f'con status {resp.status_code}'
            )

    def test_manager_no_ve_cliente_de_otro_centro(self):
        (centro_a, suc_a), _, cliente_b = self._centros()
        api = api_de(centro_a, suc_a, rol='MANAGER')

        for nombre in ENDPOINTS:
            url = reverse(nombre, kwargs={'cliente_id': cliente_b.id})
            assert api.get(url).status_code == status.HTTP_403_FORBIDDEN, nombre

    def test_empleado_no_ve_cliente_de_otro_centro(self):
        (centro_a, suc_a), _, cliente_b = self._centros()
        api = api_de(centro_a, suc_a, rol='EMPLEADO')

        for nombre in ENDPOINTS:
            url = reverse(nombre, kwargs={'cliente_id': cliente_b.id})
            assert api.get(url).status_code == status.HTTP_403_FORBIDDEN, nombre

    def test_admin_si_ve_cliente_de_su_propio_centro(self):
        """El fix no debe sobre-bloquear: el acceso legítimo sigue vivo."""
        (centro_a, suc_a), _, _ = self._centros()
        cliente_a = hacer_cliente(centro_a)
        api = api_de(centro_a, suc_a, rol='ADMIN')

        for nombre in ENDPOINTS:
            url = reverse(nombre, kwargs={'cliente_id': cliente_a.id})
            resp = api.get(url)
            # Nos interesa el límite de autorización: la permission class deja
            # pasar al dueño del dato. Lo que la vista devuelva (datos vacíos,
            # etc.) es otro contrato y no se testea acá.
            assert resp.status_code != status.HTTP_403_FORBIDDEN, (
                f'{nombre} bloqueó a un ADMIN sobre un cliente de su propio '
                f'centro con status {resp.status_code}'
            )

"""
Datos de personas que el sistema no guarda, a propósito.

Se sacaron el 17/10/2026 porque ningún flujo los usaba: cada dato sensible que
se guarda es uno más que proteger, y la política de privacidad ya promete que no
están. Si alguno vuelve, que sea a propósito: este test obliga a pasar por acá.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.clientes.models import Cliente, HistorialCliente
from apps.empleados.models import CentroEstetica, Usuario


@pytest.mark.parametrize('modelo, campo', [
    (Cliente, 'foto'),
    (Cliente, 'tipo_documento'),
    (Cliente, 'numero_documento'),
    (HistorialCliente, 'foto_antes'),
    (HistorialCliente, 'foto_despues'),
    (Usuario, 'foto'),
])
def test_no_se_guarda_el_campo(modelo, campo):
    assert campo not in {f.name for f in modelo._meta.get_fields()}


@pytest.mark.django_db
def test_la_api_ignora_un_documento_que_venga_en_el_pedido():
    centro = CentroEstetica.objects.create(nombre='AME', telefono='1', email='ame@test.local')
    staff = Usuario.objects.create_user(
        username='staff', password='x', centro_estetica=centro, rol=Usuario.Rol.EMPLEADO,
    )
    api = APIClient()
    api.force_authenticate(staff)

    resp = api.post(reverse('cliente-list'), {
        'nombre': 'Martina', 'apellido': 'Paz', 'telefono': '1155667788',
        'tipo_documento': 'DNI', 'numero_documento': '30111222',
    }, format='json')

    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    assert 'numero_documento' not in resp.data
    assert 'tipo_documento' not in resp.data

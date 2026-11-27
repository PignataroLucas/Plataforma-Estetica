"""
Aceptación de la política de privacidad y sus páginas públicas.

Lo que se cuida es que no haya forma de tener una cuenta sin constancia de que
aceptó la versión vigente: ni registrándose sin la casilla, ni habiéndose
registrado antes de que existiera, ni cuando la política cambia.
"""
from dataclasses import replace
from datetime import date
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.client_api.tokens import tokens_para_usuario_cliente
from apps.clientes.models import UsuarioCliente
from apps.empleados.models import CentroEstetica
from apps.legales import documentos
from apps.legales.models import AceptacionLegal

VIGENTE = documentos.PRIVACIDAD.version.isoformat()


@pytest.fixture(autouse=True)
def sin_cache(settings):
    """Las páginas se cachean una hora; entre tests no puede quedar la anterior."""
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@pytest.fixture(autouse=True)
def sin_throttle(settings):
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        'DEFAULT_THROTTLE_RATES': {
            **settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], 'cliente_registro': None,
        },
    }


@pytest.fixture
def centro(db):
    return CentroEstetica.objects.create(nombre='Centro A', telefono='1111', email='a@centro.com')


@pytest.fixture
def cuenta_vieja(db):
    """Creada antes de que existiera la casilla: no tiene ninguna constancia."""
    return UsuarioCliente.objects.create_user(email='vieja@mail.com', password='ClaveSegura123')


def con_sesion(cuenta):
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens_para_usuario_cliente(cuenta)['access']}")
    return api


def registrar(centro, **extra):
    datos = {
        'email': 'nueva@mail.com', 'password': 'ClaveSegura123',
        'nombre': 'Ana', 'apellido': 'Gómez', 'centro': centro.id, **extra,
    }
    return APIClient().post(reverse('client-registro'), datos, format='json')


def pendientes(api):
    return api.get(reverse('client-perfil')).data['legales_pendientes']


class TestRegistro:
    def test_sin_la_casilla_no_hay_cuenta(self, centro):
        resp = registrar(centro)

        assert resp.status_code == 400
        assert 'acepta_privacidad' in resp.data
        assert not UsuarioCliente.objects.filter(email='nueva@mail.com').exists()

    def test_con_la_casilla_destildada_no_hay_cuenta(self, centro):
        resp = registrar(centro, acepta_privacidad=False)

        assert resp.status_code == 400
        assert not UsuarioCliente.objects.filter(email='nueva@mail.com').exists()

    def test_con_la_casilla_queda_la_constancia_de_la_version_vigente(self, centro):
        resp = registrar(centro, acepta_privacidad=True)

        assert resp.status_code == 201
        constancia = AceptacionLegal.objects.get(usuario_cliente__email='nueva@mail.com')
        assert constancia.documento == 'PRIVACIDAD'
        assert constancia.version == documentos.PRIVACIDAD.version
        assert resp.data['usuario']['legales_pendientes'] == []


class TestCuentaSinConstancia:
    def test_el_perfil_la_marca_como_pendiente(self, cuenta_vieja):
        assert pendientes(con_sesion(cuenta_vieja)) == [{
            'documento': 'PRIVACIDAD',
            'titulo': 'Política de privacidad',
            'version': VIGENTE,
            'ruta': '/legales/privacidad/',
        }]

    def test_al_aceptar_deja_de_estar_pendiente(self, cuenta_vieja):
        api = con_sesion(cuenta_vieja)
        resp = api.post(reverse('client-aceptar-legal'),
                        {'documento': 'PRIVACIDAD', 'version': VIGENTE}, format='json')

        assert resp.status_code == 200
        assert resp.data['legales_pendientes'] == []
        assert pendientes(api) == []

    def test_aceptar_dos_veces_deja_una_sola_constancia(self, cuenta_vieja):
        api = con_sesion(cuenta_vieja)
        for _ in range(2):
            api.post(reverse('client-aceptar-legal'),
                     {'documento': 'PRIVACIDAD', 'version': VIGENTE}, format='json')

        assert AceptacionLegal.objects.filter(usuario_cliente=cuenta_vieja).count() == 1

    def test_no_se_acepta_una_version_que_no_es_la_vigente(self, cuenta_vieja):
        """Si la política cambió con la pantalla abierta, tiene que leer la nueva."""
        api = con_sesion(cuenta_vieja)
        resp = api.post(reverse('client-aceptar-legal'),
                        {'documento': 'PRIVACIDAD', 'version': '2020-01-01'}, format='json')

        assert resp.status_code == 400
        assert pendientes(api) != []

    def test_no_se_acepta_un_documento_desconocido(self, cuenta_vieja):
        resp = con_sesion(cuenta_vieja).post(
            reverse('client-aceptar-legal'),
            {'documento': 'CUALQUIERA', 'version': VIGENTE}, format='json',
        )
        assert resp.status_code == 400

    def test_sin_sesion_no_se_puede(self, db):
        resp = APIClient().post(reverse('client-aceptar-legal'),
                                {'documento': 'PRIVACIDAD', 'version': VIGENTE}, format='json')
        assert resp.status_code == 401


def test_cuando_la_politica_cambia_hay_que_volver_a_aceptarla(cuenta_vieja):
    api = con_sesion(cuenta_vieja)
    api.post(reverse('client-aceptar-legal'),
             {'documento': 'PRIVACIDAD', 'version': VIGENTE}, format='json')

    nueva = replace(documentos.PRIVACIDAD, version=date(2027, 1, 15))
    with patch.object(documentos, 'A_ACEPTAR', (nueva,)):
        assert [p['version'] for p in pendientes(api)] == ['2027-01-15']


class TestPaginasPublicas:
    def test_la_politica_se_ve_sin_sesion(self, db):
        resp = APIClient().get(reverse('legales-privacidad'))

        assert resp.status_code == 200
        html = resp.content.decode()
        assert 'Política de privacidad' in html
        assert documentos.fecha_larga(documentos.PRIVACIDAD.version) in html

    def test_las_notas_de_revision_no_se_publican(self, db):
        html = APIClient().get(reverse('legales-privacidad')).content.decode()

        assert 'Para la revisión' not in html
        assert '[FECHA]' not in html

    def test_la_pagina_de_eliminar_la_cuenta_se_ve_sin_sesion(self, db):
        resp = APIClient().get(reverse('legales-eliminar-cuenta'))

        assert resp.status_code == 200
        assert 'Eliminar mi cuenta' in resp.content.decode()

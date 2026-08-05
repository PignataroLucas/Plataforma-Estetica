"""
Tests for the integration API.

The isolation tests here cover the view layer, which is where multi-tenancy is
enforced in this project: an admin of one center must not be able to see or
touch another center's integration, or point their own at someone else's branch.
"""
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.empleados.models import Usuario
from apps.integraciones.models import ContoIntegration, ContoSale

from .test_services import fake_response, make_center


def make_admin(center, username='admin'):
    return Usuario.objects.create_user(
        username=username, password='x', rol='ADMIN',
        centro_estetica=center, sucursal=center.sucursales.first(),
    )


def make_user(center, rol, username):
    return Usuario.objects.create_user(
        username=username, password='x', rol=rol,
        centro_estetica=center, sucursal=center.sucursales.first(),
    )


def api(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


LIST_URL = reverse('conto-integration-list')


def detail_url(pk):
    return reverse('conto-integration-detail', args=[pk])


def action_url(name, pk):
    return reverse(f'conto-integration-{name}', args=[pk])


# --------------------------------------------------------------------------- #
# Permissions
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestPermissions:

    def test_anonymous_is_rejected(self):
        assert api().get(LIST_URL).status_code == 401

    @pytest.mark.parametrize('rol', ['EMPLEADO', 'MANAGER'])
    def test_non_admin_roles_are_rejected(self, rol):
        center, _, _ = make_center('A', 'cnt_aaa')
        user = make_user(center, rol, f'user_{rol}')

        assert api(user).get(LIST_URL).status_code == 403

    def test_admin_is_allowed(self):
        center, _, _ = make_center('A', 'cnt_aaa')
        admin = make_admin(center)

        assert api(admin).get(LIST_URL).status_code == 200


# --------------------------------------------------------------------------- #
# Tenant isolation
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestTenantIsolation:

    def test_admin_only_sees_their_own_integration(self):
        center_a, _, integration_a = make_center('A', 'cnt_aaa')
        make_center('B', 'cnt_bbb')
        admin = make_admin(center_a)

        response = api(admin).get(LIST_URL)
        returned = response.json().get('results', response.json())

        assert [item['id'] for item in returned] == [integration_a.pk]

    def test_another_centers_integration_is_not_reachable(self):
        center_a, _, _ = make_center('A', 'cnt_aaa')
        _, _, integration_b = make_center('B', 'cnt_bbb')
        admin = make_admin(center_a)

        assert api(admin).get(detail_url(integration_b.pk)).status_code == 404
        assert api(admin).patch(
            detail_url(integration_b.pk), {'is_active': True}, format='json'
        ).status_code == 404

    def test_center_comes_from_the_user_not_the_payload(self):
        """Sending another center's id must not move the integration there."""
        center_a, branch_a, integration_a = make_center('A', 'cnt_aaa')
        center_b, _, integration_b = make_center('B', 'cnt_bbb')
        integration_a.delete()  # el centro A queda libre para crear
        admin = make_admin(center_a)

        response = api(admin).post(LIST_URL, {
            'center': center_b.pk,
            'branch': branch_a.pk,
            'base_url': 'https://conto.test',
            'token': 'secreto',
        }, format='json')

        assert response.status_code == 201
        created = ContoIntegration.objects.get(pk=response.json()['id'])
        assert created.center == center_a

    def test_branch_of_another_center_is_rejected(self):
        center_a, _, integration_a = make_center('A', 'cnt_aaa')
        _, branch_b, _ = make_center('B', 'cnt_bbb')
        integration_a.delete()
        admin = make_admin(center_a)

        response = api(admin).post(LIST_URL, {
            'branch': branch_b.pk,
            'base_url': 'https://conto.test',
            'token': 'secreto',
        }, format='json')

        assert response.status_code == 400
        assert 'branch' in response.json()

    def test_vouchers_are_scoped_to_the_center(self):
        center_a, _, integration_a = make_center('A', 'cnt_aaa')
        _, _, integration_b = make_center('B', 'cnt_bbb')
        admin = make_admin(center_a)

        ContoSale.objects.create(
            integration=integration_a, voucher_id='A-1',
            channel='tiendanube', payload={},
        )
        ContoSale.objects.create(
            integration=integration_b, voucher_id='B-1',
            channel='tiendanube', payload={},
        )

        response = api(admin).get(reverse('conto-sale-list'))
        returned = response.json().get('results', response.json())

        assert [v['voucher_id'] for v in returned] == ['A-1']


# --------------------------------------------------------------------------- #
# Token handling
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestToken:

    def test_token_is_never_returned(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        admin = make_admin(center)

        body = api(admin).get(detail_url(integration.pk)).json()

        assert 'token' not in body
        assert body['token_configurado'] is True

    def test_token_can_be_updated_without_being_read_back(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        admin = make_admin(center)

        response = api(admin).patch(
            detail_url(integration.pk), {'token': 'token-nuevo'}, format='json'
        )

        assert response.status_code == 200
        assert 'token' not in response.json()
        integration.refresh_from_db()
        assert integration.token == 'token-nuevo'


# --------------------------------------------------------------------------- #
# Activation guard
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestActivation:

    def test_cannot_activate_before_verifying(self):
        """Activating unverified would leave the account tripwire with nothing
        to compare against."""
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        integration.is_active = False
        integration.save()
        admin = make_admin(center)

        response = api(admin).patch(
            detail_url(integration.pk), {'is_active': True}, format='json'
        )

        assert response.status_code == 400
        assert 'is_active' in response.json()

    def test_can_activate_once_verified(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.is_active = False
        integration.link_verified_at = timezone.now()
        integration.save()
        admin = make_admin(center)

        response = api(admin).patch(
            detail_url(integration.pk), {'is_active': True}, format='json'
        )

        assert response.status_code == 200
        integration.refresh_from_db()
        assert integration.is_active is True


# --------------------------------------------------------------------------- #
# Verifying the link
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestVerify:

    def test_verifying_stores_what_conto_answers(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        integration.save()
        admin = make_admin(center)

        with patch('requests.Session.request') as request:
            request.return_value = fake_response(payload={
                'cuenta_id': 'cnt_real', 'nombre': 'AME Centro', 'activa': True,
            })
            response = api(admin).post(action_url('verificar', integration.pk))

        assert response.status_code == 200
        integration.refresh_from_db()
        assert integration.conto_account_id == 'cnt_real'
        assert integration.conto_account_name == 'AME Centro'
        assert integration.link_verified_at is not None

    def test_a_different_account_requires_explicit_confirmation(self):
        """
        Re-linking to another account is the scenario the isolation rules exist
        to prevent, so it cannot happen by accident.
        """
        center, _, integration = make_center('A', 'cnt_aaa')
        admin = make_admin(center)

        with patch('requests.Session.request') as request:
            request.return_value = fake_response(payload={
                'cuenta_id': 'cnt_OTRA', 'nombre': 'Otro Negocio', 'activa': True,
            })
            response = api(admin).post(action_url('verificar', integration.pk))

        assert response.status_code == 409
        assert response.json()['requiere_confirmacion'] is True
        integration.refresh_from_db()
        assert integration.conto_account_id == 'cnt_aaa'  # sin cambios

    def test_confirmed_account_change_goes_through(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        admin = make_admin(center)

        with patch('requests.Session.request') as request:
            request.return_value = fake_response(payload={
                'cuenta_id': 'cnt_OTRA', 'nombre': 'Otro Negocio', 'activa': True,
            })
            response = api(admin).post(
                action_url('verificar', integration.pk),
                {'confirmar_cambio_de_cuenta': True}, format='json'
            )

        assert response.status_code == 200
        integration.refresh_from_db()
        assert integration.conto_account_id == 'cnt_OTRA'

    def test_a_revoked_token_reports_the_error(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        admin = make_admin(center)

        with patch('requests.Session.request') as request:
            request.return_value = fake_response(status=401)
            response = api(admin).post(action_url('verificar', integration.pk))

        assert response.status_code == 400
        assert response.json()['success'] is False
        assert '401' in response.json()['error']

    def test_a_response_without_account_id_is_rejected(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        integration.save()
        admin = make_admin(center)

        with patch('requests.Session.request') as request:
            request.return_value = fake_response(payload={'nombre': 'AME'})
            response = api(admin).post(action_url('verificar', integration.pk))

        assert response.status_code == 400
        integration.refresh_from_db()
        assert integration.conto_account_id is None


# --------------------------------------------------------------------------- #
# Status and alerts
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestStatus:

    def codes(self, body):
        return {alert['codigo'] for alert in body['alertas']}

    def test_unverified_integration_is_flagged(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        integration.is_active = False
        integration.save()
        admin = make_admin(center)

        body = api(admin).get(action_url('estado', integration.pk)).json()

        assert 'SIN_VINCULAR' in self.codes(body)
        assert 'INACTIVA' in self.codes(body)

    def test_stalled_sync_is_flagged(self):
        """The task runs every 15 minutes; hours of silence means it died."""
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.link_verified_at = timezone.now()
        integration.import_from = timezone.now() - timezone.timedelta(days=30)
        integration.last_sales_sync = timezone.now() - timezone.timedelta(hours=6)
        integration.save()
        admin = make_admin(center)

        body = api(admin).get(action_url('estado', integration.pk)).json()

        assert 'SINCRONIZACION_DETENIDA' in self.codes(body)

    def test_a_recent_sync_is_not_flagged(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.link_verified_at = timezone.now()
        integration.import_from = timezone.now() - timezone.timedelta(days=30)
        integration.last_sales_sync = timezone.now() - timezone.timedelta(minutes=10)
        integration.save()
        admin = make_admin(center)

        body = api(admin).get(action_url('estado', integration.pk)).json()

        assert 'SINCRONIZACION_DETENIDA' not in self.codes(body)

    def test_failed_vouchers_are_counted_and_listed(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.link_verified_at = timezone.now()
        integration.save()
        admin = make_admin(center)

        ContoSale.objects.create(
            integration=integration, voucher_id='8891', channel='tiendanube',
            payload={}, status=ContoSale.Status.ERROR,
            error_message='descuento sin líneas',
        )

        body = api(admin).get(action_url('estado', integration.pk)).json()

        assert body['vouchers']['con_error'] == 1
        assert 'VOUCHERS_CON_ERROR' in self.codes(body)
        assert body['ultimos_errores'][0]['voucher_id'] == '8891'

    def test_missing_start_date_is_flagged(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.link_verified_at = timezone.now()
        integration.import_from = None
        integration.save()
        admin = make_admin(center)

        body = api(admin).get(action_url('estado', integration.pk)).json()

        assert 'SIN_FECHA_DE_INICIO' in self.codes(body)


# --------------------------------------------------------------------------- #
# Manual trigger
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestManualSync:

    def test_it_refuses_when_not_ready(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        integration.save()
        admin = make_admin(center)

        response = api(admin).post(action_url('sincronizar', integration.pk))

        assert response.status_code == 400

    def test_it_runs_inline_and_returns_the_result(self):
        """
        No Celery worker is deployed, so this runs synchronously. The upside is
        that the response carries the outcome instead of the UI having to poll.
        """
        from .test_sync import make_syncable_center, product_line, voucher
        from .test_services import make_product

        center, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')
        admin = make_admin(center)

        payload = {
            'cuenta_id': 'cnt_aaa',
            'next': None,
            'results': [voucher(items=[product_line()])],
        }
        with patch('requests.Session.request') as request:
            request.return_value = fake_response(payload=payload)
            response = api(admin).post(
                action_url('sincronizar', integration.pk), {'que': 'ventas'},
                format='json'
            )

        assert response.status_code == 200
        assert response.json()['success'] is True
        assert '1 procesadas' in response.json()['resultados']['ventas']

    def test_a_revoked_token_is_reported_not_swallowed(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.link_verified_at = timezone.now()
        integration.import_from = timezone.now() - timezone.timedelta(days=30)
        integration.save()
        admin = make_admin(center)

        with patch('requests.Session.request') as request:
            request.return_value = fake_response(status=401)
            response = api(admin).post(action_url('sincronizar', integration.pk))

        assert response.status_code == 400
        assert response.json()['success'] is False

    def test_an_unknown_target_is_rejected(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        integration.link_verified_at = timezone.now()
        integration.save()
        admin = make_admin(center)

        response = api(admin).post(
            action_url('sincronizar', integration.pk), {'que': 'cualquiera'},
            format='json'
        )

        assert response.status_code == 400


# --------------------------------------------------------------------------- #
# Reprocessing
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestReprocess:

    def url(self, pk):
        return reverse('conto-sale-reprocesar', args=[pk])

    def test_an_already_processed_voucher_is_left_alone(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        admin = make_admin(center)
        sale = ContoSale.objects.create(
            integration=integration, voucher_id='8891', channel='tiendanube',
            payload={}, status=ContoSale.Status.PROCESSED,
        )

        response = api(admin).post(self.url(sale.pk))

        assert response.status_code == 200
        assert 'no se hizo nada' in response.json()['mensaje']

    def test_a_failed_voucher_is_retried_from_its_payload(self):
        """
        The stored payload is what makes this possible without calling Conto.
        """
        from apps.finanzas.models import Transaction

        from .test_services import make_product
        from .test_sync import make_syncable_center, product_line, voucher

        center, branch, integration = make_syncable_center('A', 'cnt_aaa')
        admin = make_admin(center)
        make_product(branch, 'SER-VITC-30')

        payload = voucher(items=[product_line()])
        sale = ContoSale.objects.create(
            integration=integration, voucher_id=payload['id'],
            channel=payload['canal'], payload=payload,
            status=ContoSale.Status.ERROR, error_message='fallo anterior',
        )

        response = api(admin).post(self.url(sale.pk))

        assert response.status_code == 200
        assert response.json()['success'] is True
        sale.refresh_from_db()
        assert sale.status == ContoSale.Status.PROCESSED
        assert Transaction.objects.count() == 1

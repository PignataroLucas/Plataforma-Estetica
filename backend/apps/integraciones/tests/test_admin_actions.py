"""
Tests for the Django admin actions.

Until the frontend screen exists, the admin is the only way to verify a link and
trigger a sync, so these are the paths that will actually get used first.
"""
from unittest.mock import Mock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages import ERROR, SUCCESS
from django.utils import timezone

from apps.finanzas.models import Transaction
from apps.integraciones.admin import ContoIntegrationAdmin
from apps.integraciones.models import ContoIntegration

from .test_services import fake_response, make_center, make_product
from .test_sync import make_syncable_center, product_line, voucher


def run_action(action_name, integration, responses=None):
    """
    Invoke an admin action and capture the messages it produced.

    Returns the list of (message, level) pairs.
    """
    admin = ContoIntegrationAdmin(ContoIntegration, AdminSite())
    captured = []
    admin.message_user = lambda request, message, level=None, **kw: captured.append(
        (message, level)
    )

    queryset = ContoIntegration.objects.filter(pk=integration.pk)
    action = getattr(admin, action_name)

    if responses is None:
        action(Mock(), queryset)
    else:
        with patch('requests.Session.request', side_effect=responses):
            action(Mock(), queryset)

    return captured


def account_response(cuenta_id='cnt_aaa', nombre='AME Centro', activa=True):
    return fake_response(payload={
        'cuenta_id': cuenta_id, 'nombre': nombre, 'activa': activa,
    })


@pytest.mark.django_db
class TestVerificarVinculacion:

    def test_it_stores_what_conto_answers(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        integration.save()

        messages = run_action(
            'verificar_vinculacion', integration, [account_response()]
        )

        integration.refresh_from_db()
        assert integration.conto_account_id == 'cnt_aaa'
        assert integration.conto_account_name == 'AME Centro'
        assert integration.link_verified_at is not None
        assert messages[0][1] == SUCCESS
        assert 'AME Centro' in messages[0][0]

    def test_it_refuses_to_relink_to_another_account(self):
        """
        An admin action has nowhere to ask for confirmation, so re-linking has to
        go through the API endpoint with its explicit flag.
        """
        _, _, integration = make_center('A', 'cnt_aaa')

        messages = run_action(
            'verificar_vinculacion', integration,
            [account_response(cuenta_id='cnt_OTRA')]
        )

        integration.refresh_from_db()
        assert integration.conto_account_id == 'cnt_aaa'  # sin cambios
        assert messages[0][1] == ERROR
        assert 'cnt_OTRA' in messages[0][0]

    def test_a_revoked_token_reports_an_error(self):
        _, _, integration = make_center('A', 'cnt_aaa')

        messages = run_action(
            'verificar_vinculacion', integration, [fake_response(status=401)]
        )

        assert messages[0][1] == ERROR
        assert '401' in messages[0][0]

    def test_an_inactive_account_warns_instead_of_confirming(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        integration.save()

        messages = run_action(
            'verificar_vinculacion', integration,
            [account_response(activa=False)]
        )

        integration.refresh_from_db()
        assert integration.conto_account_id == 'cnt_aaa'
        assert 'desactivada' in messages[0][0]


@pytest.mark.django_db
class TestSyncActions:

    def test_importar_ventas_creates_the_transactions(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        sales = fake_response(payload={
            'cuenta_id': 'cnt_aaa', 'next': None,
            'results': [voucher(items=[product_line()])],
        })
        messages = run_action('importar_ventas', integration, [sales])

        assert Transaction.objects.count() == 1
        assert messages[0][1] == SUCCESS
        assert '1 procesadas' in messages[0][0]

    def test_sincronizar_stock_reports_its_summary(self):
        _, _, integration = make_syncable_center('A', 'cnt_aaa')

        stock = fake_response(payload={
            'cuenta_id': 'cnt_aaa', 'next': None,
            'results': [{'sku': 'NUEVO', 'nombre': 'Nuevo', 'stock': 5,
                         'costo': '10.00', 'precio': '20.00', 'activo': True}],
        })
        messages = run_action('sincronizar_stock', integration, [stock])

        assert messages[0][1] == SUCCESS
        assert '1 creados' in messages[0][0]

    def test_an_unverified_integration_is_refused(self):
        """`can_sync` requires a verified link; nothing should be attempted."""
        _, _, integration = make_center('A', 'cnt_aaa')
        integration.link_verified_at = None
        integration.save()

        messages = run_action('importar_ventas', integration)

        assert 'vinculada y activa' in messages[0][0]
        assert Transaction.objects.count() == 0

    def test_a_transport_error_is_reported_not_raised(self):
        _, branch, integration = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        messages = run_action(
            'importar_ventas', integration, [fake_response(status=500)]
        )

        assert messages[0][1] == ERROR
        assert Transaction.objects.count() == 0

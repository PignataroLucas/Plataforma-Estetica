"""
Tests for the `sincronizar_conto` command.

This is the path that actually runs in production, since Celery is not deployed,
so its failure behaviour matters: a scheduler has to be able to tell a real
problem from a quiet run.
"""
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoIntegration

from .test_services import fake_response, make_product
from .test_sync import make_syncable_center, product_line, voucher


def dispatcher(account='cnt_aaa', sales=None, stock=None, account_status=200):
    """Mocked transport that answers by URL."""
    def dispatch(*args, **kwargs):
        url = args[1] if len(args) > 1 else kwargs.get('url', '')
        if '/api/cuenta/' in url:
            if account_status != 200:
                return fake_response(status=account_status)
            return fake_response(payload={
                'cuenta_id': account, 'nombre': 'AME', 'activa': True,
            })
        if '/api/ventas/' in url:
            return fake_response(payload={
                'cuenta_id': account, 'next': None, 'results': sales or [],
            })
        if '/api/stock/' in url:
            return fake_response(payload={
                'cuenta_id': account, 'next': None, 'results': stock or [],
            })
        raise AssertionError(f'URL inesperada: {url}')
    return dispatch


def run(dispatch, **options):
    out = StringIO()
    with patch('requests.Session.request', side_effect=dispatch):
        call_command('sincronizar_conto', stdout=out, **options)
    return out.getvalue()


@pytest.mark.django_db
class TestCommand:

    def test_no_integrations_is_not_an_error(self):
        """A scheduler should not alarm because nothing is configured yet."""
        out = StringIO()
        call_command('sincronizar_conto', stdout=out)
        assert 'Nada que hacer' in out.getvalue()

    def test_it_imports_sales(self):
        _, branch, _ = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        output = run(dispatcher(sales=[voucher(items=[product_line()])]))

        assert 'Vínculo: OK' in output
        assert '1 procesadas' in output
        assert Transaction.objects.count() == 1

    def test_inactive_integrations_are_ignored(self):
        _, _, integration = make_syncable_center('A', 'cnt_aaa')
        integration.is_active = False
        integration.save()

        out = StringIO()
        call_command('sincronizar_conto', stdout=out)

        assert 'Nada que hacer' in out.getvalue()

    def test_a_crossed_account_deactivates_and_fails(self):
        """
        Fails closed: importing here would write another business's sales into
        this tenant.
        """
        _, _, integration = make_syncable_center('A', 'cnt_aaa')

        with pytest.raises(CommandError, match='cnt_OTRA'):
            run(dispatcher(account='cnt_OTRA'))

        integration.refresh_from_db()
        assert integration.is_active is False
        assert Transaction.objects.count() == 0

    def test_a_revoked_token_fails_the_run(self):
        """Non-zero exit is what makes a scheduler report it."""
        make_syncable_center('A', 'cnt_aaa')

        with pytest.raises(CommandError):
            run(dispatcher(account_status=401))

    def test_it_does_not_sync_after_a_link_problem(self):
        _, branch, _ = make_syncable_center('A', 'cnt_aaa')
        make_product(branch, 'SER-VITC-30')

        with pytest.raises(CommandError):
            run(dispatcher(
                account='cnt_OTRA', sales=[voucher(items=[product_line()])]
            ))

        assert Transaction.objects.count() == 0

    def test_todo_runs_stock_and_sales(self):
        _, branch, _ = make_syncable_center('A', 'cnt_aaa')

        output = run(
            dispatcher(
                stock=[{'sku': 'NUEVO', 'nombre': 'Nuevo', 'stock': 5,
                        'costo': '10.00', 'precio': '20.00', 'activo': True}],
                sales=[],
            ),
            que='todo',
        )

        assert 'Stock:' in output
        assert 'Ventas:' in output
        assert '1 creados' in output

    def test_one_broken_integration_does_not_silence_the_others(self):
        """A revoked token in one center must not stop another center's import."""
        _, branch_a, integration_a = make_syncable_center('A', 'cnt_aaa')
        _, branch_b, integration_b = make_syncable_center('B', 'cnt_bbb')
        make_product(branch_a, 'SER-VITC-30')
        make_product(branch_b, 'SER-VITC-30')

        def dispatch(*args, **kwargs):
            url = args[1] if len(args) > 1 else kwargs.get('url', '')
            token = kwargs.get('headers', {}).get('Authorization', '')
            # Center A's token resolves to the wrong account.
            account = 'cnt_OTRA' if 'cnt_aaa' in token else 'cnt_bbb'
            if '/api/cuenta/' in url:
                return fake_response(payload={
                    'cuenta_id': account, 'nombre': 'X', 'activa': True,
                })
            return fake_response(payload={
                'cuenta_id': account, 'next': None,
                'results': [voucher(items=[product_line()])],
            })

        with pytest.raises(CommandError):
            run(dispatch)

        # B imported despite A being broken.
        assert Transaction.objects.filter(branch=branch_b).count() == 1
        assert Transaction.objects.filter(branch=branch_a).count() == 0

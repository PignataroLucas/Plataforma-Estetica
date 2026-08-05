"""
Tests for the `verificar_conto` contract check.

The command is what tells both sides whether Conto's implementation matches the
agreed contract, so a false "everything is fine" would be worse than no check
at all.
"""
from io import StringIO
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from .test_services import fake_response, make_center


def linked_integration():
    _, _, integration = make_center('A', 'cnt_aaa')
    integration.link_verified_at = timezone.now()
    integration.save()
    return integration


def good_account():
    return {'cuenta_id': 'cnt_aaa', 'nombre': 'AME Centro de Estética', 'activa': True}


def good_stock():
    return {
        'cuenta_id': 'cnt_aaa',
        'next': None,
        'results': [{
            'sku': 'SER-VITC-30', 'nombre': 'Serum Vitamina C 30ml',
            'stock': 12, 'costo': '9200.00', 'precio': '18500.00',
            'activo': True, 'actualizado_en': '2026-08-04T14:22:10Z',
        }],
    }


def good_sales():
    return {
        'cuenta_id': 'cnt_aaa',
        'next': None,
        'results': [{
            'id': '8891', 'tipo': 'VENTA', 'relacionada_con': None,
            'canal': 'tiendanube', 'orden_externa_id': 'TN-12345',
            'fecha': '2026-08-04', 'actualizado_en': '2026-08-04T14:22:10Z',
            'estado': 'PAGADO', 'medio_pago': 'card',
            'gateway_origen': 'mercadopago', 'total': '21500.00',
            'cliente': {'nombre': 'Ana Gómez', 'email': 'ana@ejemplo.com',
                        'telefono': '+5491133334444'},
            'items': [
                {'tipo': 'PRODUCTO', 'sku': 'SER-VITC-30', 'nombre': 'Serum',
                 'cantidad': 1, 'precio_unitario': '18500.00',
                 'costo_unitario': '9200.00'},
                {'tipo': 'ENVIO', 'sku': None, 'nombre': 'Envío',
                 'cantidad': 1, 'precio_unitario': '3000.00'},
            ],
        }],
    }


def run_command(responses, endpoints_open=False):
    """
    Run the command with a mocked HTTP transport and return its output.

    Dispatches on URL and on the token rather than on call order, so adding new
    checks to the command does not break every test here.

    `endpoints_open` simulates a Conto that answers without a valid token, which
    is the failure the auth check exists to catch.
    """
    account, stock, sales = responses

    def dispatch(*args, **kwargs):
        url = args[1] if len(args) > 1 else kwargs.get('url', '')
        token = kwargs.get('headers', {}).get('Authorization', '')

        if 'invalido' in token and not endpoints_open:
            return fake_response(status=401)

        if '/api/cuenta/' in url:
            return fake_response(payload=account)
        if '/api/stock/' in url:
            return fake_response(payload=stock)
        if '/api/ventas/' in url:
            return fake_response(payload=sales)
        raise AssertionError(f'URL inesperada: {url}')

    out = StringIO()
    with patch('requests.Session.request', side_effect=dispatch):
        call_command('verificar_conto', stdout=out)
    return out.getvalue()


@pytest.mark.django_db
class TestContractPasses:

    def test_a_compliant_instance_reports_no_failures(self):
        linked_integration()

        output = run_command([good_account(), good_stock(), good_sales()])

        assert 'Todos los requisitos bloqueantes se cumplen' in output
        assert 'FALLA' not in output

    def test_it_surfaces_the_actual_enum_values(self):
        """The point is to confirm the enums against the spec, not guess them."""
        linked_integration()

        output = run_command([good_account(), good_stock(), good_sales()])

        assert "'tiendanube'" in output
        assert "'PAGADO'" in output
        assert "'PRODUCTO'" in output
        assert "'ENVIO'" in output


@pytest.mark.django_db
class TestContractFails:

    def test_missing_account_id_in_a_listing_is_a_failure(self):
        """Without it there is nothing to validate the isolation against."""
        linked_integration()
        stock = good_stock()
        del stock['cuenta_id']

        output = run_command([good_account(), stock, good_sales()])

        assert 'FALLA' in output
        assert 'cuenta_id' in output
        assert 'sin cumplir' in output

    def test_wrong_account_is_a_failure(self):
        linked_integration()
        account = good_account()
        account['cuenta_id'] = 'cnt_OTHER'

        output = run_command([account, good_stock(), good_sales()])

        assert 'FALLA' in output
        assert 'cnt_OTHER' in output

    def test_datetime_instead_of_plain_date_is_a_failure(self):
        """A datetime is what causes the one-day shift read from Argentina."""
        linked_integration()
        sales = good_sales()
        sales['results'][0]['fecha'] = '2026-08-04T00:00:00Z'

        output = run_command([good_account(), good_stock(), sales])

        assert 'FALLA' in output
        assert 'YYYY-MM-DD' in output

    def test_items_without_tipo_is_a_failure(self):
        linked_integration()
        sales = good_sales()
        for item in sales['results'][0]['items']:
            del item['tipo']

        output = run_command([good_account(), good_stock(), sales])

        assert 'FALLA' in output
        assert 'tipo' in output

    def test_descending_order_is_a_failure(self):
        linked_integration()
        sales = good_sales()
        first = sales['results'][0]
        second = dict(first, id='8892', actualizado_en='2026-08-03T10:00:00Z')
        sales['results'] = [first, second]

        output = run_command([good_account(), good_stock(), sales])

        assert 'FALLA' in output
        assert 'saltear registros' in output

    def test_endpoints_open_without_a_token_is_a_failure(self):
        """
        If Conto answers a bogus token, every connected business's sales are
        public. This is the loudest thing the check can find.
        """
        linked_integration()

        output = run_command(
            [good_account(), good_stock(), good_sales()],
            endpoints_open=True,
        )

        assert 'FALLA' in output
        assert 'el endpoint está abierto' in output
        assert output.count('rechaza un token inválido') >= 3

    def test_rejecting_a_bogus_token_passes(self):
        linked_integration()

        output = run_command([good_account(), good_stock(), good_sales()])

        assert 'Todos los requisitos bloqueantes se cumplen' in output

    def test_inactive_account_is_a_failure(self):
        linked_integration()
        account = good_account()
        account['activa'] = False

        output = run_command([account, good_stock(), good_sales()])

        assert 'FALLA' in output
        assert 'inactiva' in output

    def test_unreachable_account_endpoint_stops_the_check(self):
        linked_integration()

        out = StringIO()
        with patch('requests.Session.request') as request:
            request.return_value = fake_response(status=401)
            with pytest.raises(CommandError):
                call_command('verificar_conto', stdout=out)

        assert 'FALLA' in out.getvalue()


@pytest.mark.django_db
class TestContractWarnings:

    def test_missing_next_is_a_warning_not_a_failure(self):
        linked_integration()
        stock = good_stock()
        del stock['next']

        output = run_command([good_account(), stock, good_sales()])

        assert 'AVISO' in output
        assert 'Todos los requisitos bloqueantes se cumplen' in output

    def test_missing_payment_method_is_a_warning(self):
        """Non-blocking by agreement: the default payment method covers it."""
        linked_integration()
        sales = good_sales()
        del sales['results'][0]['medio_pago']

        output = run_command([good_account(), good_stock(), sales])

        assert 'AVISO' in output
        assert 'Todos los requisitos bloqueantes se cumplen' in output


@pytest.mark.django_db
class TestCommandGuards:

    def test_it_refuses_when_there_is_no_integration(self):
        with pytest.raises(CommandError, match='No hay ninguna integración'):
            call_command('verificar_conto', stdout=StringIO())

    def test_it_refuses_when_there_is_more_than_one(self):
        linked_integration()
        _, _, other = make_center('B', 'cnt_bbb')
        other.link_verified_at = timezone.now()
        other.save()

        with pytest.raises(CommandError, match='más de una integración'):
            call_command('verificar_conto', stdout=StringIO())

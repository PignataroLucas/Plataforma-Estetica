"""
Tests for the Conto client and the tenant-scoped lookups.

The isolation tests (two centers sharing a SKU and an email) are the reason this
file exists: those are the failures that would silently mix two businesses' data
and that nobody would notice for months.
"""
from decimal import Decimal
from unittest.mock import Mock

import pytest
import requests

from apps.clientes.models import Cliente
from apps.empleados.models import CentroEstetica, Sucursal
from apps.finanzas.models import Transaction
from apps.integraciones.models import ContoIntegration
from apps.integraciones.services import (
    ContoAccountMismatch,
    ContoAuthError,
    ContoClient,
    ContoError,
    ContoNotLinked,
    ContoScope,
    ContoUnavailable,
)
from apps.inventario.models import MovimientoInventario, Producto


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def fake_response(status=200, payload=None, text=''):
    response = Mock()
    response.status_code = status
    response.json.return_value = {} if payload is None else payload
    response.text = text
    return response


def make_center(name, account_id, base_url='https://conto.test'):
    """Create a center with a branch and a linked, verified Conto integration."""
    center = CentroEstetica.objects.create(
        nombre=name, telefono='1', email=f'{account_id}@test.local'
    )
    branch = Sucursal.objects.create(
        centro_estetica=center, nombre=f'Sucursal {name}',
        direccion='x', telefono='1', ciudad='CABA', provincia='CABA',
    )
    integration = ContoIntegration.objects.create(
        center=center,
        branch=branch,
        base_url=base_url,
        token=f'token-{account_id}',
        conto_account_id=account_id,
        is_active=True,
    )
    return center, branch, integration


def make_product(branch, sku, name='Serum', stock=0, cost='9200.00', price='18500.00'):
    return Producto.objects.create(
        sucursal=branch,
        nombre=name,
        sku=sku,
        stock_actual=stock,
        precio_costo=Decimal(cost),
        precio_venta=Decimal(price),
    )


# --------------------------------------------------------------------------- #
# ContoClient
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestContoClientIsolation:
    """The account tripwire, which is what keeps two tenants from crossing."""

    def test_mismatched_account_aborts_without_yielding(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        session = Mock()
        session.request.return_value = fake_response(payload={
            'cuenta_id': 'cnt_OTHER',
            'results': [{'sku': 'X'}],
            'next': None,
        })
        client = ContoClient(integration, session=session)

        with pytest.raises(ContoAccountMismatch) as exc:
            list(client.iter_stock())

        assert 'cnt_OTHER' in str(exc.value)
        assert 'cnt_aaa' in str(exc.value)

    def test_unverified_integration_refuses_to_sync(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        integration.save(update_fields=['conto_account_id'])

        client = ContoClient(integration, session=Mock())

        with pytest.raises(ContoNotLinked):
            list(client.iter_stock())

    def test_account_check_runs_on_every_page(self):
        """A second page belonging to another account must also be caught."""
        _, _, integration = make_center('A', 'cnt_aaa')
        session = Mock()
        session.request.side_effect = [
            fake_response(payload={
                'cuenta_id': 'cnt_aaa',
                'results': [{'sku': 'A'}],
                'next': 'https://conto.test/api/stock/?page=2',
            }),
            fake_response(payload={
                'cuenta_id': 'cnt_OTHER',
                'results': [{'sku': 'B'}],
                'next': None,
            }),
        ]
        client = ContoClient(integration, session=session)

        collected = []
        with pytest.raises(ContoAccountMismatch):
            for item in client.iter_stock():
                collected.append(item)

        # The first page was legitimate, the second aborted the walk.
        assert collected == [{'sku': 'A'}]

    def test_get_account_does_not_require_a_stored_id(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        integration.conto_account_id = None
        session = Mock()
        session.request.return_value = fake_response(payload={
            'cuenta_id': 'cnt_aaa', 'nombre': 'AME', 'activa': True,
        })
        client = ContoClient(integration, session=session)

        assert client.get_account()['cuenta_id'] == 'cnt_aaa'


@pytest.mark.django_db
class TestContoClientPagination:

    def test_follows_next_across_pages(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        session = Mock()
        session.request.side_effect = [
            fake_response(payload={
                'cuenta_id': 'cnt_aaa',
                'results': [{'id': '1'}, {'id': '2'}],
                'next': 'https://conto.test/api/ventas/?page=2',
            }),
            fake_response(payload={
                'cuenta_id': 'cnt_aaa',
                'results': [{'id': '3'}],
                'next': None,
            }),
        ]
        client = ContoClient(integration, session=session)

        from django.utils import timezone
        items = list(client.iter_sales(timezone.now()))

        assert [item['id'] for item in items] == ['1', '2', '3']
        assert session.request.call_count == 2

    def test_next_pointing_elsewhere_is_rejected(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        session = Mock()
        session.request.return_value = fake_response(payload={
            'cuenta_id': 'cnt_aaa',
            'results': [{'id': '1'}],
            'next': 'https://attacker.example/api/stock/',
        })
        client = ContoClient(integration, session=session)

        with pytest.raises(ContoError, match='otro origen'):
            list(client.iter_stock())

    def test_empty_results_is_not_an_error(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        session = Mock()
        session.request.return_value = fake_response(payload={
            'cuenta_id': 'cnt_aaa', 'results': [], 'next': None,
        })
        client = ContoClient(integration, session=session)

        assert list(client.iter_stock()) == []


@pytest.mark.django_db
class TestContoClientErrors:

    @pytest.mark.parametrize('status,expected', [
        (401, ContoAuthError),
        (500, ContoUnavailable),
        (503, ContoUnavailable),
    ])
    def test_status_codes_map_to_exceptions(self, status, expected):
        _, _, integration = make_center('A', 'cnt_aaa')
        session = Mock()
        session.request.return_value = fake_response(status=status)
        client = ContoClient(integration, session=session)

        with pytest.raises(expected):
            client.get_account()

    def test_network_failure_is_retryable(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        session = Mock()
        session.request.side_effect = requests.ConnectionError('boom')
        client = ContoClient(integration, session=session)

        with pytest.raises(ContoUnavailable):
            client.get_account()

    def test_token_is_sent_as_bearer(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        session = Mock()
        session.request.return_value = fake_response(payload={'cuenta_id': 'cnt_aaa'})
        client = ContoClient(integration, session=session)

        client.get_account()

        headers = session.request.call_args.kwargs['headers']
        assert headers['Authorization'] == 'Bearer token-cnt_aaa'
        assert 'User-Agent' in headers


# --------------------------------------------------------------------------- #
# ContoScope — tenant isolation
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestScopeProductIsolation:
    """
    Two centers with the same SKU is the expected case, not an edge case: SKUs
    come from suppliers and brands.
    """

    def test_same_sku_in_two_centers_resolves_independently(self):
        _, branch_a, integration_a = make_center('A', 'cnt_aaa')
        _, branch_b, integration_b = make_center('B', 'cnt_bbb')

        product_a = make_product(branch_a, 'SER-VITC-30', name='Serum A')
        product_b = make_product(branch_b, 'SER-VITC-30', name='Serum B')

        assert ContoScope(integration_a).find_product('SER-VITC-30') == product_a
        assert ContoScope(integration_b).find_product('SER-VITC-30') == product_b

    def test_sku_present_only_in_the_other_center_is_not_found(self):
        _, _, integration_a = make_center('A', 'cnt_aaa')
        _, branch_b, _ = make_center('B', 'cnt_bbb')
        make_product(branch_b, 'ONLY-IN-B')

        assert ContoScope(integration_a).find_product('ONLY-IN-B') is None

    def test_sku_matching_is_case_and_space_insensitive(self):
        _, branch, integration = make_center('A', 'cnt_aaa')
        product = make_product(branch, 'SER-VITC-30')

        scope = ContoScope(integration)
        assert scope.find_product('  ser-vitc-30 ') == product

    def test_duplicate_skus_cannot_exist_to_be_ambiguous(self):
        """
        Ambiguity is now prevented in the database rather than handled on read:
        `unique_sku_per_sucursal` rejects a second product with the same SKU in
        the branch, comparing uppercased.

        `find_product` still returns None on multiple matches as defence in
        depth. See apps/inventario/tests/test_sku_constraint.py.
        """
        from django.db import IntegrityError, transaction

        _, branch, integration = make_center('A', 'cnt_aaa')
        make_product(branch, 'DUP', name='Primero')

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_product(branch, 'DUP', name='Segundo')

    def test_blank_sku_returns_none(self):
        _, branch, integration = make_center('A', 'cnt_aaa')
        make_product(branch, '', name='Sin SKU')

        scope = ContoScope(integration)
        assert scope.find_product('') is None
        assert scope.find_product(None) is None


@pytest.mark.django_db
class TestScopeClientIsolation:

    def test_same_email_in_two_centers_resolves_independently(self):
        center_a, _, integration_a = make_center('A', 'cnt_aaa')
        center_b, _, integration_b = make_center('B', 'cnt_bbb')

        client_a = Cliente.objects.create(
            centro_estetica=center_a, nombre='Ana', apellido='Gómez',
            email='ana@ejemplo.com', telefono='1133334444',
        )
        client_b = Cliente.objects.create(
            centro_estetica=center_b, nombre='Ana', apellido='Gómez',
            email='ana@ejemplo.com', telefono='1133334444',
        )

        assert ContoScope(integration_a).find_client(email='ana@ejemplo.com') == client_a
        assert ContoScope(integration_b).find_client(email='ana@ejemplo.com') == client_b

    def test_client_of_another_center_is_not_found(self):
        _, _, integration_a = make_center('A', 'cnt_aaa')
        center_b, _, _ = make_center('B', 'cnt_bbb')
        Cliente.objects.create(
            centro_estetica=center_b, nombre='Solo', apellido='B',
            email='solo@b.com', telefono='1199998888',
        )

        scope = ContoScope(integration_a)
        assert scope.find_client(email='solo@b.com') is None
        assert scope.find_client(phone='1199998888') is None

    def test_phone_matches_across_formats(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        client = Cliente.objects.create(
            centro_estetica=center, nombre='Ana', apellido='Gómez',
            email='', telefono='11 3333-4444',
        )

        scope = ContoScope(integration)
        assert scope.find_client(phone='+5491133334444') == client

    def test_email_wins_over_phone(self):
        center, _, integration = make_center('A', 'cnt_aaa')
        by_email = Cliente.objects.create(
            centro_estetica=center, nombre='Por', apellido='Email',
            email='ana@ejemplo.com', telefono='1100000000',
        )
        Cliente.objects.create(
            centro_estetica=center, nombre='Por', apellido='Telefono',
            email='otro@ejemplo.com', telefono='1133334444',
        )

        scope = ContoScope(integration)
        found = scope.find_client(email='ana@ejemplo.com', phone='1133334444')
        assert found == by_email

    def test_no_data_returns_none(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        scope = ContoScope(integration)
        assert scope.find_client() is None
        assert scope.find_client(email='', phone='') is None


# --------------------------------------------------------------------------- #
# ContoScope — product creation without phantom expenses
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestScopeCreateProduct:

    def test_creating_a_product_does_not_generate_a_phantom_expense(self):
        """
        Creating a Producto with stock and cost fires
        create_initial_stock_movement, which generates an ENTRADA movement and a
        purchase expense. The center did not buy this stock now — it already had
        it in Conto.
        """
        _, branch, integration = make_center('A', 'cnt_aaa')
        scope = ContoScope(integration)

        product = scope.create_product(
            sku='SER-VITC-30', name='Serum Vitamina C 30ml',
            cost=Decimal('9200.00'), price=Decimal('18500.00'), stock=12,
        )

        assert MovimientoInventario.objects.filter(producto=product).count() == 0
        assert Transaction.objects.filter(product=product).count() == 0

    def test_stock_and_prices_land_correctly(self):
        _, branch, integration = make_center('A', 'cnt_aaa')
        scope = ContoScope(integration)

        product = scope.create_product(
            sku=' ser-vitc-30 ', name='Serum',
            cost=Decimal('9200.00'), price=Decimal('18500.00'), stock=12,
        )
        product.refresh_from_db()

        assert product.sku == 'SER-VITC-30'
        assert product.stock_actual == 12
        assert product.precio_costo == Decimal('9200.00')
        assert product.precio_venta == Decimal('18500.00')
        assert product.sucursal == branch

    def test_created_product_is_findable_afterwards(self):
        _, _, integration = make_center('A', 'cnt_aaa')
        scope = ContoScope(integration)

        created = scope.create_product(
            sku='NEW-SKU', name='Nuevo',
            cost=Decimal('100.00'), price=Decimal('200.00'), stock=5,
        )

        assert scope.find_product('NEW-SKU') == created

    def test_update_stock_creates_no_movements(self):
        _, branch, integration = make_center('A', 'cnt_aaa')
        product = make_product(branch, 'SER-VITC-30', stock=0)
        scope = ContoScope(integration)

        scope.update_stock(product, stock=7, cost=Decimal('1000.00'))
        product.refresh_from_db()

        assert product.stock_actual == 7
        assert product.precio_costo == Decimal('1000.00')
        assert MovimientoInventario.objects.filter(producto=product).count() == 0

    def test_update_stock_cannot_touch_another_branch(self):
        _, _, integration_a = make_center('A', 'cnt_aaa')
        _, branch_b, _ = make_center('B', 'cnt_bbb')
        foreign = make_product(branch_b, 'SER-VITC-30', stock=1)

        # Even handed the wrong object, the branch filter prevents the write.
        ContoScope(integration_a).update_stock(foreign, stock=999)
        foreign.refresh_from_db()

        assert foreign.stock_actual == 1

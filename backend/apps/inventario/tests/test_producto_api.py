"""
Tests for SKU validation on the product API.

The database constraint blocks duplicate SKUs, but Django does not validate
UniqueConstraints built on expressions and DRF does not call full_clean(). These
tests cover the serializer check that turns what would be a 500 into a field
error.
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.inventario.models import Producto


def make_center(name):
    center = CentroEstetica.objects.create(
        nombre=name, telefono='1', email=f'{name}@test.local'
    )
    branch = Sucursal.objects.create(
        centro_estetica=center, nombre=f'Sucursal {name}',
        direccion='x', telefono='1', ciudad='CABA', provincia='CABA',
    )
    user = Usuario.objects.create_user(
        username=f'admin_{name}', password='x', rol='ADMIN',
        centro_estetica=center, sucursal=branch,
    )
    return center, branch, user


def make_product(branch, sku, name='Producto'):
    return Producto.objects.create(
        sucursal=branch, nombre=name, sku=sku,
        precio_costo=Decimal('100.00'), precio_venta=Decimal('200.00'),
    )


def api(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def payload(**overrides):
    data = {
        'nombre': 'Serum Vitamina C',
        'precio_costo': '100.00',
        'precio_venta': '200.00',
    }
    data.update(overrides)
    return data


LIST_URL = reverse('producto-list')


@pytest.mark.django_db
class TestSkuValidation:

    def test_duplicate_sku_returns_a_field_error_not_a_500(self):
        _, branch, user = make_center('A')
        make_product(branch, 'SER-VITC-30', name='El original')

        response = api(user).post(LIST_URL, payload(sku='SER-VITC-30'), format='json')

        assert response.status_code == 400
        assert 'sku' in response.json()
        assert 'El original' in response.json()['sku'][0]

    def test_case_only_difference_is_also_caught(self):
        """Matches how the constraint and the Conto lookup compare SKUs."""
        _, branch, user = make_center('A')
        make_product(branch, 'SER-VITC-30')

        response = api(user).post(LIST_URL, payload(sku='ser-vitc-30'), format='json')

        assert response.status_code == 400
        assert 'sku' in response.json()

    def test_surrounding_spaces_do_not_bypass_the_check(self):
        _, branch, user = make_center('A')
        make_product(branch, 'SER-VITC-30')

        response = api(user).post(
            LIST_URL, payload(sku='  SER-VITC-30  '), format='json'
        )

        assert response.status_code == 400

    def test_a_free_sku_is_accepted(self):
        _, branch, user = make_center('A')
        make_product(branch, 'OTRO-SKU')

        response = api(user).post(LIST_URL, payload(sku='SER-VITC-30'), format='json')

        assert response.status_code == 201

    def test_several_products_without_sku_are_accepted(self):
        """This is the current production state: 13 products, none with a code."""
        _, branch, user = make_center('A')
        make_product(branch, '', name='Sin código')

        response = api(user).post(LIST_URL, payload(sku=''), format='json')

        assert response.status_code == 201

    def test_a_sku_used_in_another_branch_is_accepted(self):
        _, _, user_a = make_center('A')
        _, branch_b, _ = make_center('B')
        make_product(branch_b, 'SER-VITC-30')

        response = api(user_a).post(LIST_URL, payload(sku='SER-VITC-30'), format='json')

        assert response.status_code == 201

    def test_editing_a_product_keeping_its_own_sku_is_allowed(self):
        """The uniqueness check must not flag the product against itself."""
        _, branch, user = make_center('A')
        product = make_product(branch, 'SER-VITC-30')

        response = api(user).patch(
            reverse('producto-detail', args=[product.pk]),
            {'sku': 'SER-VITC-30', 'nombre': 'Nombre nuevo'},
            format='json',
        )

        assert response.status_code == 200

    def test_editing_into_another_products_sku_is_rejected(self):
        _, branch, user = make_center('A')
        make_product(branch, 'OCUPADO', name='Ya lo tiene')
        product = make_product(branch, 'LIBRE')

        response = api(user).patch(
            reverse('producto-detail', args=[product.pk]),
            {'sku': 'OCUPADO'},
            format='json',
        )

        assert response.status_code == 400
        assert 'sku' in response.json()

"""
Tests for the SKU uniqueness constraint on Producto.

The SKU is the join key against Conto's catalog, so its uniqueness rules are
load-bearing: a duplicate makes the lookup ambiguous, which ends up creating a
duplicate product instead of matching the existing one.
"""
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.empleados.models import CentroEstetica, Sucursal
from apps.inventario.models import Producto


def make_branch(center_name, branch_name):
    center = CentroEstetica.objects.create(
        nombre=center_name, telefono='1', email=f'{branch_name}@test.local'
    )
    return Sucursal.objects.create(
        centro_estetica=center, nombre=branch_name,
        direccion='x', telefono='1', ciudad='CABA', provincia='CABA',
    )


def make_product(branch, sku, name='Producto'):
    return Producto.objects.create(
        sucursal=branch, nombre=name, sku=sku,
        precio_costo=Decimal('100.00'), precio_venta=Decimal('200.00'),
    )


@pytest.mark.django_db
class TestSkuConstraint:

    def test_several_products_without_sku_can_coexist(self):
        """
        This is the current state in production: 13 products, none with a SKU.
        The constraint has to tolerate it, so that adding the constraint does
        not depend on backfilling them first.
        """
        branch = make_branch('Ame', 'Banfield')

        for index in range(3):
            make_product(branch, '', name=f'Sin código {index}')

        assert Producto.objects.filter(sucursal=branch, sku='').count() == 3

    def test_duplicate_sku_in_the_same_branch_is_rejected(self):
        branch = make_branch('Ame', 'Banfield')
        make_product(branch, 'SER-VITC-30', name='Primero')

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_product(branch, 'SER-VITC-30', name='Segundo')

    def test_case_only_difference_is_also_rejected(self):
        """
        The integration looks products up case-insensitively, so allowing 'abc'
        and 'ABC' to coexist would let the constraint pass while the lookup
        reads them back as ambiguous.
        """
        branch = make_branch('Ame', 'Banfield')
        make_product(branch, 'SER-VITC-30', name='Primero')

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_product(branch, 'ser-vitc-30', name='Segundo')

    def test_same_sku_in_different_branches_is_allowed(self):
        """
        SKUs come from suppliers and brands: two centers selling the same line
        sharing a code is expected, not an error.
        """
        branch_a = make_branch('Ame', 'Banfield')
        branch_b = make_branch('Otro Centro', 'Palermo')

        make_product(branch_a, 'SER-VITC-30')
        make_product(branch_b, 'SER-VITC-30')

        assert Producto.objects.filter(sku='SER-VITC-30').count() == 2

    def test_same_sku_in_two_branches_of_the_same_center_is_allowed(self):
        """Each branch keeps its own stock, so each needs its own product row."""
        branch_a = make_branch('Ame', 'Banfield')
        branch_b = Sucursal.objects.create(
            centro_estetica=branch_a.centro_estetica, nombre='Lomas',
            direccion='x', telefono='1', ciudad='CABA', provincia='CABA',
        )

        make_product(branch_a, 'SER-VITC-30')
        make_product(branch_b, 'SER-VITC-30')

        assert Producto.objects.filter(sku='SER-VITC-30').count() == 2

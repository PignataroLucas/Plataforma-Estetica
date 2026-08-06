"""
Tests for the name-matching used to pair local products with Conto's SKUs.

A wrong pairing attributes income and stock to the wrong product, so the rules
that decide when to write without asking are worth pinning down.
"""
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.integraciones.management.commands.emparejar_sku_conto import (
    AUTO_RULES,
    FLOOR,
    normalize,
    similarity,
)
from apps.inventario.models import Producto

from .test_services import make_center


class TestNormalize:

    @pytest.mark.parametrize('raw,expected', [
        ('CREMA GEL HIDRATANTE', 'CREMA GEL HIDRATANTE'),
        ('Serum Ácido Hialurónico', 'SERUM ACIDO HIALURONICO'),
        ('Bruma  -  150 ml', 'BRUMA 150 ML'),
        ('Contorno de ojos (con Eyeseryl)', 'CONTORNO DE OJOS CON EYESERYL'),
        ('', ''),
        (None, ''),
    ])
    def test_it_strips_accents_case_and_punctuation(self, raw, expected):
        assert normalize(raw) == expected

    def test_accents_do_not_affect_similarity(self):
        assert similarity(
            'Serum Acido Hialuronico', 'SERUM ÁCIDO HIALURÓNICO'
        ) == 1.0

    def test_a_suffix_lowers_but_does_not_destroy_the_score(self):
        """
        Conto often appends a description to the name, which caps the score below
        a perfect match. It has to stay well clear of the floor, otherwise an
        obvious pairing would be reported as having no counterpart.

        How far below 1.0 depends on how long the suffix is, so this pins the
        property rather than a number: the second tier of AUTO_RULES is what
        decides whether a score like this is written, and that is tested apart.
        """
        score = similarity(
            'Serum Acido Hialuronico Doble Peso Molecular',
            'SERUM ÁCIDO HIALURÓNICO DOBLE PESO MOLECULAR - HIDRATACIÓN PROFUNDA',
        )
        assert FLOOR < score < 1.0

    def test_unrelated_names_score_below_the_floor(self):
        assert similarity('Toallas de papel para camilla', 'SERUM RETINOL') < FLOOR


class TestAutoRules:
    """The two tiers exist so an obvious match is not blocked by a low score."""

    def evaluates_as_safe(self, score, runner_up):
        margin = score - runner_up
        return any(score >= s and margin >= m for s, m in AUTO_RULES)

    def test_identical_name_with_no_competition_is_safe(self):
        assert self.evaluates_as_safe(1.00, 0.52)

    def test_a_suffixed_name_far_ahead_is_safe(self):
        """The 0.80 / 0.39 case seen with the hyaluronic acid serum."""
        assert self.evaluates_as_safe(0.80, 0.39)

    def test_two_sizes_of_the_same_product_are_not_safe(self):
        """100% vs 96% is the 150 ml / 60 ml pair: too close to guess."""
        assert not self.evaluates_as_safe(1.00, 0.96)

    def test_a_weak_match_is_not_safe_even_unopposed(self):
        assert not self.evaluates_as_safe(0.60, 0.10)


class FakeClient:
    def __init__(self, catalog, sales):
        self._catalog = catalog
        self._sales = sales

    def iter_stock(self, since=None):
        yield from self._catalog

    def iter_sales(self, since):
        yield from self._sales


def catalog_entry(sku, nombre, activo=True):
    return {'sku': sku, 'nombre': nombre, 'stock': 1, 'costo': '1',
            'precio': '2', 'activo': activo}


def sale_of(sku):
    return {
        'id': f'v-{sku}', 'canal': 'tiendanube', 'estado': 'PAGADO',
        'items': [{'tipo': 'PRODUCTO', 'sku': sku, 'cantidad': 1,
                   'precio_unitario': '100'}],
    }


def run_command(catalog, sales, **options):
    out = StringIO()
    with patch(
        'apps.integraciones.management.commands.emparejar_sku_conto.ContoClient',
        return_value=FakeClient(catalog, sales),
    ):
        call_command('emparejar_sku_conto', stdout=out, **options)
    return out.getvalue()


@pytest.mark.django_db
class TestCommand:

    def setup_integration(self):
        center, branch, integration = make_center('A', 'cnt_aaa')
        integration.link_verified_at = timezone.now()
        integration.save()
        return branch

    def add_product(self, branch, nombre):
        return Producto.objects.create(
            sucursal=branch, nombre=nombre, sku='',
            precio_costo=Decimal('1'), precio_venta=Decimal('2'),
        )

    def test_sales_break_the_tie_between_duplicate_entries(self):
        """
        Conto holds each product twice — a slug code and a generated one — and
        both match the name perfectly. The one that sells is the right answer.
        """
        branch = self.setup_integration()
        producto = self.add_product(branch, 'CREMA GEL HIDRATANTE')

        catalog = [
            catalog_entry('crema-gel-hidratante', 'CREMA GEL HIDRATANTE'),
            catalog_entry('PROD-1778369711284', 'CREMA GEL HIDRATANTE'),
        ]
        run_command(catalog, [sale_of('PROD-1778369711284')], aplicar=True)

        producto.refresh_from_db()
        assert producto.sku == 'PROD-1778369711284'

    def test_an_inactive_duplicate_is_not_chosen(self):
        """
        Conto flags the slug-coded duplicates as inactive, which is the second
        signal that identifies them — and it agrees with the sales one.
        """
        branch = self.setup_integration()
        producto = self.add_product(branch, 'SERUM RETINOL')

        catalog = [
            catalog_entry('SERUM-RETINOL', 'SERUM RETINOL', activo=False),
            catalog_entry('PROD-1778370360104', 'SERUM RETINOL', activo=True),
        ]
        run_command(catalog, [sale_of('PROD-1778370360104')], aplicar=True)

        producto.refresh_from_db()
        assert producto.sku == 'PROD-1778370360104'

    def test_an_inactive_entry_is_still_a_fallback(self):
        """A discontinued product may legitimately be the only counterpart."""
        branch = self.setup_integration()
        producto = self.add_product(branch, 'CARMEX EN BARRA')

        catalog = [catalog_entry('CARMEX-EN-BARRA', 'CARMEX EN BARRA',
                                 activo=False)]
        run_command(catalog, [], aplicar=True)

        producto.refresh_from_db()
        assert producto.sku == 'CARMEX-EN-BARRA'

    def test_nothing_is_written_without_aplicar(self):
        branch = self.setup_integration()
        producto = self.add_product(branch, 'SERUM RETINOL')

        catalog = [catalog_entry('PROD-1', 'SERUM RETINOL')]
        output = run_command(catalog, [sale_of('PROD-1')])

        producto.refresh_from_db()
        assert producto.sku == ''
        assert 'no se escribió nada' in output

    def test_two_sizes_are_left_for_a_human(self):
        branch = self.setup_integration()
        producto = self.add_product(branch, 'BRUMA HIDRATANTE Y CALMANTE - 150 ML')

        catalog = [
            catalog_entry('PROD-1', 'BRUMA HIDRATANTE Y CALMANTE - 150 ML'),
            catalog_entry('PROD-2', 'BRUMA HIDRATANTE Y CALMANTE - 60 ML'),
        ]
        output = run_command(
            catalog, [sale_of('PROD-1'), sale_of('PROD-2')], aplicar=True
        )

        producto.refresh_from_db()
        assert producto.sku == ''
        assert 'Requieren decisión humana' in output

    def test_a_product_absent_from_conto_is_reported(self):
        branch = self.setup_integration()
        self.add_product(branch, 'Toallas de papel para camilla')

        catalog = [catalog_entry('PROD-1', 'SERUM RETINOL')]
        output = run_command(catalog, [sale_of('PROD-1')], aplicar=True)

        assert 'Sin candidato parecido' in output

    def test_a_sku_already_used_is_not_assigned_twice(self):
        """The unique_sku_per_sucursal constraint would reject it anyway."""
        branch = self.setup_integration()
        Producto.objects.create(
            sucursal=branch, nombre='Ya emparejado', sku='PROD-1',
            precio_costo=Decimal('1'), precio_venta=Decimal('2'),
        )
        producto = self.add_product(branch, 'SERUM RETINOL')

        catalog = [catalog_entry('PROD-1', 'SERUM RETINOL')]
        run_command(catalog, [sale_of('PROD-1')], aplicar=True)

        producto.refresh_from_db()
        assert producto.sku == ''

    def test_products_of_another_branch_are_not_touched(self):
        branch = self.setup_integration()
        _, other_branch, _ = make_center('B', 'cnt_bbb')
        ajeno = Producto.objects.create(
            sucursal=other_branch, nombre='SERUM RETINOL', sku='',
            precio_costo=Decimal('1'), precio_venta=Decimal('2'),
        )
        propio = self.add_product(branch, 'SERUM RETINOL')

        catalog = [catalog_entry('PROD-1', 'SERUM RETINOL')]
        run_command(catalog, [sale_of('PROD-1')], aplicar=True,
                    integration_id=branch.conto_integrations.first().pk)

        propio.refresh_from_db()
        ajeno.refresh_from_db()
        assert propio.sku == 'PROD-1'
        assert ajeno.sku == ''

"""
Tests for the model-level guardrails on ContoIntegration.

Both rules live in `Model.clean()` rather than only in the serializer, so the
Django admin is covered too — the admin is the main interface until the frontend
screen exists, and a rule the admin skips is a rule that does not exist.
"""
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.empleados.models import CentroEstetica, Sucursal
from apps.integraciones.models import ContoIntegration


def make_center(name):
    center = CentroEstetica.objects.create(
        nombre=name, telefono='1', email=f'{name}@test.local'
    )
    branch = Sucursal.objects.create(
        centro_estetica=center, nombre=f'Sucursal {name}',
        direccion='x', telefono='1', ciudad='CABA', provincia='CABA',
    )
    return center, branch


def build(center, branch, **kwargs):
    defaults = {
        'center': center,
        'branch': branch,
        'base_url': 'https://conto.test',
        'token': 'x',
    }
    defaults.update(kwargs)
    return ContoIntegration(**defaults)


@pytest.mark.django_db
class TestBranchBelongsToCenter:

    def test_a_branch_of_another_center_is_rejected(self):
        center_a, _ = make_center('A')
        _, branch_b = make_center('B')

        with pytest.raises(ValidationError) as exc:
            build(center_a, branch_b).full_clean()

        assert 'branch' in exc.value.message_dict

    def test_the_centers_own_branch_is_accepted(self):
        center, branch = make_center('A')
        build(center, branch).full_clean()  # no debe levantar


@pytest.mark.django_db
class TestActivationRequiresAVerifiedLink:
    """
    Activating without a verified link leaves the account tripwire with nothing
    to compare responses against.
    """

    def test_cannot_activate_without_verifying(self):
        center, branch = make_center('A')

        with pytest.raises(ValidationError) as exc:
            build(center, branch, is_active=True).full_clean()

        assert 'is_active' in exc.value.message_dict
        assert 'Verificar vinculación' in exc.value.message_dict['is_active'][0]

    def test_an_account_id_alone_is_not_enough(self):
        """Both the id and the verification timestamp are required."""
        center, branch = make_center('A')

        with pytest.raises(ValidationError):
            build(
                center, branch, is_active=True, conto_account_id='cnt_aaa'
            ).full_clean()

    def test_can_activate_once_verified(self):
        center, branch = make_center('A')

        build(
            center, branch,
            is_active=True,
            conto_account_id='cnt_aaa',
            link_verified_at=timezone.now(),
        ).full_clean()  # no debe levantar

    def test_staying_inactive_needs_no_verification(self):
        center, branch = make_center('A')
        build(center, branch, is_active=False).full_clean()  # no debe levantar

    def test_can_sync_requires_both(self):
        center, branch = make_center('A')

        integration = build(center, branch, conto_account_id='cnt_aaa')
        assert integration.is_linked is False
        assert integration.can_sync is False

        integration.link_verified_at = timezone.now()
        assert integration.is_linked is True
        assert integration.can_sync is False  # sigue inactiva

        integration.is_active = True
        assert integration.can_sync is True

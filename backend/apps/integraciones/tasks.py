"""
Celery tasks for the Conto integration.

Thin wrappers: all the logic lives in sync.py so it can be tested without a
broker. These handle scheduling, iteration over integrations and retries.
"""
import logging

from celery import shared_task

from .models import ContoIntegration
from .services import (
    ContoAccountInactive,
    ContoAccountMismatch,
    ContoAuthError,
    ContoNotLinked,
    ContoUnavailable,
)
from .sync import SalesImporter, StockSynchronizer

logger = logging.getLogger(__name__)

# Errors that mean "stop and tell someone", not "try again". Retrying a revoked
# token or a mismatched account just delays the alert.
FATAL_ERRORS = (
    ContoAuthError,
    ContoAccountMismatch,
    ContoAccountInactive,
    ContoNotLinked,
)


def _syncable_integrations(integration_id=None):
    """
    Only integrations that are active AND have a verified account.

    The verification requirement is what makes the account tripwire meaningful:
    without a stored account id there is nothing to compare responses against.
    """
    queryset = ContoIntegration.objects.filter(
        is_active=True,
        conto_account_id__isnull=False,
        link_verified_at__isnull=False,
    ).select_related('branch', 'center')

    if integration_id:
        queryset = queryset.filter(pk=integration_id)

    return queryset


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_conto_stock(self, integration_id=None, full=False):
    """
    Pull the catalog state from Conto.

    Scheduled every 30 minutes. Stock is state, not events, so a missed run is
    corrected by the next one.
    """
    results = {}

    for integration in _syncable_integrations(integration_id):
        try:
            result = StockSynchronizer(integration).run(full=full)
            results[integration.pk] = result.summary
        except FATAL_ERRORS as exc:
            logger.error(
                "Sync de stock detenido para la integración %s: %s",
                integration.pk, exc,
            )
            results[integration.pk] = f"ERROR: {exc}"
        except ContoUnavailable as exc:
            logger.warning(
                "Conto no disponible para la integración %s: %s", integration.pk, exc
            )
            results[integration.pk] = f"REINTENTO: {exc}"
            raise self.retry(exc=exc)

    return results


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def import_conto_sales(self, integration_id=None):
    """
    Import vouchers from Conto as financial transactions.

    Scheduled every 15 minutes. The window overlaps the previous run and
    duplicates are absorbed by the uniqueness of (integration, voucher_id), so
    running it more often than needed is harmless.
    """
    results = {}

    for integration in _syncable_integrations(integration_id):
        try:
            result = SalesImporter(integration).run()
            results[integration.pk] = result.summary
        except FATAL_ERRORS as exc:
            logger.error(
                "Import de ventas detenido para la integración %s: %s",
                integration.pk, exc,
            )
            results[integration.pk] = f"ERROR: {exc}"
        except ContoUnavailable as exc:
            logger.warning(
                "Conto no disponible para la integración %s: %s", integration.pk, exc
            )
            results[integration.pk] = f"REINTENTO: {exc}"
            raise self.retry(exc=exc)

    return results


@shared_task
def verify_conto_links():
    """
    Re-check that every integration still points at the account it was linked to.

    Scheduled daily. The per-sync tripwire already catches a swapped token, but
    only when there is data to pull: an integration with no recent sales could
    stay silently wrong for weeks otherwise.
    """
    from .services import ContoClient

    results = {}

    for integration in _syncable_integrations():
        try:
            account = ContoClient(integration).get_account()
        except Exception as exc:
            logger.error(
                "No se pudo verificar la vinculación de %s: %s", integration.pk, exc
            )
            results[integration.pk] = f"ERROR: {exc}"
            continue

        received = account.get('cuenta_id')
        if received != integration.conto_account_id:
            logger.error(
                "La integración %s está vinculada a %s pero el token resuelve a %s. "
                "Se desactiva.",
                integration.pk, integration.conto_account_id, received,
            )
            integration.is_active = False
            integration.save(update_fields=['is_active', 'updated_at'])
            results[integration.pk] = 'DESVINCULADA'
            continue

        if not account.get('activa', True):
            logger.warning("La cuenta de Conto %s está desactivada", received)
            results[integration.pk] = 'CUENTA INACTIVA'
            continue

        results[integration.pk] = 'OK'

    return results

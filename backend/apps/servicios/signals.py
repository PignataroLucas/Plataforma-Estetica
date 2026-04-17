"""
Signals for servicios app.

Handles automatic expense generation when an AlquilerMaquina transitions to
COBRADO. This covers the case where the user marks a rental as COBRADO from
the edit form or any code path other than the turno completion flow.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import AlquilerMaquina


@receiver(pre_save, sender=AlquilerMaquina)
def track_previous_alquiler_state(sender, instance, **kwargs):
    """Remember the previous estado so post_save can detect transitions."""
    if instance.pk:
        try:
            old = AlquilerMaquina.objects.get(pk=instance.pk)
            instance._previous_estado = old.estado
        except AlquilerMaquina.DoesNotExist:
            instance._previous_estado = None
    else:
        instance._previous_estado = None


@receiver(post_save, sender=AlquilerMaquina)
def create_expense_on_cobrado(sender, instance, created, **kwargs):
    """
    When a rental transitions to COBRADO, create the expense transaction in
    finanzas (unless one is already linked).
    """
    from apps.finanzas.models import Transaction, TransactionCategory

    previous_estado = getattr(instance, '_previous_estado', None)

    if instance.estado != AlquilerMaquina.Estado.COBRADO:
        return
    if previous_estado == AlquilerMaquina.Estado.COBRADO:
        return
    if instance.transaccion_gasto_id:
        return

    category = TransactionCategory.objects.filter(
        branch=instance.sucursal,
        name='Alquileres de Equipos',
        type='EXPENSE',
        parent_category__isnull=True,
    ).first()

    if not category:
        category = TransactionCategory.objects.create(
            branch=instance.sucursal,
            name='Alquileres de Equipos',
            type='EXPENSE',
            is_system_category=True,
            color='#F59E0B',
            order=5,
        )

    transaction = Transaction.objects.create(
        branch=instance.sucursal,
        category=category,
        type='EXPENSE',
        amount=instance.costo,
        date=instance.fecha,
        description=f"Alquiler de {instance.maquina.nombre} - {instance.fecha.strftime('%d/%m/%Y')}",
        notes=f"Alquiler ID: {instance.pk}\nCosto: ${instance.costo}",
        payment_method='BANK_TRANSFER',
        auto_generated=True,
        registered_by=instance.creado_por,
    )

    AlquilerMaquina.objects.filter(pk=instance.pk).update(transaccion_gasto=transaction)
    instance.transaccion_gasto = transaction

"""
Signals for appointments (turnos) app to automatically create financial transactions
when payment states change (deposits and completed services).
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Turno


@receiver(pre_save, sender=Turno)
def track_previous_state(sender, instance, **kwargs):
    """
    Track the previous state of the appointment before saving.
    This allows us to detect state changes in post_save.
    """
    if instance.pk:
        try:
            old_instance = Turno.objects.get(pk=instance.pk)
            instance._previous_estado = old_instance.estado
            instance._previous_estado_pago = old_instance.estado_pago
        except Turno.DoesNotExist:
            instance._previous_estado = None
            instance._previous_estado_pago = None
    else:
        instance._previous_estado = None
        instance._previous_estado_pago = None


@receiver(post_save, sender=Turno)
def create_transaction_from_appointment(sender, instance, created, **kwargs):
    """
    Automatically create financial transactions when appointment payment state changes.

    Scenarios:
    1. Deposit paid (estado_pago: PENDIENTE → CON_SENA)
       → Create INCOME_SERVICE for monto_sena

    2. Service completed (estado: any → COMPLETADO)
       → Create INCOME_SERVICE for remaining amount (monto_total - monto_sena if applicable)
    """
    # Import here to avoid circular imports
    from apps.finanzas.models import Transaction, TransactionCategory

    previous_estado = getattr(instance, '_previous_estado', None)
    previous_estado_pago = getattr(instance, '_previous_estado_pago', None)

    # ==================== SCENARIO 1: Deposit Paid ====================
    # When estado_pago changes to CON_SENA, create income for the deposit
    if (previous_estado_pago != Turno.EstadoPago.CON_SENA and
        instance.estado_pago == Turno.EstadoPago.CON_SENA and
        instance.monto_sena and instance.monto_sena > 0):

        _create_service_income(
            instance=instance,
            amount=instance.monto_sena,
            description=f"Seña de turno: {instance.servicio.nombre} - {instance.cliente.nombre_completo}",
            Transaction=Transaction,
            TransactionCategory=TransactionCategory,
            is_deposit=True
        )

    # ==================== SCENARIO 2: Service Completed ====================
    # When estado changes to COMPLETADO, create income for the remaining amount
    if (previous_estado != Turno.Estado.COMPLETADO and
        instance.estado == Turno.Estado.COMPLETADO):

        # Calculate remaining amount
        if instance.estado_pago == Turno.EstadoPago.CON_SENA and instance.monto_sena:
            # Already paid deposit, charge the rest
            remaining_amount = instance.monto_total - instance.monto_sena
        else:
            # No deposit, charge full amount
            remaining_amount = instance.monto_total

        if remaining_amount > 0:
            _create_service_income(
                instance=instance,
                amount=remaining_amount,
                description=f"Servicio completado: {instance.servicio.nombre} - {instance.cliente.nombre_completo}",
                Transaction=Transaction,
                TransactionCategory=TransactionCategory,
                is_deposit=False
            )

        # Update payment status to PAGADO
        if instance.estado_pago != Turno.EstadoPago.PAGADO:
            # Use update() to avoid triggering signals again
            Turno.objects.filter(pk=instance.pk).update(estado_pago=Turno.EstadoPago.PAGADO)


def _create_service_income(instance, amount, description, Transaction, TransactionCategory, is_deposit=False):
    """
    Helper function to create an INCOME_SERVICE transaction from an appointment.

    Args:
        instance: The Turno instance
        amount: The amount to record
        description: Transaction description (in Spanish for UI)
        Transaction: Transaction model class
        TransactionCategory: TransactionCategory model class
        is_deposit: Whether this is a deposit payment
    """
    # Get or create "Servicios" income category
    service_income_category = TransactionCategory.objects.filter(
        branch=instance.sucursal,
        name='Servicios',
        type='INCOME',
        parent_category__isnull=True
    ).first()

    if not service_income_category:
        # Create category if it doesn't exist
        service_income_category = TransactionCategory.objects.create(
            branch=instance.sucursal,
            name='Servicios',
            type='INCOME',
            is_system_category=True,
            color='#3B82F6',  # Blue
            order=1
        )

    # Add deposit indicator to description if applicable
    if is_deposit:
        description = f"[SEÑA] {description}"

    # Create the financial transaction
    transaction = Transaction.objects.create(
        branch=instance.sucursal,
        category=service_income_category,
        type='INCOME_SERVICE',
        amount=amount,
        date=instance.fecha_hora_inicio.date(),
        description=description,
        notes=f"Turno #{instance.pk} - {instance.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}",
        client=instance.cliente,
        appointment=instance,
        payment_method='CASH',  # Default, can be edited later
        auto_generated=True,
        registered_by=instance.creado_por,
    )

    print(f"✅ Service income auto-created: {transaction} (${amount})")

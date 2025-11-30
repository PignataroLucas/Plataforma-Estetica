"""
Signals for appointments (turnos) app to automatically create financial transactions
when payment states change (deposits and completed services).
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
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

        # ==================== Machine Rental Expense ====================
        # If service uses a rented machine, create expense for daily rental
        if instance.servicio.maquina_alquilada:
            _create_machine_rental_expense(
                instance=instance,
                Transaction=Transaction,
                TransactionCategory=TransactionCategory
            )


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
        date=timezone.localtime(instance.fecha_hora_inicio).date(),
        description=description,
        notes=f"Turno #{instance.pk} - {instance.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}",
        client=instance.cliente,
        appointment=instance,
        payment_method='CASH',  # Default, can be edited later
        auto_generated=True,
        registered_by=instance.creado_por,
    )

    print(f"✅ Service income auto-created: {transaction} (${amount})")


def _create_machine_rental_expense(instance, Transaction, TransactionCategory):
    """
    Helper function to create an EXPENSE transaction for rented machine.

    IMPORTANT: Creates expense ONLY ONCE PER DAY per machine.
    The machine is rented for the full day, not per appointment.

    NEW: Verifies if there's a confirmed rental for this date.
    If no rental is confirmed, does NOT create expense automatically.

    Args:
        instance: The Turno instance
        Transaction: Transaction model class
        TransactionCategory: TransactionCategory model class
    """
    from apps.servicios.models import AlquilerMaquina

    machine = instance.servicio.maquina_alquilada
    appointment_date = timezone.localtime(instance.fecha_hora_inicio).date()

    # ==================== VERIFICACIÓN DE ALQUILER CONFIRMADO ====================
    # Check if there's a confirmed rental for this machine on this date
    alquiler = AlquilerMaquina.objects.filter(
        maquina=machine,
        fecha=appointment_date,
        sucursal=instance.sucursal,
        estado__in=[AlquilerMaquina.Estado.CONFIRMADO, AlquilerMaquina.Estado.COBRADO]
    ).first()

    if not alquiler:
        print(f"⚠️ No confirmed rental for {machine.nombre} on {appointment_date}. Skipping expense creation.")
        print(f"   → Create rental in: Servicios > Máquinas > {machine.nombre} > Programar Alquiler")
        return

    # Get or create "Alquileres de Equipos" expense category
    machine_expense_category = TransactionCategory.objects.filter(
        branch=instance.sucursal,
        name='Alquileres de Equipos',
        type='EXPENSE',
        parent_category__isnull=True
    ).first()

    if not machine_expense_category:
        # Create category if it doesn't exist
        machine_expense_category = TransactionCategory.objects.create(
            branch=instance.sucursal,
            name='Alquileres de Equipos',
            type='EXPENSE',
            is_system_category=True,
            color='#F59E0B',  # Amber
            order=5
        )

    # Check if expense already exists (linked to the alquiler)
    if alquiler.transaccion_gasto:
        # Expense already exists, just update notes
        existing_expense = alquiler.transaccion_gasto
        existing_expense.notes += f"\n+ Turno #{instance.pk}: {instance.servicio.nombre} - {instance.cliente.nombre_completo} ({instance.fecha_hora_inicio.strftime('%H:%M')})"
        existing_expense.save()
        print(f"✅ Machine rental expense updated: {existing_expense}")
        return

    # Create the expense transaction (ONCE PER DAY)
    transaction = Transaction.objects.create(
        branch=instance.sucursal,
        category=machine_expense_category,
        type='EXPENSE',
        amount=alquiler.costo,  # Use cost from rental record
        date=appointment_date,
        description=f"Alquiler de {machine.nombre} - {appointment_date.strftime('%d/%m/%Y')}",
        notes=f"Alquiler confirmado ID: {alquiler.pk}\nCosto: ${alquiler.costo}\nTurnos realizados:\n- Turno #{instance.pk}: {instance.servicio.nombre} - {instance.cliente.nombre_completo} ({instance.fecha_hora_inicio.strftime('%H:%M')})",
        payment_method='BANK_TRANSFER',  # Default for equipment rentals
        auto_generated=True,
        registered_by=instance.creado_por,
    )

    # Link transaction to rental and mark as charged
    alquiler.transaccion_gasto = transaction
    alquiler.estado = AlquilerMaquina.Estado.COBRADO
    alquiler.save()

    print(f"✅ Machine rental expense auto-created: {transaction} (${alquiler.costo})")
    print(f"   → Rental {alquiler.pk} marked as COBRADO")

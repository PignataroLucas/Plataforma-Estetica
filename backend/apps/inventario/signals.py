"""
Signals for inventory app to automatically create financial transactions
when inventory movements occur (e.g., purchases).
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import MovimientoInventario, Producto


@receiver(post_save, sender=Producto)
def create_initial_stock_movement(sender, instance, created, **kwargs):
    """
    When a product is created with initial stock, automatically create
    a MovimientoInventario (ENTRADA) which will trigger the expense creation.

    This ensures the initial stock purchase is recorded in finances.
    """
    if not created:
        return

    # Only if product has initial stock and cost
    if instance.stock_actual > 0 and instance.precio_costo > 0:
        # Create initial stock entry movement
        MovimientoInventario.objects.create(
            producto=instance,
            tipo='ENTRADA',
            cantidad=instance.stock_actual,
            stock_anterior=0,
            stock_nuevo=instance.stock_actual,
            costo_unitario=instance.precio_costo,
            motivo='Stock inicial al crear producto',
            notas=f'Carga automática de stock inicial: {instance.stock_actual} {instance.unidad_medida}',
            usuario=None,  # System generated
        )
        print(f"✅ Initial stock movement created for {instance.nombre}: {instance.stock_actual} units")


@receiver(post_save, sender=MovimientoInventario)
def create_transaction_from_inventory_movement(sender, instance, created, **kwargs):
    """
    Automatically create a financial transaction when an inventory movement occurs.

    - ENTRADA (purchase) → Creates EXPENSE transaction
    - SALIDA (sale) → Creates INCOME_PRODUCT transaction

    This ensures that all inventory movements are automatically recorded
    in the financial system without duplicate manual entry.
    """
    # Only process new records
    if not created:
        return

    # Avoid duplicates - check if transaction already exists
    if hasattr(instance, 'financial_transaction') and instance.financial_transaction:
        return

    # Import here to avoid circular imports
    from apps.finanzas.models import Transaction, TransactionCategory

    # Handle ENTRADA (purchases) - Create EXPENSE
    if instance.tipo == 'ENTRADA' and instance.costo_unitario:
        _create_expense_from_purchase(instance, Transaction, TransactionCategory)

    # Handle SALIDA (sales) - Create INCOME
    elif instance.tipo == 'SALIDA':
        _create_income_from_sale(instance, Transaction, TransactionCategory)


def _create_expense_from_purchase(instance, Transaction, TransactionCategory):
    """
    Create an EXPENSE transaction from an inventory purchase (ENTRADA)
    """
    # Calculate total amount
    total_amount = instance.cantidad * instance.costo_unitario

    # Get or create "Insumos y Productos" expense category
    supplies_category = TransactionCategory.objects.filter(
        branch=instance.producto.sucursal,
        name='Insumos y Productos',
        type='EXPENSE',
        parent_category__isnull=True
    ).first()

    if not supplies_category:
        # Create category if it doesn't exist
        supplies_category = TransactionCategory.objects.create(
            branch=instance.producto.sucursal,
            name='Insumos y Productos',
            type='EXPENSE',
            is_system_category=True,
            color='#8B5CF6',
            order=3
        )

    # Try to get subcategory based on product type
    subcategory = None
    if instance.producto.tipo == 'INSUMO':
        subcategory = TransactionCategory.objects.filter(
            parent_category=supplies_category,
            name='Productos Tratamiento'
        ).first()

    # Use subcategory if exists, otherwise use main category
    final_category = subcategory if subcategory else supplies_category

    # Create the financial transaction (description in Spanish for UI)
    transaction = Transaction.objects.create(
        branch=instance.producto.sucursal,
        category=final_category,
        type='EXPENSE',
        amount=total_amount,
        date=timezone.localtime(instance.creado_en).date(),
        description=f"Compra de {instance.cantidad} {instance.producto.unidad_medida} de {instance.producto.nombre}",
        notes=instance.notas or '',
        product=instance.producto,
        payment_method='CASH',  # Default, can be edited later
        auto_generated=True,
        registered_by=instance.usuario,
        inventory_movement=instance
    )

    print(f"✅ Expense transaction auto-created: {transaction}")


def _create_income_from_sale(instance, Transaction, TransactionCategory):
    """
    Create an INCOME_PRODUCT transaction from an inventory sale (SALIDA)
    """
    # Calculate total amount using sale price
    # Use custom price if provided, otherwise use product's final price (with offers)
    precio_unitario = instance.precio_unitario if instance.precio_unitario else instance.producto.precio_venta_final
    total_amount = instance.cantidad * precio_unitario

    # Get or create "Venta de Productos" income category
    product_sales_category = TransactionCategory.objects.filter(
        branch=instance.producto.sucursal,
        name='Venta de Productos',
        type='INCOME',
        parent_category__isnull=True
    ).first()

    if not product_sales_category:
        # Create category if it doesn't exist
        product_sales_category = TransactionCategory.objects.create(
            branch=instance.producto.sucursal,
            name='Venta de Productos',
            type='INCOME',
            is_system_category=True,
            color='#10B981',  # Green
            order=2
        )

    # Build description with offer info if applicable
    description = f"Venta de {instance.cantidad} {instance.producto.unidad_medida} de {instance.producto.nombre}"
    if instance.producto.en_oferta and instance.producto.precio_oferta:
        description += f" (en oferta: {instance.producto.porcentaje_descuento}% OFF)"

    # Add custom note if motivo is provided
    if instance.motivo:
        description += f" - {instance.motivo}"

    # Create the financial transaction (description in Spanish for UI)
    transaction = Transaction.objects.create(
        branch=instance.producto.sucursal,
        category=product_sales_category,
        type='INCOME_PRODUCT',
        amount=total_amount,
        date=timezone.localtime(instance.creado_en).date(),
        description=description,
        notes=instance.notas or '',
        product=instance.producto,
        payment_method='CASH',  # Default, can be edited later
        auto_generated=True,
        registered_by=instance.usuario,
        inventory_movement=instance
    )

    print(f"✅ Income transaction auto-created: {transaction} (${total_amount})")


@receiver(pre_delete, sender=MovimientoInventario)
def delete_associated_transaction(sender, instance, **kwargs):
    """
    When an inventory movement is deleted, also delete its associated
    financial transaction if it was auto-generated.

    This maintains data consistency between inventory and finances.
    """
    if hasattr(instance, 'financial_transaction') and instance.financial_transaction:
        transaction = instance.financial_transaction
        if transaction.auto_generated:
            print(f"🗑️  Deleting auto-generated transaction: {transaction}")
            transaction.delete()

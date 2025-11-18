from django.db import models
from django.utils import timezone
from apps.empleados.models import Sucursal, Usuario
from apps.clientes.models import Cliente


class TransactionCategory(models.Model):
    """
    Hierarchical category system for organizing financial transactions.
    Supports 2 levels: Main Category → Subcategory
    Example: Rent → Office Rent, Equipment Rent
    """
    class CategoryType(models.TextChoices):
        INCOME = 'INCOME', 'Ingreso'
        EXPENSE = 'EXPENSE', 'Gasto'

    # Relationships
    branch = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='transaction_categories'
    )
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="Categoría padre para estructura jerárquica"
    )

    # Type
    type = models.CharField(
        max_length=10,
        choices=CategoryType.choices
    )

    # Information
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Código de color hexadecimal para mostrar en UI"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Identificador de ícono para UI"
    )

    # Configuration
    is_active = models.BooleanField(default=True)
    is_system_category = models.BooleanField(
        default=False,
        help_text="Las categorías del sistema no pueden eliminarse, solo desactivarse"
    )
    order = models.IntegerField(
        default=0,
        help_text="Orden de visualización en UI"
    )

    # Audit
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_created'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría de Transacción'
        verbose_name_plural = 'Categorías de Transacciones'
        ordering = ['type', 'order', 'name']
        unique_together = [['branch', 'name', 'type', 'parent_category']]
        indexes = [
            models.Index(fields=['branch', 'type', 'is_active']),
            models.Index(fields=['parent_category']),
        ]

    def __str__(self):
        if self.parent_category:
            return f"{self.parent_category.name} > {self.name}"
        return self.name

    @property
    def is_subcategory(self):
        """Check if this is a subcategory"""
        return self.parent_category is not None

    @property
    def full_path(self):
        """Returns full path: Category > Subcategory"""
        if self.parent_category:
            return f"{self.parent_category.name} > {self.name}"
        return self.name

    @property
    def transaction_count(self):
        """Count of transactions using this category"""
        return self.transactions.count()


class Transaction(models.Model):
    """
    Record of all financial transactions (income and expenses).
    Integrates with inventory for automatic expense generation from purchases.
    """
    class TransactionType(models.TextChoices):
        # INCOME
        INCOME_SERVICE = 'INCOME_SERVICE', 'Ingreso por Servicio'
        INCOME_PRODUCT = 'INCOME_PRODUCT', 'Ingreso por Venta de Producto'
        INCOME_OTHER = 'INCOME_OTHER', 'Otro Ingreso'

        # EXPENSES (using category system instead of specific types)
        EXPENSE = 'EXPENSE', 'Gasto'

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Efectivo'
        TRANSFER = 'TRANSFER', 'Transferencia'
        DEBIT_CARD = 'DEBIT_CARD', 'Tarjeta de Débito'
        CREDIT_CARD = 'CREDIT_CARD', 'Tarjeta de Crédito'
        MERCADOPAGO = 'MERCADOPAGO', 'MercadoPago'
        OTHER = 'OTHER', 'Otro'

    # Relationships
    branch = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.PROTECT,  # Cannot delete category with transactions
        related_name='transactions',
        help_text="Categoría o subcategoría de la transacción"
    )

    client = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Cliente asociado (principalmente para ingresos)"
    )

    # Related entities
    appointment = models.ForeignKey(
        'turnos.Turno',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    product = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )

    # NEW: Relationship with inventory movement (for traceability)
    inventory_movement = models.OneToOneField(
        'inventario.MovimientoInventario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='financial_transaction',
        help_text="Movimiento de inventario vinculado si fue auto-generado"
    )

    # Transaction information
    type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        db_index=True
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto de la transacción (siempre positivo)"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    date = models.DateField(db_index=True)
    description = models.CharField(max_length=300)
    notes = models.TextField(blank=True)

    # Receipt/Invoice
    receipt_number = models.CharField(max_length=50, blank=True)
    receipt_file = models.FileField(
        upload_to='receipts/%Y/%m/',
        null=True,
        blank=True,
        help_text="Archivo PDF, JPG o PNG"
    )

    # NEW: Auto-generation flag
    auto_generated = models.BooleanField(
        default=False,
        help_text="Si fue creado automáticamente (ej: desde inventario)"
    )

    # Audit
    registered_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions_registered'
    )
    edited_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_edited'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['branch', 'date']),
            models.Index(fields=['branch', 'type', 'date']),
            models.Index(fields=['branch', 'category', 'date']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} - ${self.amount} - {self.date.strftime('%d/%m/%Y')}"

    @property
    def is_income(self):
        """Check if transaction is income"""
        return self.type.startswith('INCOME_')

    @property
    def is_expense(self):
        """Check if transaction is expense"""
        return self.type == 'EXPENSE'

    @property
    def signed_amount(self):
        """Returns amount with sign for balance calculations"""
        return self.amount if self.is_income else -self.amount

    @property
    def can_be_edited(self):
        """Check if transaction can be edited (< 30 days old)"""
        age_in_days = (timezone.now().date() - self.date).days
        return age_in_days <= 30

    @property
    def can_be_deleted(self):
        """Auto-generated transactions cannot be deleted directly"""
        return not self.auto_generated


class AccountReceivable(models.Model):
    """
    Tracking of client debts and pending payments
    """
    # Relationships
    client = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='accounts_receivable'
    )
    branch = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='accounts_receivable'
    )
    appointment = models.ForeignKey(
        'turnos.Turno',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accounts_receivable'
    )

    # Debt information
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto total adeudado"
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monto ya pagado"
    )
    pending_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto restante por pagar"
    )

    # Dates
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    full_payment_date = models.DateField(null=True, blank=True)

    # Details
    description = models.CharField(max_length=300)
    notes = models.TextField(blank=True)

    # Status
    is_paid = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cuenta por Cobrar'
        verbose_name_plural = 'Cuentas por Cobrar'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.client.full_name} - ${self.pending_amount} pending"

    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        if self.due_date and not self.is_paid:
            return timezone.now().date() > self.due_date
        return False

    def save(self, *args, **kwargs):
        # Calculate pending amount
        self.pending_amount = self.total_amount - self.paid_amount

        # Update payment status
        if self.pending_amount <= 0:
            self.is_paid = True
            if not self.full_payment_date:
                self.full_payment_date = timezone.now().date()

        super().save(*args, **kwargs)

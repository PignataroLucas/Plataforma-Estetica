"""
Models for the Conto integration.

Conto is the external platform that owns the real stock and cost of products.
It is automatically updated on every Tienda Nube sale, so this integration reads
sales and stock from Conto instead of talking to Tienda Nube directly.

See CONTO_API_REQUIREMENTS.md for the API contract and
INTEGRACION_CONTO_SPEC.md for the implementation plan.
"""
from django.core.exceptions import ValidationError
from django.db import models

from apps.empleados.models import CentroEstetica, Sucursal
from apps.finanzas.models import Transaction


def default_import_channels():
    """
    Only online sales are imported by default.

    Counter sales ('presencial') are already registered through Mi Caja, so
    importing them would double-count the income.
    """
    return ['tiendanube']


class ContoIntegration(models.Model):
    """
    Links one aesthetic center to one Conto account.

    The two uniqueness constraints point in opposite directions and both are
    needed: OneToOne on `center` prevents a center from having two accounts,
    and unique on `conto_account_id` prevents two centers from reading the
    same account. Either one alone lets half of the misconfigurations through.
    """
    # Tenant. Derived from request.user, never accepted from the request body.
    center = models.OneToOneField(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='conto_integration'
    )
    branch = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name='conto_integrations',
        help_text="Sucursal a la que se imputan las ventas y el stock de Conto"
    )

    # Credentials
    base_url = models.URLField(
        help_text="URL base de la API de Conto, sin barra final"
    )
    token = models.CharField(
        max_length=255,
        help_text="Token de solo lectura generado en Conto. No se muestra en la API"
    )

    # Identity, filled by calling GET /api/cuenta/ — never typed by hand
    conto_account_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        help_text="Se completa automáticamente al verificar la vinculación"
    )
    conto_account_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre de la cuenta en Conto, para que un humano confirme la vinculación"
    )
    link_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que se validó la identidad contra Conto"
    )

    # Configuration
    is_active = models.BooleanField(
        default=False,
        help_text="Se activa recién cuando la vinculación fue verificada"
    )
    default_payment_method = models.CharField(
        max_length=20,
        choices=Transaction.PaymentMethod.choices,
        default=Transaction.PaymentMethod.MERCADOPAGO,
        help_text="Se usa cuando Conto no informa el medio de pago real"
    )
    channels_to_import = models.JSONField(
        default=default_import_channels,
        help_text="Canales de Conto a importar. Por defecto solo 'tiendanube'"
    )
    create_missing_clients = models.BooleanField(
        default=True,
        help_text="Crear el cliente si no existe en este centro"
    )
    create_missing_products = models.BooleanField(
        default=True,
        help_text="Crear el producto si el SKU no existe en la sucursal. "
                  "Conto informa costo y precio, así que el producto nace completo"
    )

    # Sync cursors
    import_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="No importar ventas anteriores a esta fecha. Obligatorio para la "
                  "primera corrida: evita traer años de histórico sin querer. "
                  "Para ampliar el histórico después, moverla hacia atrás y "
                  "limpiar 'última sincronización de ventas'"
    )
    last_stock_sync = models.DateTimeField(null=True, blank=True)
    last_sales_sync = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Integración con Conto'
        verbose_name_plural = 'Integraciones con Conto'
        ordering = ['id']

    def __str__(self):
        return f"Conto - {self.center.nombre}"

    def clean(self):
        """
        The branch must belong to this integration's center.

        Without this check, pointing the integration at another center's branch
        is enough to write stock and income into the wrong tenant. It lives on
        the model rather than only on the serializer so the admin is covered too.
        """
        super().clean()
        if self.branch_id and self.center_id:
            if self.branch.centro_estetica_id != self.center_id:
                raise ValidationError({
                    'branch': "La sucursal no pertenece a este centro de estética"
                })

    @property
    def is_linked(self):
        """An integration can only sync once its identity was verified."""
        return bool(self.conto_account_id and self.link_verified_at)

    @property
    def can_sync(self):
        return self.is_active and self.is_linked


class ContoSale(models.Model):
    """
    A voucher pulled from Conto: either a sale or a credit note.

    Acts as the idempotency lock and the audit trail. The raw payload is always
    stored, including on failures, so a voucher can be reprocessed without
    querying Conto again.
    """
    class VoucherType(models.TextChoices):
        SALE = 'SALE', 'Venta'
        CREDIT_NOTE = 'CREDIT_NOTE', 'Nota de Crédito'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        PROCESSED = 'PROCESSED', 'Procesada'
        ERROR = 'ERROR', 'Error'
        SKIPPED = 'SKIPPED', 'Omitida'

    integration = models.ForeignKey(
        ContoIntegration,
        on_delete=models.CASCADE,
        related_name='sales'
    )

    # Conto ids are unique within an account, not across accounts, which is why
    # the uniqueness constraint below includes the integration.
    voucher_id = models.CharField(max_length=100, db_index=True)
    type = models.CharField(
        max_length=20,
        choices=VoucherType.choices,
        default=VoucherType.SALE
    )
    related_voucher_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Para notas de crédito: voucher de la venta que reversan"
    )
    external_order_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Número de orden en Tienda Nube o Mercado Libre"
    )
    channel = models.CharField(max_length=50, db_index=True)

    # Denormalized from the payload for listing and filtering without parsing JSON
    date = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de la venta según Conto, ya resuelta en hora de Argentina"
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    payload = models.JSONField(
        help_text="Respuesta cruda de Conto. Permite reprocesar sin volver a consultar"
    )

    # Processing state
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    error_message = models.TextField(blank=True)
    transactions = models.ManyToManyField(
        Transaction,
        blank=True,
        related_name='conto_sales',
        help_text="Transacciones generadas a partir de este voucher"
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Venta de Conto'
        verbose_name_plural = 'Ventas de Conto'
        ordering = ['-date', '-created_at']
        unique_together = [['integration', 'voucher_id']]
        indexes = [
            models.Index(fields=['integration', 'status']),
            models.Index(fields=['integration', 'date']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} {self.voucher_id} - {self.get_status_display()}"

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
from django.utils import timezone

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
        related_name='conto_integration',
        verbose_name='Centro estética'
    )
    branch = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name='conto_integrations',
        verbose_name='Sucursal',
        help_text="Sucursal a la que se imputan las ventas y el stock de Conto"
    )

    # Credentials
    base_url = models.URLField(
        verbose_name='URL de Conto',
        help_text="URL base de la API de Conto, sin barra final"
    )
    token = models.CharField(
        max_length=255,
        verbose_name='Token',
        help_text="Token de solo lectura generado en Conto. No se muestra en la API"
    )

    # Identity, filled by calling GET /api/cuenta/ — never typed by hand
    conto_account_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        verbose_name='ID de cuenta en Conto',
        help_text="Se completa automáticamente al verificar la vinculación"
    )
    conto_account_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre de cuenta en Conto',
        help_text="Nombre de la cuenta en Conto, para que un humano confirme la vinculación"
    )
    link_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Vinculación verificada el',
        help_text="Última vez que se validó la identidad contra Conto"
    )

    # Configuration
    is_active = models.BooleanField(
        default=False,
        verbose_name='Activa',
        help_text="Se activa recién cuando la vinculación fue verificada"
    )
    default_payment_method = models.CharField(
        max_length=20,
        choices=Transaction.PaymentMethod.choices,
        default=Transaction.PaymentMethod.MERCADOPAGO,
        verbose_name='Medio de pago por defecto',
        help_text="Se usa cuando Conto no informa el medio de pago real"
    )
    channels_to_import = models.JSONField(
        default=default_import_channels,
        verbose_name='Canales a importar',
        help_text="Canales de Conto a importar. Por defecto solo 'tiendanube'"
    )
    create_missing_clients = models.BooleanField(
        default=True,
        verbose_name='Crear clientes faltantes',
        help_text="Crear el cliente si no existe en este centro"
    )
    create_missing_products = models.BooleanField(
        default=True,
        verbose_name='Crear productos faltantes',
        help_text="Crear el producto si el SKU no existe en la sucursal. "
                  "Conto informa costo y precio, así que el producto nace completo"
    )

    # Sync cursors
    import_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Importar ventas desde',
        help_text="No importar ventas anteriores a esta fecha. Obligatorio para la "
                  "primera corrida: evita traer años de histórico sin querer. "
                  "Para ampliar el histórico después, moverla hacia atrás y "
                  "limpiar 'última sincronización de ventas'"
    )
    last_stock_sync = models.DateTimeField(
        null=True, blank=True, verbose_name='Última sincronización de stock'
    )
    last_sales_sync = models.DateTimeField(
        null=True, blank=True, verbose_name='Última sincronización de ventas'
    )

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

        # Activating without a verified link leaves the account tripwire with
        # nothing to compare responses against. This lives on the model, not only
        # on the serializer, so the admin is covered too — the admin is the main
        # interface until the frontend screen exists.
        if self.is_active and not self.is_linked:
            raise ValidationError({
                'is_active': "Primero verificá la vinculación con Conto. "
                             "Usá la acción «Verificar vinculación con Conto» "
                             "en el listado de integraciones."
            })

    @property
    def is_linked(self):
        """An integration can only sync once its identity was verified."""
        return bool(self.conto_account_id and self.link_verified_at)

    @property
    def can_sync(self):
        return self.is_active and self.is_linked


class TiendanubeIntegration(models.Model):
    """
    Links one aesthetic center to its Tienda Nube store, for issuing coupons.

    Separate from `ContoIntegration` on purpose: they are different channels
    with different lifetimes. Conto is read-only and reads sales; this one
    writes coupons and dies when the merchant uninstalls the app.

    Same two uniqueness constraints as the Conto integration, and for the same
    reason: OneToOne on `center` stops a center from having two stores, unique
    on `store_id` stops two centers from pointing at the same store.
    """
    center = models.OneToOneField(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='tiendanube_integration',
        verbose_name='Centro estética'
    )

    store_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='ID de tienda',
        help_text="El `user_id` que devuelve el OAuth de Tienda Nube"
    )
    store_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre de la tienda',
        help_text="Para que un humano confirme que se vinculó la tienda correcta"
    )
    # La dirección pública de la tienda, que es contra la que se arma el carrito.
    # Sale de `url_with_protocol` al vincular y no se escribe a mano: un dominio
    # tipeado mal manda a la clienta a una tienda que no es.
    store_url = models.URLField(
        blank=True,
        verbose_name='URL de la tienda',
        help_text="Dirección pública, para armar el carrito y el checkout"
    )

    # The token does not expire: it is valid until the merchant uninstalls the
    # app or a new one is issued. There is no refresh flow to implement.
    #
    # Stored like `ContoIntegration.token`: never exposed by the API. That is
    # the existing pattern in this app, not encryption at rest — see the note
    # in COMPRA_EN_APP_SPEC.md §5.1.
    token = models.CharField(
        max_length=255,
        verbose_name='Token',
        help_text="Token de Tienda Nube. No se muestra en la API"
    )
    scope = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Permisos',
        help_text="Permisos que el centro autorizó al instalar la app"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa',
        help_text="Se desactiva sola cuando el centro desinstala la app"
    )
    # Acá vive la decisión del §7.2, que es del centro y no técnica: si el
    # descuento de la app se suma al 10% de transferencia o lo reemplaza.
    # Arranca en True porque es lo que hace Tienda Nube por defecto (verificado
    # contra la API): dejarlo en False sin que nadie lo haya decidido cambiaría
    # el comportamiento actual de la tienda por omisión.
    coupons_combine_with_other_discounts = models.BooleanField(
        default=True,
        verbose_name='Los cupones se combinan con otras promociones',
        help_text="Si está activo, el descuento de la app se suma a los del "
                  "medio de pago. Si no, lo reemplaza"
    )
    installed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Instalada el'
    )
    uninstalled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Desinstalada el'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Integración con Tienda Nube'
        verbose_name_plural = 'Integraciones con Tienda Nube'
        ordering = ['id']

    def __str__(self):
        return f"Tienda Nube - {self.center.nombre}"

    @property
    def can_issue_coupons(self):
        return self.is_active and bool(self.token)


class CuponApp(models.Model):
    """
    A single-use coupon issued to one clienta for one purchase from the app.

    It is the whole mechanism of COMPRA_EN_APP_SPEC.md §3.2 in one row: it
    applies the discount, it locks it to a single use so the code cannot leak
    into a WhatsApp group, and it is what makes the sale attributable — a sale
    that comes back from Conto carrying one of these codes is, by definition, a
    sale from the app.

    The row outlives the coupon in Tienda Nube on purpose. The cleanup deletes
    the coupon there but keeps this, because the analytics of §5.7 are built
    against it: which code, to which clienta, when, and for how much.
    """
    integration = models.ForeignKey(
        TiendanubeIntegration,
        on_delete=models.CASCADE,
        related_name='cupones'
    )
    # SET_NULL and not CASCADE: borrar una ficha no puede borrar el rastro de un
    # descuento que se dio y que quizás ya se cobró.
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cupones_app',
        verbose_name='Clienta'
    )

    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Código',
        help_text="Código con prefijo APP-, impredecible y de un solo uso"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Descuento',
        help_text="Porcentaje que se le aplicó, resuelto por el segmento de la clienta"
    )
    tiendanube_coupon_id = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        verbose_name='ID en Tienda Nube',
        help_text="Necesario para borrarlo cuando vence sin usarse"
    )

    issued_at = models.DateTimeField(default=timezone.now, verbose_name='Emitido')
    expires_at = models.DateTimeField(verbose_name='Vence')
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Usado',
        help_text="Se completa al importar la venta que lo trae"
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Borrado de Tienda Nube',
        help_text="Cuándo lo borró la limpieza por haber vencido sin usarse"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cupón de la app'
        verbose_name_plural = 'Cupones de la app'
        ordering = ['-issued_at']
        indexes = [
            # La limpieza busca por acá: vencidos, sin usar y todavía vivos en TN.
            models.Index(fields=['expires_at', 'used_at', 'revoked_at']),
        ]

    def __str__(self):
        return f"{self.code} ({self.percentage}%)"

    @property
    def esta_vencido(self):
        return timezone.now() >= self.expires_at


class TiendanubeInstallIntent(models.Model):
    """
    An admin declaring, before installing, which center the store belongs to.

    Exists because of a hole in Tienda Nube's OAuth: **there is no `state`**.
    Their authorize URL takes only the app id, and the callback comes back with
    only `code` — verified against their docs and their official PHP SDK, which
    neither sends nor reads one. So when the token comes back there is nothing
    in the request tying it to a tenant.

    A reinstall resolves itself: the store id already has an integration. A
    first install has no such anchor, and guessing wrong would hand one center
    the power to issue coupons on another's store. This row is the anchor: the
    admin opens the install from the CRM, that leaves a short-lived intent, and
    the callback claims it.

    Deliberately claimed only when there is exactly one open intent. Two centers
    installing at the same time is ambiguous, and the right answer to an
    ambiguous tenant is to refuse, not to pick.
    """
    center = models.ForeignKey(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='tiendanube_install_intents',
        verbose_name='Centro estética'
    )
    created_by = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Iniciada por'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        verbose_name='Vence',
        help_text="Ventana para completar la instalación. Corta a propósito: "
                  "es lo que hace que solo haya un intento abierto por vez"
    )
    consumed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Usada',
        help_text="Cuándo la reclamó el callback. Una intención sirve una sola vez"
    )

    class Meta:
        verbose_name = 'Instalación de Tienda Nube iniciada'
        verbose_name_plural = 'Instalaciones de Tienda Nube iniciadas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['consumed_at', 'expires_at']),
        ]

    def __str__(self):
        return f"Instalación de {self.center.nombre} ({self.created_at:%d/%m %H:%M})"

    @property
    def esta_abierta(self):
        return self.consumed_at is None and timezone.now() < self.expires_at


class TiendanubePrivacyRequest(models.Model):
    """
    A privacy request from Tienda Nube, kept so a person can answer it.

    Tienda Nube requires three webhooks to homologate an app (§5.1). Two of them
    —`customers/redact` and `customers/data_request`— are addressed to a human:
    their own documentation says it is the app's responsibility to send the
    report to the merchant. Answering 200 and logging a line would mean the
    request dies in the deploy's log, so it gets a row instead.

    **The handlers do not delete anything on their own, and that is on purpose.**
    This app's permissions are read products and read/write coupons: it never
    reads customers or orders from the store, so there is no Tienda Nube
    customer data here to redact. What does exist —the clienta's file in the
    CRM— is the center's own record, loaded in this platform and not sourced
    from the store. Deleting it because Tienda Nube forwarded a request would
    destroy the center's data on a third party's say-so.

    The payload is stored whole, like `ContoSale.payload` and for the same
    reason: it is what lets someone act on the request later. It carries the
    buyer's personal data, so it belongs in the same purge as that one
    (INTEGRACION_CONTO_SPEC.md §14).
    """
    class Event(models.TextChoices):
        STORE_REDACT = 'store/redact', 'Borrado de la tienda'
        CUSTOMERS_REDACT = 'customers/redact', 'Borrado de datos de un comprador'
        CUSTOMERS_DATA_REQUEST = 'customers/data_request', 'Pedido de datos de un comprador'

    # Nullable and not the only link: el pedido llega igual para una tienda que
    # nunca vinculamos, o para una que ya se desvinculó. Se guarda el `store_id`
    # crudo para que el pedido siga siendo legible en ese caso.
    integration = models.ForeignKey(
        TiendanubeIntegration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='privacy_requests',
        verbose_name='Integración'
    )
    store_id = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='ID de tienda'
    )
    event = models.CharField(
        max_length=40,
        choices=Event.choices,
        db_index=True,
        verbose_name='Evento'
    )
    payload = models.JSONField(
        verbose_name='Contenido',
        help_text="Lo que mandó Tienda Nube, crudo"
    )

    received_at = models.DateTimeField(default=timezone.now, verbose_name='Recibido')
    handled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Resuelto',
        help_text="Cuándo se le respondió al centro. Los de la tienda se "
                  "resuelven solos; los de un comprador los cierra una persona"
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas',
        help_text="Qué se hizo con el pedido"
    )

    class Meta:
        verbose_name = 'Pedido de privacidad de Tienda Nube'
        verbose_name_plural = 'Pedidos de privacidad de Tienda Nube'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['handled_at', 'received_at']),
        ]

    def __str__(self):
        return f"{self.get_event_display()} - tienda {self.store_id}"


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

    # Origin and coupon, copied from the payload without being interpreted.
    #
    # They get columns of their own even though `payload` already holds them:
    # attributing app sales means matching the coupon code against the codes the
    # app issues (COMPRA_EN_APP_SPEC.md §5.6), and `payload` cannot be relied on
    # to still be there — it carries the buyer's personal data and is a
    # candidate for purging (INTEGRACION_CONTO_SPEC.md §14).
    sale_origin = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Origen de la venta',
        help_text="Campo 'origen_venta' de Conto, crudo: de dónde dice Tienda "
                  "Nube que viene la orden (store, api, meli, form, pos)"
    )
    app_origin = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='App de origen',
        help_text="Campo 'app_origen' de Conto, crudo: qué app de Tienda Nube "
                  "creó la orden, si fue creada por una"
    )
    coupon_code = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
        verbose_name='Cupón',
        help_text="Campo 'cupon' de Conto, crudo. Con más de un cupón vienen "
                  "los códigos separados por coma"
    )
    coupon_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Descuento por cupón',
        help_text="Campo 'descuento_cupon' de Conto. Vacío significa que Conto "
                  "no informó el campo, que no es lo mismo que un descuento de 0"
    )

    # La atribución del §5.6: si la venta trae uno de nuestros códigos, es una
    # venta de la app y sabemos de qué clienta. El vínculo se guarda en vez de
    # recalcularlo, porque el cupón se borra de Tienda Nube al vencer y los
    # códigos viejos dejarían de resolverse.
    cupon_app = models.ForeignKey(
        'integraciones.CuponApp',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas',
        verbose_name='Cupón de la app',
        help_text="Cargado al importar, cuando el código de la venta es uno nuestro"
    )

    payload = models.JSONField(
        help_text="Respuesta cruda de Conto. Permite reprocesar sin volver a consultar"
    )

    # Conto's `total` is what the customer actually paid, taken straight from
    # Tienda Nube's order.total. The line items, summed with the sign of their
    # type, must equal it exactly. When they do not, our income breakdown is
    # wrong even though the sale imported, so it gets flagged rather than trusted.
    total_discrepancy = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Descuadre contra el total',
        help_text="Diferencia entre la suma de las líneas y el total informado "
                  "por Conto. Vacío significa que cuadra"
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

    @property
    def es_venta_de_la_app(self):
        """
        Verdadero cuando la venta trae un cupón emitido por la app.

        Es la definición del §3.2, y no depende de `origen_venta`: una compra
        hecha desde la app llega igual que una del navegador (`store`), así que
        el único rastro es el código.
        """
        return self.cupon_app_id is not None

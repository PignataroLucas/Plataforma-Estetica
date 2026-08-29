"""
Django Admin for the Conto integration.

This is intentionally usable on its own: it lets an admin load the Conto token
and configure the integration before the frontend screen exists.
"""
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.html import format_html

from .instalacion import (
    AUTHORIZE_URL,
    VENTANA_DE_INSTALACION,
    cerrar_intentos_abiertos,
)
from .models import (
    ContoIntegration,
    ContoSale,
    CuponApp,
    TiendanubeInstallIntent,
    TiendanubeIntegration,
    TiendanubePrivacyRequest,
)
from .services import ContoClient, ContoError
from .sync import SalesImporter, StockSynchronizer


class ContoIntegrationForm(forms.ModelForm):
    """
    Masks the token in the form.

    render_value stays True on purpose: with it off, saving the form without
    retyping the token would silently blank it.
    """
    class Meta:
        model = ContoIntegration
        fields = '__all__'
        widgets = {
            'token': forms.PasswordInput(render_value=True),
        }


@admin.register(ContoIntegration)
class ContoIntegrationAdmin(admin.ModelAdmin):
    """Admin for the center-to-Conto-account link"""
    form = ContoIntegrationForm
    list_display = [
        'center',
        'branch',
        'link_status',
        'is_active',
        'last_sales_sync',
        'last_stock_sync',
    ]
    list_filter = ['is_active']
    search_fields = ['center__nombre', 'conto_account_id', 'conto_account_name']

    # Filled by the sync process against Conto, never typed by hand
    readonly_fields = [
        'conto_account_id',
        'conto_account_name',
        'link_verified_at',
        'last_stock_sync',
        'last_sales_sync',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Vinculación', {
            'fields': ('center', 'branch'),
            'description': 'La sucursal debe pertenecer al centro seleccionado.'
        }),
        ('Credenciales de Conto', {
            'fields': ('base_url', 'token'),
            'description': 'El token se genera en Conto, en "API de integraciones". '
                           'Debe ser de solo lectura.'
        }),
        ('Identidad verificada', {
            'fields': ('conto_account_id', 'conto_account_name', 'link_verified_at'),
            'description': 'Se completa automáticamente al verificar la vinculación '
                           'contra Conto. No se carga a mano.'
        }),
        ('Configuración de importación', {
            'fields': (
                'is_active',
                'channels_to_import',
                'default_payment_method',
                'create_missing_clients',
                'create_missing_products',
            ),
            'description': 'La integración se activa recién cuando la vinculación '
                           'fue verificada.'
        }),
        ('Sincronización', {
            'fields': ('import_from', 'last_stock_sync', 'last_sales_sync'),
            'description': '"Importar desde" es obligatorio antes de la primera '
                           'sincronización de ventas. Para ampliar el histórico, '
                           'movela hacia atrás y borrá la última sincronización.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'verificar_vinculacion',
        'sincronizar_stock',
        'sincronizar_stock_completo',
        'importar_ventas',
    ]

    @admin.action(description='Verificar vinculación con Conto')
    def verificar_vinculacion(self, request, queryset):
        """
        Ask Conto which account each token belongs to, and store the answer.

        Refuses to re-link an integration whose token now resolves to a
        different account: that is the scenario the isolation rules exist to
        prevent, and an admin action has nowhere to ask for confirmation. Use the
        API endpoint for that, which requires an explicit flag.
        """
        for integration in queryset:
            try:
                account = ContoClient(integration).get_account()
            except ContoError as exc:
                self.message_user(
                    request, f'{integration}: {exc}', level=messages.ERROR
                )
                continue

            received = account.get('cuenta_id')
            if not received:
                self.message_user(
                    request,
                    f"{integration}: Conto no devolvió 'cuenta_id'.",
                    level=messages.ERROR,
                )
                continue

            previous = integration.conto_account_id
            if previous and previous != received:
                self.message_user(
                    request,
                    f'{integration}: el token resuelve a la cuenta {received!r} '
                    f'y está vinculada a {previous!r}. No se cambió nada. '
                    f'Cambiar de cuenta requiere confirmación explícita por API.',
                    level=messages.ERROR,
                )
                continue

            integration.conto_account_id = received
            integration.conto_account_name = account.get('nombre') or ''
            integration.link_verified_at = timezone.now()
            integration.save(update_fields=[
                'conto_account_id', 'conto_account_name',
                'link_verified_at', 'updated_at',
            ])

            activa = account.get('activa', True)
            level = messages.SUCCESS if activa else messages.WARNING
            self.message_user(
                request,
                f'{integration}: vinculado a "{integration.conto_account_name}" '
                f'({received}). Confirmá que sea la cuenta correcta antes de activar.'
                + ('' if activa else ' Atención: la cuenta está desactivada en Conto.'),
                level=level,
            )

    @admin.action(description='Sincronizar stock desde Conto (incremental)')
    def sincronizar_stock(self, request, queryset):
        """Only what changed in Conto since the last run."""
        self._run(request, queryset, 'Stock',
                  lambda i: StockSynchronizer(i).run())

    @admin.action(description='Sincronizar stock desde Conto (catálogo completo)')
    def sincronizar_stock_completo(self, request, queryset):
        """
        Re-pull the whole catalog, ignoring the cursor.

        Needed after changing what the sync does — turning on
        `create_missing_products`, for instance. The incremental run would return
        nothing, because nothing changed in Conto: the change was on our side.
        """
        self._run(request, queryset, 'Stock (completo)',
                  lambda i: StockSynchronizer(i).run(full=True))

    @admin.action(description='Importar ventas desde Conto')
    def importar_ventas(self, request, queryset):
        self._run(request, queryset, 'Ventas',
                  lambda i: SalesImporter(i).run())

    def _run(self, request, queryset, label, work):
        """
        Run a synchronization inline and report the summary.

        Inline because there is no Celery worker deployed. A very large first
        import should go through the `sincronizar_conto` command instead, to
        avoid the request timing out.
        """
        for integration in queryset:
            if not integration.can_sync:
                self.message_user(
                    request,
                    f'{integration}: tiene que estar vinculada y activa.',
                    level=messages.WARNING,
                )
                continue

            try:
                result = work(integration)
            except ContoError as exc:
                self.message_user(
                    request, f'{integration} — {label}: {exc}', level=messages.ERROR
                )
                continue

            level = messages.ERROR if result.errors else messages.SUCCESS
            self.message_user(
                request, f'{integration} — {label}: {result.summary}', level=level
            )

            # The unmatched list is the point of the first stock run: it is the
            # Conto catalog to pair the local products against. A count alone
            # does not help.
            unmatched = getattr(result, 'unmatched', None)
            if unmatched:
                shown = ', '.join(unmatched[:40])
                extra = f' … y {len(unmatched) - 40} más' if len(unmatched) > 40 else ''
                self.message_user(
                    request,
                    f'SKU de Conto sin producto en la sucursal: {shown}{extra}',
                    level=messages.WARNING,
                )

            for error in (result.errors or [])[:10]:
                self.message_user(
                    request, f'{label} — error: {error}', level=messages.ERROR
                )

    def link_status(self, obj):
        """Show whether the account identity was verified against Conto"""
        if obj.is_linked:
            return format_html(
                '<span style="background-color: #D1FAE5; color: #065F46; '
                'padding: 3px 8px; border-radius: 4px;">Verificada: {}</span>',
                obj.conto_account_name or obj.conto_account_id
            )
        return format_html(
            '<span style="background-color: #FEF3C7; color: #92400E; '
            'padding: 3px 8px; border-radius: 4px;">Sin verificar</span>'
        )
    link_status.short_description = 'Vinculación'


@admin.register(ContoSale)
class ContoSaleAdmin(admin.ModelAdmin):
    """
    Read-only view of the vouchers pulled from Conto.

    These records mirror external data, so they are not editable from here:
    fixing one means reprocessing it, not hand-editing the mirror.
    """
    list_display = [
        'date',
        'voucher_id',
        'type',
        'channel',
        'total_formatted',
        'status_badge',
        'descuadre',
        'origen',
        'external_order_id',
    ]
    list_filter = ['status', 'type', 'channel', 'integration']
    search_fields = [
        'voucher_id', 'external_order_id', 'related_voucher_id', 'coupon_code',
    ]
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'

    readonly_fields = [
        'integration',
        'voucher_id',
        'type',
        'related_voucher_id',
        'external_order_id',
        'channel',
        'date',
        'total',
        'sale_origin',
        'app_origin',
        'coupon_code',
        'coupon_discount',
        'cupon_app',
        'total_discrepancy',
        'payload',
        'status',
        'error_message',
        'transactions',
        'processed_at',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Vouchers only arrive through the sync, never by hand"""
        return False

    def total_formatted(self, obj):
        if obj.total is None:
            return '-'
        # The number is formatted before being handed to `format_html`: it
        # escapes every argument to a SafeString first, so a numeric spec like
        # ',.2f' applied inside the template raises ValueError.
        return format_html('${}', f'{obj.total:,.2f}')
    total_formatted.short_description = 'Total'

    def descuadre(self, obj):
        """
        Whether our breakdown adds up to what Conto says the customer paid.

        A difference means the income was recorded but split wrong, which is the
        kind of thing that never surfaces on its own.
        """
        if obj.total_discrepancy is None:
            return format_html(
                '<span style="color: #065F46;">cuadra</span>'
            )
        return format_html(
            '<span style="background-color: #FEE2E2; color: #DC2626; '
            'padding: 3px 8px; border-radius: 4px;">{}</span>',
            f'{obj.total_discrepancy:+,.2f}'
        )
    descuadre.short_description = 'Descuadre'

    def origen(self, obj):
        """
        Si la venta vino de la app.

        No sale de `origen_venta` —una compra desde la app llega como `store`,
        igual que una del navegador— sino del cupón (§6.3).
        """
        if not obj.cupon_app_id:
            return '—'
        return format_html(
            '<span style="background-color: #E8D1CD; color: #1F1F1F; '
            'padding: 3px 8px; border-radius: 4px;">app</span>'
        )
    origen.short_description = 'Origen'

    def status_badge(self, obj):
        colors = {
            'PROCESSED': ('#D1FAE5', '#065F46'),
            'PENDING': ('#FEF3C7', '#92400E'),
            'ERROR': ('#FEE2E2', '#DC2626'),
            'SKIPPED': ('#F3F4F6', '#6B7280'),
        }
        background, color = colors.get(obj.status, ('#F3F4F6', '#6B7280'))
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 4px;">{}</span>',
            background,
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'


@admin.register(TiendanubeIntegration)
class TiendanubeIntegrationAdmin(admin.ModelAdmin):
    """
    Read-only view of the Tienda Nube link.

    Not editable by hand on purpose: the token comes from the OAuth exchange,
    and one typed by a human is a token that works until the first coupon.
    Para vincular, se arranca la instalación desde «Instalaciones de Tienda
    Nube iniciadas» y la vuelta la resuelve el callback;
    `python manage.py vincular_tiendanube` es el camino de atrás.
    """
    list_display = ['center', 'store_id', 'store_name', 'is_active', 'installed_at']
    list_filter = ['is_active']
    search_fields = ['store_id', 'store_name', 'center__nombre']

    readonly_fields = [
        'center', 'store_id', 'store_name', 'scope',
        'installed_at', 'uninstalled_at', 'created_at', 'updated_at',
    ]
    # El token no se muestra nunca, ni siquiera como readonly.
    exclude = ['token']

    def has_add_permission(self, request):
        return False


@admin.register(CuponApp)
class CuponAppAdmin(admin.ModelAdmin):
    """
    Los cupones emitidos por la app.

    Sirve para dos preguntas: qué se emitió y a quién, y cuántos quedaron sin
    usar — que es la tasa de compras que se empiezan y no se terminan.
    """
    list_display = ['code', 'cliente', 'percentage', 'estado', 'issued_at', 'expires_at']
    list_filter = ['integration', 'issued_at']
    search_fields = ['code', 'cliente__nombre', 'cliente__apellido']
    date_hierarchy = 'issued_at'
    readonly_fields = [
        'integration', 'cliente', 'code', 'percentage', 'tiendanube_coupon_id',
        'issued_at', 'expires_at', 'used_at', 'revoked_at', 'created_at',
    ]

    def has_add_permission(self, request):
        """Los cupones los emite la app al tocar «Comprar», nunca una persona."""
        return False

    def estado(self, obj):
        if obj.used_at:
            return format_html('<span style="color: #065F46;">usado</span>')
        if obj.revoked_at:
            return format_html('<span style="color: #6B7280;">borrado de TN</span>')
        if obj.esta_vencido:
            return format_html('<span style="color: #92400E;">vencido</span>')
        return format_html('<span style="color: #1D4ED8;">vigente</span>')
    estado.short_description = 'Estado'


@admin.register(TiendanubePrivacyRequest)
class TiendanubePrivacyRequestAdmin(admin.ModelAdmin):
    """
    Los pedidos de privacidad que llegan por webhook.

    Existe porque dos de los tres los tiene que contestar una persona: Tienda
    Nube dice que es responsabilidad de la app mandarle el informe al centro.
    Sin una pantalla, un pedido contestado con 200 no se distingue de uno
    atendido.

    Los de tienda se resuelven solos al llegar. Los de comprador quedan abiertos
    hasta que alguien los cierra con la acción de abajo.
    """
    list_display = ['received_at', 'event', 'store_id', 'integration', 'estado']
    list_filter = ['event', 'handled_at']
    search_fields = ['store_id', 'notes']
    date_hierarchy = 'received_at'
    readonly_fields = [
        'integration', 'store_id', 'event', 'payload', 'received_at',
    ]
    actions = ['marcar_resuelto']

    def has_add_permission(self, request):
        """Los pedidos los crea Tienda Nube por webhook, nunca una persona."""
        return False

    def estado(self, obj):
        if obj.handled_at:
            return format_html('<span style="color: #065F46;">resuelto</span>')
        return format_html('<span style="color: #92400E;">pendiente</span>')
    estado.short_description = 'Estado'

    @admin.action(description='Marcar como resuelto')
    def marcar_resuelto(self, request, queryset):
        actualizados = queryset.filter(handled_at__isnull=True).update(
            handled_at=timezone.now()
        )
        self.message_user(
            request,
            f'{actualizados} pedido(s) marcados como resueltos.',
            messages.SUCCESS,
        )


@admin.register(TiendanubeInstallIntent)
class TiendanubeInstallIntentAdmin(admin.ModelAdmin):
    """
    Por acá se arranca una instalación de la app en la tienda de un centro.

    Es la pantalla que compensa un agujero de Tienda Nube: **su OAuth no acepta
    un `state`**, así que cuando el token vuelve no hay nada en el pedido que
    diga de qué centro es. Guardar acá quién está instalando, antes de mandar a
    Tienda Nube, es lo que después le permite al callback resolverlo sin
    adivinar (`instalacion.resolver_centro`).

    Vive en el admin y no en el CRM porque acá es donde se administran las
    integraciones en este proyecto — el token de Conto se carga por el mismo
    camino. Guardar redirige derecho a Tienda Nube.
    """
    list_display = ['center', 'created_by', 'created_at', 'expires_at', 'estado']
    list_filter = ['center']
    # Lo único que se elige es el centro; lo demás lo pone el sistema.
    fields = ['center']
    readonly_fields = ['created_by', 'created_at', 'expires_at', 'consumed_at']

    def has_change_permission(self, request, obj=None):
        """Una intención es un hecho con fecha, no algo que se edite."""
        return False

    def estado(self, obj):
        if obj.consumed_at:
            return format_html('<span style="color: #065F46;">completada</span>')
        if obj.esta_abierta:
            return format_html('<span style="color: #1D4ED8;">esperando a Tienda Nube</span>')
        return format_html('<span style="color: #6B7280;">vencida</span>')
    estado.short_description = 'Estado'

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.expires_at = timezone.now() + VENTANA_DE_INSTALACION
        cerrar_intentos_abiertos(obj.center)
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Mandar a la persona directo a Tienda Nube.

        El paso siguiente es autorizar la app con una cuenta que administre la
        tienda, y la intención recién guardada dura pocos minutos: devolverla al
        listado sería devolverla a un reloj corriendo.
        """
        app_id = getattr(settings, 'TIENDANUBE_CLIENT_ID', '')
        if not app_id:
            self.message_user(
                request,
                'Falta TIENDANUBE_CLIENT_ID en el entorno, así que no se puede '
                'abrir la instalación. Sale de «Claves de Acceso» en el panel '
                'de partners.',
                messages.ERROR,
            )
            return super().response_add(request, obj, post_url_continue)

        self.message_user(
            request,
            f'Autorizá la app con una cuenta que administre la tienda de '
            f'«{obj.center.nombre}». Tenés hasta las '
            f'{timezone.localtime(obj.expires_at):%H:%M}.',
            messages.INFO,
        )
        return HttpResponseRedirect(AUTHORIZE_URL.format(app_id=app_id))

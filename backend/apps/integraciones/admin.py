"""
Django Admin for the Conto integration.

This is intentionally usable on its own: it lets an admin load the Conto token
and configure the integration before the frontend screen exists.
"""
from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import ContoIntegration, ContoSale


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
        'external_order_id',
    ]
    list_filter = ['status', 'type', 'channel', 'integration']
    search_fields = ['voucher_id', 'external_order_id', 'related_voucher_id']
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
        return format_html('${:,.2f}', obj.total)
    total_formatted.short_description = 'Total'

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

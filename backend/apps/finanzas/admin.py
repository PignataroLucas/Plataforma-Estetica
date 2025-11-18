from django.contrib import admin
from django.utils.html import format_html
from .models import TransactionCategory, Transaction, AccountReceivable


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'type',
        'parent_category',
        'colored_badge',
        'is_active',
        'is_system_category',
        'transaction_count',
        'created_at'
    ]
    list_filter = ['type', 'is_active', 'is_system_category', 'branch']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'transaction_count']
    fieldsets = (
        ('Basic Information', {
            'fields': ('branch', 'name', 'type', 'parent_category', 'description')
        }),
        ('Display Settings', {
            'fields': ('color', 'icon', 'order')
        }),
        ('Configuration', {
            'fields': ('is_active', 'is_system_category', 'created_by')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'transaction_count'),
            'classes': ('collapse',)
        }),
    )

    def colored_badge(self, obj):
        """Display color as a badge"""
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.color
        )
    colored_badge.short_description = 'Color'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'type',
        'category',
        'description',
        'formatted_amount',
        'payment_method',
        'auto_generated',
        'created_at'
    ]
    list_filter = [
        'type',
        'payment_method',
        'auto_generated',
        'date',
        'branch',
        'category'
    ]
    search_fields = ['description', 'notes', 'receipt_number']
    readonly_fields = ['created_at', 'updated_at', 'signed_amount', 'can_be_edited', 'can_be_deleted']
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('branch', 'type', 'category', 'date', 'amount', 'payment_method')
        }),
        ('Details', {
            'fields': ('description', 'notes')
        }),
        ('Related Entities', {
            'fields': ('client', 'appointment', 'product', 'inventory_movement'),
            'classes': ('collapse',)
        }),
        ('Receipt/Invoice', {
            'fields': ('receipt_number', 'receipt_file'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('auto_generated', 'registered_by', 'edited_by')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'signed_amount', 'can_be_edited', 'can_be_deleted'),
            'classes': ('collapse',)
        }),
    )

    def formatted_amount(self, obj):
        """Display amount with color based on income/expense"""
        color = 'green' if obj.is_income else 'red'
        sign = '+' if obj.is_income else '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ${:,.2f}</span>',
            color,
            sign,
            obj.amount
        )
    formatted_amount.short_description = 'Amount'


@admin.register(AccountReceivable)
class AccountReceivableAdmin(admin.ModelAdmin):
    list_display = [
        'client',
        'issue_date',
        'due_date',
        'formatted_total',
        'formatted_paid',
        'formatted_pending',
        'is_paid',
        'is_overdue'
    ]
    list_filter = ['is_paid', 'branch', 'issue_date', 'due_date']
    search_fields = ['client__full_name', 'description', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'pending_amount', 'is_overdue']
    date_hierarchy = 'issue_date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('client', 'branch', 'appointment', 'issue_date', 'due_date')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'paid_amount', 'pending_amount')
        }),
        ('Details', {
            'fields': ('description', 'notes')
        }),
        ('Status', {
            'fields': ('is_paid', 'full_payment_date', 'is_overdue')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formatted_total(self, obj):
        """Format total amount"""
        return f'${obj.total_amount:,.2f}'
    formatted_total.short_description = 'Total'

    def formatted_paid(self, obj):
        """Format paid amount in green"""
        return format_html(
            '<span style="color: green;">${:,.2f}</span>',
            obj.paid_amount
        )
    formatted_paid.short_description = 'Paid'

    def formatted_pending(self, obj):
        """Format pending amount in red if overdue"""
        color = 'red' if obj.is_overdue else 'orange'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:,.2f}</span>',
            color,
            obj.pending_amount
        )
    formatted_pending.short_description = 'Pending'

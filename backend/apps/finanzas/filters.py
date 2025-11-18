"""
Custom filters for financial module
Provides advanced filtering capabilities for transactions
"""
from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Transaction, TransactionCategory, AccountReceivable


class TransactionFilter(filters.FilterSet):
    """
    Advanced filters for Transaction model
    """
    # Date range filters
    date_from = filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='date', lookup_expr='lte')
    date_year = filters.NumberFilter(field_name='date', lookup_expr='year')
    date_month = filters.NumberFilter(field_name='date', lookup_expr='month')

    # Amount range filters
    amount_min = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = filters.NumberFilter(field_name='amount', lookup_expr='lte')

    # Type filters
    is_income = filters.BooleanFilter(method='filter_is_income')
    is_expense = filters.BooleanFilter(method='filter_is_expense')

    # Category filters
    category_id = filters.NumberFilter(field_name='category__id')
    category_name = filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    parent_category = filters.NumberFilter(field_name='category__parent_category__id')

    # Search filter
    search = filters.CharFilter(method='filter_search')

    # Auto-generated filter
    auto_generated = filters.BooleanFilter(field_name='auto_generated')

    # Client filter
    client_id = filters.NumberFilter(field_name='client__id')

    class Meta:
        model = Transaction
        fields = [
            'type',
            'payment_method',
            'branch',
            'date',
            'category',
        ]

    def filter_is_income(self, queryset, name, value):
        """Filter by income transactions"""
        if value:
            return queryset.filter(type__startswith='INCOME_')
        return queryset.exclude(type__startswith='INCOME_')

    def filter_is_expense(self, queryset, name, value):
        """Filter by expense transactions"""
        if value:
            return queryset.filter(type='EXPENSE')
        return queryset.exclude(type='EXPENSE')

    def filter_search(self, queryset, name, value):
        """
        Search across description, notes, receipt_number, category name
        """
        return queryset.filter(
            Q(description__icontains=value) |
            Q(notes__icontains=value) |
            Q(receipt_number__icontains=value) |
            Q(category__name__icontains=value) |
            Q(client__full_name__icontains=value)
        )


class TransactionCategoryFilter(filters.FilterSet):
    """
    Filters for TransactionCategory model
    """
    # Type filter
    type = filters.ChoiceFilter(choices=TransactionCategory.CategoryType.choices)

    # Active/inactive filter
    is_active = filters.BooleanFilter(field_name='is_active')

    # System category filter
    is_system_category = filters.BooleanFilter(field_name='is_system_category')

    # Parent category filter (to get only main categories or only subcategories)
    is_main_category = filters.BooleanFilter(method='filter_is_main_category')
    parent_category_id = filters.NumberFilter(field_name='parent_category__id')

    # Search filter
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = TransactionCategory
        fields = ['branch', 'type']

    def filter_is_main_category(self, queryset, name, value):
        """Filter to get only main categories (no parent)"""
        if value:
            return queryset.filter(parent_category__isnull=True)
        return queryset.filter(parent_category__isnull=False)

    def filter_search(self, queryset, name, value):
        """Search by category name or description"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )


class AccountReceivableFilter(filters.FilterSet):
    """
    Filters for AccountReceivable model
    """
    # Date range filters
    issue_date_from = filters.DateFilter(field_name='issue_date', lookup_expr='gte')
    issue_date_to = filters.DateFilter(field_name='issue_date', lookup_expr='lte')
    due_date_from = filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = filters.DateFilter(field_name='due_date', lookup_expr='lte')

    # Amount filters
    total_amount_min = filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_max = filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    pending_amount_min = filters.NumberFilter(field_name='pending_amount', lookup_expr='gte')
    pending_amount_max = filters.NumberFilter(field_name='pending_amount', lookup_expr='lte')

    # Status filters
    is_paid = filters.BooleanFilter(field_name='is_paid')
    is_overdue = filters.BooleanFilter(method='filter_is_overdue')

    # Client filter
    client_id = filters.NumberFilter(field_name='client__id')
    client_name = filters.CharFilter(field_name='client__full_name', lookup_expr='icontains')

    # Search filter
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = AccountReceivable
        fields = ['branch', 'is_paid']

    def filter_is_overdue(self, queryset, name, value):
        """Filter by overdue status (using property from model)"""
        from django.utils import timezone
        today = timezone.now().date()

        if value:
            # Overdue: due_date < today AND not paid
            return queryset.filter(
                due_date__lt=today,
                is_paid=False
            )
        else:
            # Not overdue: due_date >= today OR already paid
            return queryset.filter(
                Q(due_date__gte=today) | Q(is_paid=True)
            )

    def filter_search(self, queryset, name, value):
        """Search across description, notes, client name"""
        return queryset.filter(
            Q(description__icontains=value) |
            Q(notes__icontains=value) |
            Q(client__full_name__icontains=value)
        )

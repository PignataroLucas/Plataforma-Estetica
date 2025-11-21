from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import TransactionCategory, Transaction, AccountReceivable
from apps.empleados.models import Usuario
from .serializers import (
    TransactionCategorySerializer,
    TransactionCategoryListSerializer,
    TransactionSerializer,
    TransactionListSerializer,
    AccountReceivableSerializer
)
from .permissions import (
    IsAdminOrOwner,
    CanEditTransaction,
    CanDeleteTransaction,
    CanManageCategory,
    BelongsToUserBranch
)
from .filters import (
    TransactionFilter,
    TransactionCategoryFilter,
    AccountReceivableFilter
)


class TransactionCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transaction categories

    Endpoints:
    - GET /api/finanzas/categories/ - List all categories
    - POST /api/finanzas/categories/ - Create new category
    - GET /api/finanzas/categories/{id}/ - Get category details
    - PUT/PATCH /api/finanzas/categories/{id}/ - Update category
    - DELETE /api/finanzas/categories/{id}/ - Delete category (if allowed)
    - GET /api/finanzas/categories/tree/ - Get hierarchical tree view
    """
    queryset = TransactionCategory.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrOwner, CanManageCategory]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TransactionCategoryFilter
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['type', 'order', 'name']
    search_fields = ['name', 'description']
    pagination_class = None  # Return all categories without pagination

    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return TransactionCategoryListSerializer
        return TransactionCategorySerializer

    def get_queryset(self):
        """Filter by user's branch"""
        queryset = super().get_queryset()

        # Superuser can see all
        if self.request.user.is_superuser:
            return queryset

        # Filter by user's branch
        if hasattr(self.request.user, 'sucursal'):
            queryset = queryset.filter(branch=self.request.user.sucursal)

        return queryset

    def perform_create(self, serializer):
        """Automatically set branch from user's sucursal"""
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            serializer.save(branch=user.sucursal)
        else:
            # For superusers, use first available branch
            from apps.empleados.models import Sucursal
            branch = Sucursal.objects.first()
            serializer.save(branch=branch)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get categories in hierarchical tree structure
        Returns main categories with nested subcategories
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Get only main categories (no parent)
        main_categories = queryset.filter(parent_category__isnull=True)

        serializer = TransactionCategorySerializer(
            main_categories,
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Get categories grouped by type (INCOME/EXPENSE)
        """
        queryset = self.filter_queryset(self.get_queryset())

        income_categories = queryset.filter(
            type='INCOME',
            parent_category__isnull=True
        )
        expense_categories = queryset.filter(
            type='EXPENSE',
            parent_category__isnull=True
        )

        return Response({
            'income': TransactionCategorySerializer(
                income_categories,
                many=True,
                context={'request': request}
            ).data,
            'expense': TransactionCategorySerializer(
                expense_categories,
                many=True,
                context={'request': request}
            ).data
        })


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing financial transactions

    Endpoints:
    - GET /api/finanzas/transactions/ - List all transactions
    - POST /api/finanzas/transactions/ - Create new transaction
    - GET /api/finanzas/transactions/{id}/ - Get transaction details
    - PUT/PATCH /api/finanzas/transactions/{id}/ - Update transaction
    - DELETE /api/finanzas/transactions/{id}/ - Delete transaction
    - GET /api/finanzas/transactions/summary/ - Get financial summary
    - GET /api/finanzas/transactions/by_category/ - Breakdown by category
    """
    queryset = Transaction.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsAdminOrOwner,
        CanEditTransaction,
        CanDeleteTransaction
    ]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TransactionFilter
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']
    search_fields = ['description', 'notes', 'receipt_number']

    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer

    def get_queryset(self):
        """Filter by user's branch and optimize queries"""
        queryset = super().get_queryset()

        # Optimize queries with select_related and prefetch_related
        queryset = queryset.select_related(
            'category',
            'category__parent_category',
            'client',
            'registered_by',
            'branch'
        )

        # Superuser can see all
        if self.request.user.is_superuser:
            return queryset

        # Filter by user's branch
        if hasattr(self.request.user, 'sucursal'):
            queryset = queryset.filter(branch=self.request.user.sucursal)

        return queryset

    def perform_create(self, serializer):
        """Automatically set branch from user's sucursal"""
        user = self.request.user
        if hasattr(user, 'sucursal') and user.sucursal:
            serializer.save(branch=user.sucursal)
        else:
            # For superusers, use first available branch
            from apps.empleados.models import Sucursal
            branch = Sucursal.objects.first()
            serializer.save(branch=branch)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get financial summary for a period
        Query params:
        - date_from: Start date (default: first day of current month)
        - date_to: End date (default: today)
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Calculate totals
        income_total = queryset.filter(
            type__startswith='INCOME_'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        expense_total = queryset.filter(
            type='EXPENSE'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        balance = income_total - expense_total

        # Calculate counts
        income_count = queryset.filter(type__startswith='INCOME_').count()
        expense_count = queryset.filter(type='EXPENSE').count()

        return Response({
            'income': {
                'total': float(income_total),
                'count': income_count
            },
            'expense': {
                'total': float(expense_total),
                'count': expense_count
            },
            'balance': float(balance),
            'profit_margin': float((balance / income_total * 100) if income_total > 0 else 0)
        })

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Get transactions breakdown by category
        Returns amount and count per category
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Group by category
        by_category = queryset.values(
            'category__id',
            'category__name',
            'category__color',
            'type'
        ).annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')

        return Response(list(by_category))

    @action(detail=False, methods=['get'])
    def by_payment_method(self, request):
        """
        Get transactions breakdown by payment method
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Group by payment method
        by_method = queryset.values(
            'payment_method'
        ).annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')

        # Add display names
        for item in by_method:
            choices_dict = dict(Transaction.PaymentMethod.choices)
            item['payment_method_display'] = choices_dict.get(
                item['payment_method'],
                item['payment_method']
            )

        return Response(list(by_method))

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent transactions (last 10)
        """
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = TransactionListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def process_salaries(self, request):
        """
        Process monthly salaries for all employees with sueldo_mensual > 0
        Creates EXPENSE transactions for each employee

        Query params:
        - month: Month number (1-12), default: current month
        - year: Year (e.g., 2024), default: current year
        """
        # Get month and year from request
        today = timezone.now().date()
        month = int(request.data.get('month', today.month))
        year = int(request.data.get('year', today.year))

        # Get user's branch
        branch = None
        if hasattr(request.user, 'sucursal') and request.user.sucursal:
            branch = request.user.sucursal
        else:
            # For superusers, use first branch
            from apps.empleados.models import Sucursal
            branch = Sucursal.objects.first()

        if not branch:
            return Response(
                {'error': 'No se encontró una sucursal válida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create "Sueldos" category
        salary_category, created = TransactionCategory.objects.get_or_create(
            branch=branch,
            name='Sueldos',
            type='EXPENSE',
            defaults={
                'description': 'Sueldos de empleados',
                'color': '#FF6B6B',
                'is_system_category': True
            }
        )

        # Get all active employees with salary in the same centro_estetica
        employees = Usuario.objects.filter(
            centro_estetica=branch.centro_estetica,
            activo=True,
            sueldo_mensual__gt=0
        )

        # Check if salaries were already processed for this month
        month_start = timezone.datetime(year, month, 1).date()
        existing_transactions = Transaction.objects.filter(
            branch=branch,
            category=salary_category,
            date__year=year,
            date__month=month,
            description__contains='Sueldo de'
        )

        if existing_transactions.exists():
            return Response({
                'error': f'Los sueldos del mes {month}/{year} ya fueron procesados',
                'processed_count': 0,
                'total_amount': 0,
                'transactions': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create transactions for each employee
        created_transactions = []
        total_amount = Decimal('0')

        for employee in employees:
            transaction = Transaction.objects.create(
                branch=branch,
                category=salary_category,
                type='EXPENSE',
                amount=employee.sueldo_mensual,
                payment_method='BANK_TRANSFER',
                date=month_start,
                description=f'Sueldo de {employee.get_full_name()} - {month}/{year}',
                notes=f'Procesado automáticamente el {today}',
                registered_by=request.user
            )
            created_transactions.append({
                'id': transaction.id,
                'employee': employee.get_full_name(),
                'amount': float(employee.sueldo_mensual)
            })
            total_amount += employee.sueldo_mensual

        return Response({
            'message': f'Se procesaron {len(created_transactions)} sueldos correctamente',
            'processed_count': len(created_transactions),
            'total_amount': float(total_amount),
            'month': month,
            'year': year,
            'transactions': created_transactions
        })


class AccountReceivableViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing accounts receivable (client debts)

    Endpoints:
    - GET /api/finanzas/accounts-receivable/ - List all accounts receivable
    - POST /api/finanzas/accounts-receivable/ - Create new account
    - GET /api/finanzas/accounts-receivable/{id}/ - Get details
    - PUT/PATCH /api/finanzas/accounts-receivable/{id}/ - Update
    - DELETE /api/finanzas/accounts-receivable/{id}/ - Delete
    - GET /api/finanzas/accounts-receivable/overdue/ - Get overdue accounts
    - GET /api/finanzas/accounts-receivable/summary/ - Get summary
    """
    queryset = AccountReceivable.objects.all()
    serializer_class = AccountReceivableSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner, BelongsToUserBranch]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = AccountReceivableFilter
    ordering_fields = ['issue_date', 'due_date', 'total_amount', 'pending_amount']
    ordering = ['-issue_date']
    search_fields = ['description', 'notes', 'client__full_name']

    def get_queryset(self):
        """Filter by user's branch and optimize queries"""
        queryset = super().get_queryset()

        # Optimize queries
        queryset = queryset.select_related('client', 'branch')

        # Superuser can see all
        if self.request.user.is_superuser:
            return queryset

        # Filter by user's branch
        if hasattr(self.request.user, 'sucursal'):
            queryset = queryset.filter(branch=self.request.user.sucursal)

        return queryset

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Get all overdue accounts (past due date and not paid)
        """
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            due_date__lt=today,
            is_paid=False
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get summary of accounts receivable
        - Total owed
        - Total paid
        - Total pending
        - Count of overdue accounts
        """
        queryset = self.filter_queryset(self.get_queryset())

        today = timezone.now().date()

        # Calculate totals
        totals = queryset.aggregate(
            total_owed=Sum('total_amount'),
            total_paid=Sum('paid_amount'),
            total_pending=Sum('pending_amount')
        )

        # Count overdue
        overdue_count = queryset.filter(
            due_date__lt=today,
            is_paid=False
        ).count()

        # Count by status
        paid_count = queryset.filter(is_paid=True).count()
        pending_count = queryset.filter(is_paid=False).count()

        return Response({
            'total_owed': float(totals['total_owed'] or 0),
            'total_paid': float(totals['total_paid'] or 0),
            'total_pending': float(totals['total_pending'] or 0),
            'overdue_count': overdue_count,
            'paid_count': paid_count,
            'pending_count': pending_count
        })

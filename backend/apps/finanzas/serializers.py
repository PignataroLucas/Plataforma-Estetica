from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import TransactionCategory, Transaction, AccountReceivable
from apps.clientes.models import Cliente
from apps.empleados.models import Sucursal


class TransactionCategoryListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing categories (used in dropdowns/selects)
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    subcategory_count = serializers.IntegerField(
        source='subcategories.count',
        read_only=True
    )

    class Meta:
        model = TransactionCategory
        fields = [
            'id',
            'name',
            'type',
            'type_display',
            'color',
            'icon',
            'is_active',
            'is_system_category',
            'parent_category',
            'subcategory_count',
            'full_path'
        ]
        read_only_fields = ['full_path', 'type_display', 'subcategory_count']


class TransactionCategorySerializer(serializers.ModelSerializer):
    """
    Full serializer for transaction categories with nested subcategories
    """
    # Make branch not required - will be set by perform_create
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Sucursal.objects.all(),
        required=False,
        allow_null=True,
        default=None
    )
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    parent_category_name = serializers.CharField(
        source='parent_category.name',
        read_only=True,
        allow_null=True
    )
    subcategories = TransactionCategoryListSerializer(many=True, read_only=True)
    transaction_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TransactionCategory
        fields = [
            'id',
            'branch',
            'name',
            'type',
            'type_display',
            'description',
            'color',
            'icon',
            'parent_category',
            'parent_category_name',
            'is_active',
            'is_system_category',
            'order',
            'subcategories',
            'transaction_count',
            'full_path',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'full_path',
            'type_display',
            'transaction_count',
            'parent_category_name',
            'created_at',
            'updated_at'
        ]
        extra_kwargs = {
            'parent_category': {'required': False, 'allow_null': True, 'default': None},  # Optional for main categories
        }

    def validate(self, data):
        """Validate category data"""
        # Prevent creating subcategories of subcategories (max 2 levels)
        if data.get('parent_category') and data['parent_category'].parent_category:
            raise serializers.ValidationError({
                'parent_category': 'No se pueden crear subcategorías de subcategorías. Máximo 2 niveles.'
            })

        # Ensure type matches parent category type
        if data.get('parent_category'):
            if data.get('type') != data['parent_category'].type:
                raise serializers.ValidationError({
                    'type': 'El tipo debe coincidir con el tipo de la categoría padre.'
                })

        return data

    def validate_name(self, value):
        """Validate category name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError('El nombre de la categoría no puede estar vacío.')
        return value.strip()


class TransactionSerializer(serializers.ModelSerializer):
    """
    Full serializer for transactions
    """
    # Make branch optional - will be set by perform_create
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Sucursal.objects.all(),
        required=False,
        allow_null=True
    )

    # Read-only display fields
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )
    category_name = serializers.CharField(source='category.full_path', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True, allow_null=True)
    registered_by_name = serializers.CharField(
        source='registered_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    # Computed fields
    signed_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    can_be_edited = serializers.BooleanField(read_only=True)
    can_be_deleted = serializers.BooleanField(read_only=True)
    is_income = serializers.BooleanField(read_only=True)
    is_expense = serializers.BooleanField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'branch',
            'category',
            'category_name',
            'category_color',
            'client',
            'client_name',
            'appointment',
            'product',
            'inventory_movement',
            'type',
            'type_display',
            'amount',
            'signed_amount',
            'payment_method',
            'payment_method_display',
            'date',
            'description',
            'notes',
            'receipt_number',
            'receipt_file',
            'auto_generated',
            'registered_by',
            'registered_by_name',
            'edited_by',
            'is_income',
            'is_expense',
            'can_be_edited',
            'can_be_deleted',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'type_display',
            'payment_method_display',
            'category_name',
            'category_color',
            'client_name',
            'registered_by_name',
            'signed_amount',
            'can_be_edited',
            'can_be_deleted',
            'is_income',
            'is_expense',
            'auto_generated',
            'inventory_movement',
            'created_at',
            'updated_at'
        ]

    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError('El monto debe ser mayor a cero.')
        if value > Decimal('9999999.99'):
            raise serializers.ValidationError('El monto no puede exceder $9,999,999.99.')
        return value

    def validate_date(self, value):
        """Validate transaction date"""
        today = timezone.now().date()

        # Warning for future dates (don't block, just warn in response)
        if value > today:
            # Note: In a real app, you might want to add this to context
            pass

        # Warning for dates older than 30 days
        age_in_days = (today - value).days
        if age_in_days > 30:
            # This is just a warning, not blocking
            pass

        return value

    def validate_description(self, value):
        """Validate description is not empty and has minimum length"""
        if not value or not value.strip():
            raise serializers.ValidationError('La descripción no puede estar vacía.')
        if len(value.strip()) < 5:
            raise serializers.ValidationError('La descripción debe tener al menos 5 caracteres.')
        return value.strip()

    def validate(self, data):
        """Cross-field validation"""
        # Ensure category belongs to the same branch
        if data.get('category') and data.get('branch'):
            if data['category'].branch != data['branch']:
                raise serializers.ValidationError({
                    'category': 'La categoría debe pertenecer a la misma sucursal.'
                })

        # Ensure category type matches transaction type
        if data.get('category') and data.get('type'):
            if data['type'] == 'EXPENSE' and data['category'].type != 'EXPENSE':
                raise serializers.ValidationError({
                    'category': 'Debe seleccionar una categoría de tipo Gasto.'
                })
            if data['type'].startswith('INCOME_') and data['category'].type != 'INCOME':
                raise serializers.ValidationError({
                    'category': 'Debe seleccionar una categoría de tipo Ingreso.'
                })

        # Client is mainly for income transactions
        if data.get('client') and data.get('type') == 'EXPENSE':
            # This is just a warning, not blocking
            pass

        return data

    def create(self, validated_data):
        """Override create to set registered_by from request user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['registered_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Override update to set edited_by from request user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['edited_by'] = request.user

        # Prevent editing auto-generated transactions
        if instance.auto_generated:
            raise serializers.ValidationError(
                'No se pueden editar transacciones auto-generadas. '
                'Edite el movimiento de inventario asociado.'
            )

        # Prevent editing old transactions
        if not instance.can_be_edited:
            raise serializers.ValidationError(
                'No se pueden editar transacciones con más de 30 días de antigüedad.'
            )

        return super().update(instance, validated_data)


class TransactionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing transactions (optimized for performance)
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )
    category_name = serializers.CharField(source='category.full_path', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True, allow_null=True)
    registered_by_name = serializers.CharField(
        source='registered_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    signed_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id',
            'type',
            'type_display',
            'category_name',
            'amount',
            'signed_amount',
            'payment_method_display',
            'date',
            'description',
            'client_name',
            'registered_by_name',
            'auto_generated',
            'created_at'
        ]


class AccountReceivableSerializer(serializers.ModelSerializer):
    """
    Serializer for accounts receivable
    """
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    branch_name = serializers.CharField(source='branch.nombre', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = AccountReceivable
        fields = [
            'id',
            'client',
            'client_name',
            'branch',
            'branch_name',
            'appointment',
            'total_amount',
            'paid_amount',
            'pending_amount',
            'issue_date',
            'due_date',
            'full_payment_date',
            'description',
            'notes',
            'is_paid',
            'is_overdue',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'client_name',
            'branch_name',
            'pending_amount',
            'is_paid',
            'is_overdue',
            'full_payment_date',
            'created_at',
            'updated_at'
        ]

    def validate_total_amount(self, value):
        """Validate total amount is positive"""
        if value <= 0:
            raise serializers.ValidationError('El monto total debe ser mayor a cero.')
        return value

    def validate_paid_amount(self, value):
        """Validate paid amount is not negative"""
        if value < 0:
            raise serializers.ValidationError('El monto pagado no puede ser negativo.')
        return value

    def validate(self, data):
        """Cross-field validation"""
        # Ensure paid amount doesn't exceed total amount
        total = data.get('total_amount', 0)
        paid = data.get('paid_amount', 0)

        if paid > total:
            raise serializers.ValidationError({
                'paid_amount': 'El monto pagado no puede exceder el monto total.'
            })

        # Ensure due date is after issue date
        if data.get('due_date') and data.get('issue_date'):
            if data['due_date'] < data['issue_date']:
                raise serializers.ValidationError({
                    'due_date': 'La fecha de vencimiento debe ser posterior a la fecha de emisión.'
                })

        return data

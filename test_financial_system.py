"""
Test script for the Financial System
Run with: docker-compose exec backend python test_financial_system.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.finanzas.models import TransactionCategory, Transaction
from apps.empleados.models import Sucursal
from decimal import Decimal

def test_financial_system():
    print("\n" + "="*60)
    print("🧪 TESTING FINANCIAL SYSTEM")
    print("="*60 + "\n")

    # Test 1: Check categories were populated
    print("📋 TEST 1: Check Default Categories")
    print("-" * 60)

    branch = Sucursal.objects.first()
    if not branch:
        print("❌ ERROR: No branch found. Create a branch first.")
        return

    print(f"✅ Found branch: {branch.nombre}")

    expense_categories = TransactionCategory.objects.filter(
        branch=branch,
        type='EXPENSE',
        parent_category__isnull=True
    )

    print(f"\n📊 Main EXPENSE Categories: {expense_categories.count()}")
    for cat in expense_categories:
        subcats = cat.subcategories.count()
        print(f"  ├─ {cat.name} ({cat.color}) - {subcats} subcategories")
        for subcat in cat.subcategories.all()[:2]:
            print(f"  │  └─ {subcat.name}")
        if subcats > 2:
            print(f"  │  └─ ... and {subcats - 2} more")

    income_categories = TransactionCategory.objects.filter(
        branch=branch,
        type='INCOME',
        parent_category__isnull=True
    )

    print(f"\n💰 Main INCOME Categories: {income_categories.count()}")
    for cat in income_categories:
        subcats = cat.subcategories.count()
        print(f"  ├─ {cat.name} ({cat.color}) - {subcats} subcategories")

    # Test 2: Create a test expense transaction
    print("\n" + "="*60)
    print("📋 TEST 2: Create Test Expense Transaction")
    print("-" * 60)

    try:
        # Get a category
        utilities_cat = TransactionCategory.objects.filter(
            branch=branch,
            name='Utilities',
            type='EXPENSE'
        ).first()

        if not utilities_cat:
            print("❌ ERROR: Utilities category not found")
            return

        # Try to get electricity subcategory
        electricity_subcat = utilities_cat.subcategories.filter(
            name='Electricity'
        ).first()

        category_to_use = electricity_subcat if electricity_subcat else utilities_cat

        # Create transaction
        transaction = Transaction.objects.create(
            branch=branch,
            category=category_to_use,
            type='EXPENSE',
            amount=Decimal('3500.00'),
            date='2025-11-17',
            description='Electric bill - November 2025',
            payment_method='TRANSFER',
            auto_generated=False
        )

        print(f"✅ Created expense transaction:")
        print(f"   ID: {transaction.id}")
        print(f"   Category: {transaction.category.full_path}")
        print(f"   Amount: ${transaction.amount}")
        print(f"   Signed Amount: ${transaction.signed_amount}")
        print(f"   Is Expense: {transaction.is_expense}")
        print(f"   Can be edited: {transaction.can_be_edited}")
        print(f"   Can be deleted: {transaction.can_be_deleted}")

        # Test 3: Create a test income transaction
        print("\n" + "="*60)
        print("📋 TEST 3: Create Test Income Transaction")
        print("-" * 60)

        services_cat = TransactionCategory.objects.filter(
            branch=branch,
            name='Services',
            type='INCOME'
        ).first()

        if services_cat:
            income_transaction = Transaction.objects.create(
                branch=branch,
                category=services_cat,
                type='INCOME_SERVICE',
                amount=Decimal('12500.00'),
                date='2025-11-17',
                description='Facial treatment - Client John Doe',
                payment_method='CASH',
                auto_generated=False
            )

            print(f"✅ Created income transaction:")
            print(f"   ID: {income_transaction.id}")
            print(f"   Category: {income_transaction.category.full_path}")
            print(f"   Amount: ${income_transaction.amount}")
            print(f"   Signed Amount: ${income_transaction.signed_amount}")
            print(f"   Is Income: {income_transaction.is_income}")

        # Test 4: Summary
        print("\n" + "="*60)
        print("📊 TEST 4: Financial Summary")
        print("-" * 60)

        total_income = sum([
            t.amount for t in Transaction.objects.filter(
                branch=branch,
                type__startswith='INCOME_'
            )
        ])

        total_expense = sum([
            t.amount for t in Transaction.objects.filter(
                branch=branch,
                type='EXPENSE'
            )
        ])

        balance = total_income - total_expense

        print(f"💰 Total Income:  ${total_income:,.2f}")
        print(f"💸 Total Expense: ${total_expense:,.2f}")
        print(f"📊 Balance:       ${balance:,.2f}")

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")

        # Cleanup (optional - comment out to keep test data)
        print("🧹 Cleaning up test data...")
        Transaction.objects.filter(id__in=[transaction.id, income_transaction.id]).delete()
        print("✅ Cleanup complete\n")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_financial_system()

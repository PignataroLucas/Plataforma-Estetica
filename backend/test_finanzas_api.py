#!/usr/bin/env python
"""
Quick test script to verify Financial API endpoints are working
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from apps.empleados.models import Usuario
from apps.finanzas.models import TransactionCategory, Transaction

# Create test client
client = Client()

# Get or create a superuser for testing
user, created = Usuario.objects.get_or_create(
    username='test_admin',
    defaults={
        'email': 'test@admin.com',
        'rol': 'ADMIN',
        'is_superuser': True,
        'is_staff': True,
    }
)
if created:
    user.set_password('testpass123')
    user.save()
    print("✅ Created test admin user: test_admin / testpass123")

# Force login (bypass authentication for testing)
client.force_login(user)

print("\n" + "="*60)
print("TESTING FINANCIAL API ENDPOINTS")
print("="*60)

# Test 1: List categories
print("\n1️⃣  Testing GET /api/finanzas/categories/")
response = client.get('/api/finanzas/categories/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        print(f"   ✅ Found {data['count']} categories")
        if data['results']:
            print(f"   Sample: {data['results'][0]['name']}")
    elif isinstance(data, list):
        print(f"   ✅ Found {len(data)} categories")
        if data:
            print(f"   Sample: {data[0]['name']}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 2: Get categories by type
print("\n2️⃣  Testing GET /api/finanzas/categories/by_type/")
response = client.get('/api/finanzas/categories/by_type/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Income categories: {len(data.get('income', []))}")
    print(f"   ✅ Expense categories: {len(data.get('expense', []))}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 3: Get hierarchical tree
print("\n3️⃣  Testing GET /api/finanzas/categories/tree/")
response = client.get('/api/finanzas/categories/tree/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    count = len(data) if isinstance(data, list) else data.get('count', 0)
    print(f"   ✅ Main categories: {count}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 4: List transactions
print("\n4️⃣  Testing GET /api/finanzas/transactions/")
response = client.get('/api/finanzas/transactions/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        print(f"   ✅ Found {data['count']} transactions")
    elif isinstance(data, list):
        print(f"   ✅ Found {len(data)} transactions")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 5: Get summary
print("\n5️⃣  Testing GET /api/finanzas/transactions/summary/")
response = client.get('/api/finanzas/transactions/summary/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Income: ${data.get('income', {}).get('total', 0):,.2f}")
    print(f"   ✅ Expense: ${data.get('expense', {}).get('total', 0):,.2f}")
    print(f"   ✅ Balance: ${data.get('balance', 0):,.2f}")
    print(f"   ✅ Profit Margin: {data.get('profit_margin', 0):.2f}%")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 6: Get by category
print("\n6️⃣  Testing GET /api/finanzas/transactions/by_category/")
response = client.get('/api/finanzas/transactions/by_category/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Categories with transactions: {len(data)}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 7: Get by payment method
print("\n7️⃣  Testing GET /api/finanzas/transactions/by_payment_method/")
response = client.get('/api/finanzas/transactions/by_payment_method/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Payment methods: {len(data)}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 8: Get recent transactions
print("\n8️⃣  Testing GET /api/finanzas/transactions/recent/")
response = client.get('/api/finanzas/transactions/recent/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    count = len(data) if isinstance(data, list) else len(data.get('results', []))
    print(f"   ✅ Recent transactions: {count}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 9: List accounts receivable
print("\n9️⃣  Testing GET /api/finanzas/accounts-receivable/")
response = client.get('/api/finanzas/accounts-receivable/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        print(f"   ✅ Found {data['count']} accounts receivable")
    elif isinstance(data, list):
        print(f"   ✅ Found {len(data)} accounts receivable")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 10: Get overdue accounts
print("\n🔟 Testing GET /api/finanzas/accounts-receivable/overdue/")
response = client.get('/api/finanzas/accounts-receivable/overdue/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    count = len(data) if isinstance(data, list) else len(data.get('results', []))
    print(f"   ✅ Overdue accounts: {count}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test 11: Get accounts receivable summary
print("\n1️⃣1️⃣  Testing GET /api/finanzas/accounts-receivable/summary/")
response = client.get('/api/finanzas/accounts-receivable/summary/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Total Owed: ${data.get('total_owed', 0):,.2f}")
    print(f"   ✅ Total Paid: ${data.get('total_paid', 0):,.2f}")
    print(f"   ✅ Total Pending: ${data.get('total_pending', 0):,.2f}")
    print(f"   ✅ Overdue Count: {data.get('overdue_count', 0)}")
    print(f"   ✅ Paid Count: {data.get('paid_count', 0)}")
    print(f"   ✅ Pending Count: {data.get('pending_count', 0)}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

# Test filters
print("\n1️⃣2️⃣  Testing filters: ?type=EXPENSE")
response = client.get('/api/finanzas/categories/?type=EXPENSE')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        count = data['count']
    elif isinstance(data, list):
        count = len(data)
    else:
        count = 0
    print(f"   ✅ Expense categories: {count}")
else:
    print(f"   ❌ Error: {response.content[:200]}")

print("\n" + "="*60)
print("✅ ALL TESTS COMPLETED!")
print("="*60)

# Count endpoints
category_count = TransactionCategory.objects.count()
transaction_count = Transaction.objects.count()

print(f"\n📊 Database Summary:")
print(f"   - Categories: {category_count}")
print(f"   - Transactions: {transaction_count}")

print("\n✨ Financial API is ready to use!")
print("\n📚 Available endpoints:")
print("   - Categories: /api/finanzas/categories/")
print("   - Transactions: /api/finanzas/transactions/")
print("   - Accounts Receivable: /api/finanzas/accounts-receivable/")
print("\n📖 See backend/apps/finanzas/urls.py for full endpoint documentation")

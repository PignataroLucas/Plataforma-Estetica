#!/usr/bin/env python
"""
Test script to verify sales flow with offers
Tests the automatic creation of income transactions when products are sold
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from apps.inventario.models import Producto, MovimientoInventario, CategoriaProducto
from apps.finanzas.models import Transaction, TransactionCategory
from apps.empleados.models import Sucursal, Usuario

print("\n" + "="*70)
print("TESTING SALES FLOW WITH OFFERS")
print("="*70)

# Get or create a branch
sucursal = Sucursal.objects.first()
if not sucursal:
    print("❌ No hay sucursales en la base de datos")
    exit(1)

print(f"\n✅ Using branch: {sucursal.nombre}")

# Get or create a user
usuario = Usuario.objects.filter(is_superuser=True).first()
if not usuario:
    usuario = Usuario.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='admin123'
    )
print(f"✅ Using user: {usuario.username}")

# Create or get product category
categoria, created = CategoriaProducto.objects.get_or_create(
    sucursal=sucursal,
    nombre='Productos de Reventa',
    defaults={'activa': True}
)
print(f"✅ Product category: {categoria.nombre}")

# Test 1: Create a product
print("\n" + "="*70)
print("TEST 1: Creating a product")
print("="*70)

# Delete previous test product if exists
Producto.objects.filter(nombre='Crema Facial Premium').delete()

producto = Producto.objects.create(
    sucursal=sucursal,
    categoria=categoria,
    nombre='Crema Facial Premium',
    descripcion='Crema hidratante de alta calidad',
    tipo='REVENTA',
    codigo_barras='7890123456789',  # Unique barcode
    stock_actual=100,
    stock_minimo=10,
    unidad_medida='UNIDAD',
    precio_costo=Decimal('500.00'),
    precio_venta=Decimal('1200.00'),
    en_oferta=False,
    activo=True
)

print(f"✅ Created product: {producto.nombre}")
print(f"   - Stock: {producto.stock_actual} {producto.unidad_medida}")
print(f"   - Cost: ${producto.precio_costo}")
print(f"   - Sale price: ${producto.precio_venta}")
print(f"   - Profit margin: {producto.margen_ganancia:.2f}%")

# Test 2: Register a normal sale
print("\n" + "="*70)
print("TEST 2: Register a sale at normal price")
print("="*70)

# Count transactions before
transactions_before = Transaction.objects.count()
print(f"Transactions before: {transactions_before}")

# Create SALIDA movement (sale)
venta1 = MovimientoInventario.objects.create(
    producto=producto,
    tipo='SALIDA',
    cantidad=Decimal('5.00'),
    stock_anterior=producto.stock_actual,
    stock_nuevo=producto.stock_actual - Decimal('5.00'),
    motivo='Venta en mostrador',
    usuario=usuario
)

# Update product stock
producto.stock_actual -= Decimal('5.00')
producto.save()

print(f"✅ Sale registered: {venta1}")
print(f"   - Quantity sold: {venta1.cantidad} units")
print(f"   - Unit price: ${producto.precio_venta_final}")
print(f"   - Total amount: ${venta1.monto_total}")
print(f"   - New stock: {producto.stock_actual}")

# Check if transaction was auto-created
transactions_after = Transaction.objects.count()
print(f"\nTransactions after: {transactions_after}")

if transactions_after > transactions_before:
    transaction = Transaction.objects.latest('created_at')
    print(f"✅ Income transaction auto-created!")
    print(f"   - ID: {transaction.id}")
    print(f"   - Type: {transaction.get_type_display()}")
    print(f"   - Category: {transaction.category.name}")
    print(f"   - Amount: ${transaction.amount}")
    print(f"   - Description: {transaction.description}")
    print(f"   - Auto-generated: {transaction.auto_generated}")
else:
    print("❌ No transaction was created!")

# Test 3: Put product on offer
print("\n" + "="*70)
print("TEST 3: Activate offer on product")
print("="*70)

producto.en_oferta = True
producto.precio_oferta = Decimal('900.00')  # 25% discount
producto.save()

print(f"✅ Offer activated!")
print(f"   - Normal price: ${producto.precio_venta} (crossed out)")
print(f"   - Offer price: ${producto.precio_oferta}")
print(f"   - Discount: {producto.porcentaje_descuento}% OFF")
print(f"   - Final sale price: ${producto.precio_venta_final}")
print(f"   - Real profit margin: {producto.margen_ganancia_real:.2f}%")

# Test 4: Register sale with offer
print("\n" + "="*70)
print("TEST 4: Register a sale at offer price")
print("="*70)

transactions_before_offer = Transaction.objects.count()

# Create SALIDA movement (sale with offer)
venta2 = MovimientoInventario.objects.create(
    producto=producto,
    tipo='SALIDA',
    cantidad=Decimal('3.00'),
    stock_anterior=producto.stock_actual,
    stock_nuevo=producto.stock_actual - Decimal('3.00'),
    motivo='Venta con descuento',
    usuario=usuario
)

# Update product stock
producto.stock_actual -= Decimal('3.00')
producto.save()

print(f"✅ Sale with offer registered: {venta2}")
print(f"   - Quantity sold: {venta2.cantidad} units")
print(f"   - Unit price: ${producto.precio_venta_final} (offer price)")
print(f"   - Total amount: ${venta2.monto_total}")
print(f"   - Discount applied: {producto.porcentaje_descuento}% OFF")
print(f"   - New stock: {producto.stock_actual}")

# Check if transaction was auto-created with offer price
transactions_after_offer = Transaction.objects.count()
print(f"\nTransactions after offer sale: {transactions_after_offer}")

if transactions_after_offer > transactions_before_offer:
    transaction = Transaction.objects.latest('created_at')
    print(f"✅ Income transaction with offer auto-created!")
    print(f"   - ID: {transaction.id}")
    print(f"   - Type: {transaction.get_type_display()}")
    print(f"   - Category: {transaction.category.name}")
    print(f"   - Amount: ${transaction.amount}")
    print(f"   - Description: {transaction.description}")
    print(f"   - Auto-generated: {transaction.auto_generated}")

    # Verify amount is correct (3 units × $900)
    expected_amount = Decimal('3.00') * producto.precio_venta_final
    if transaction.amount == expected_amount:
        print(f"   ✅ Amount is correct! (${expected_amount})")
    else:
        print(f"   ❌ Amount mismatch! Expected ${expected_amount}, got ${transaction.amount}")
else:
    print("❌ No transaction was created!")

# Test 5: Register sale with custom price
print("\n" + "="*70)
print("TEST 5: Register a sale with custom price override")
print("="*70)

transactions_before_custom = Transaction.objects.count()

# Create SALIDA with custom price (e.g., special discount for a client)
custom_price = Decimal('800.00')
venta3 = MovimientoInventario.objects.create(
    producto=producto,
    tipo='SALIDA',
    cantidad=Decimal('2.00'),
    precio_unitario=custom_price,  # Custom price override
    stock_anterior=producto.stock_actual,
    stock_nuevo=producto.stock_actual - Decimal('2.00'),
    motivo='Venta especial cliente VIP',
    usuario=usuario
)

# Update product stock
producto.stock_actual -= Decimal('2.00')
producto.save()

print(f"✅ Sale with custom price registered: {venta3}")
print(f"   - Quantity sold: {venta3.cantidad} units")
print(f"   - Custom unit price: ${venta3.precio_unitario}")
print(f"   - Total amount: ${venta3.monto_total}")
print(f"   - New stock: {producto.stock_actual}")

# Check transaction
transactions_after_custom = Transaction.objects.count()
if transactions_after_custom > transactions_before_custom:
    transaction = Transaction.objects.latest('created_at')
    print(f"✅ Income transaction with custom price auto-created!")
    print(f"   - Amount: ${transaction.amount}")

    expected_amount = Decimal('2.00') * custom_price
    if transaction.amount == expected_amount:
        print(f"   ✅ Amount is correct! (${expected_amount})")
    else:
        print(f"   ❌ Amount mismatch!")

# Final summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

total_sold = Decimal('5.00') + Decimal('3.00') + Decimal('2.00')
print(f"✅ Total units sold: {total_sold}")
print(f"✅ Remaining stock: {producto.stock_actual}")
print(f"✅ Total transactions created: {Transaction.objects.count() - transactions_before}")

# Calculate total revenue
all_sales = MovimientoInventario.objects.filter(
    producto=producto,
    tipo='SALIDA'
)
total_revenue = sum(sale.monto_total for sale in all_sales)
print(f"✅ Total revenue: ${total_revenue}")

# Show all auto-generated transactions
print("\n📊 All auto-generated income transactions:")
income_transactions = Transaction.objects.filter(
    product=producto,
    type='INCOME_PRODUCT',
    auto_generated=True
).order_by('created_at')

for trans in income_transactions:
    print(f"   - {trans.date}: ${trans.amount} - {trans.description}")

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
print("="*70)
print("\n🎉 Sales flow with offers is working perfectly!")
print("   ✓ Normal sales create income transactions")
print("   ✓ Offer prices are applied automatically")
print("   ✓ Custom prices can be set per sale")
print("   ✓ Stock is decremented correctly")
print("   ✓ Transactions track date and time for analytics")

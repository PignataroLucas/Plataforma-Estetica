# Coding Conventions - Plataforma de Estética

**Last Updated:** November 17, 2025

---

## 🌍 Language Convention

### **CRITICAL RULE: Code in English, UI in Spanish**

This project follows a **bilingual approach**:

- ✅ **CODE** (variables, functions, classes, comments) → **ENGLISH**
- ✅ **UI/Frontend** (what users see: labels, messages, categories) → **SPANISH**

---

## 📝 Why This Approach?

1. **International Best Practice**: Code in English is the industry standard
2. **Team Collaboration**: Easier for developers worldwide to understand
3. **Libraries & Documentation**: Most resources are in English
4. **User Experience**: End users in Argentina/LATAM need Spanish interface
5. **Maintainability**: Clear separation between code and content

---

## ✅ Correct Examples

### Django Models

```python
# ✅ CORRECT: Code in English, verbose_name in Spanish

class Transaction(models.Model):
    """
    Record of all financial transactions (income and expenses).
    Integrates with inventory for automatic expense generation.
    """

    class TransactionType(models.TextChoices):
        INCOME_SERVICE = 'INCOME_SERVICE', 'Ingreso por Servicio'  # Spanish label
        EXPENSE = 'EXPENSE', 'Gasto'  # Spanish label

    # Field names in English
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto de la transacción"  # Spanish help text for admin
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices
    )

    class Meta:
        verbose_name = 'Transacción'  # Spanish for admin
        verbose_name_plural = 'Transacciones'  # Spanish for admin
```

### API Serializers

```python
# ✅ CORRECT: Code in English, error messages in Spanish

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""

    category_name = serializers.CharField(
        source='category.full_path',
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'date', 'category_name']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto debe ser mayor a cero"  # Spanish error message
            )
        return value
```

### Frontend (React/TypeScript)

```typescript
// ✅ CORRECT: Code in English, UI text in Spanish

interface Transaction {
  id: number;
  amount: number;
  date: string;
  categoryName: string;  // Variable name in English
}

function TransactionForm() {
  const [amount, setAmount] = useState<number>(0);

  return (
    <form>
      <label>
        Monto  {/* UI label in Spanish */}
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(Number(e.target.value))}
        />
      </label>

      <button type="submit">
        Guardar Transacción  {/* Button text in Spanish */}
      </button>
    </form>
  );
}
```

### Database Content

```python
# ✅ CORRECT: Category names stored in Spanish (displayed to users)

DEFAULT_CATEGORIES = {
    'EXPENSE': {
        'Alquileres': {  # Spanish name for UI
            'subcategories': ['Alquiler Local', 'Alquiler Máquina']
        },
        'Servicios': {
            'subcategories': ['Luz', 'Agua', 'Gas']
        }
    }
}
```

---

## ❌ Incorrect Examples

### Wrong: Spanish Code

```python
# ❌ WRONG: Code in Spanish

class Transaccion(models.Model):  # Wrong class name
    monto = models.DecimalField()  # Wrong field name
    metodo_pago = models.CharField()  # Wrong field name

    def calcular_total(self):  # Wrong method name
        return self.monto
```

### Wrong: English UI

```python
# ❌ WRONG: UI in English for Spanish-speaking users

class TransactionType(models.TextChoices):
    INCOME = 'INCOME', 'Income'  # Should be 'Ingreso'
    EXPENSE = 'EXPENSE', 'Expense'  # Should be 'Gasto'
```

---

## 📋 Checklist for New Code

When writing new code, ensure:

- [ ] Variable names are in English
- [ ] Function/method names are in English
- [ ] Class names are in English
- [ ] Code comments are in English
- [ ] Docstrings are in English
- [ ] `verbose_name` in models is in Spanish
- [ ] `help_text` in models is in Spanish
- [ ] Choice labels are in Spanish
- [ ] Error messages are in Spanish
- [ ] Database content (categories, etc.) is in Spanish
- [ ] Frontend UI text is in Spanish

---

## 🔧 Tools & Configuration

### Django Admin

Django admin will automatically show Spanish labels thanks to `verbose_name`:

```python
class Meta:
    verbose_name = 'Transacción'
    verbose_name_plural = 'Transacciones'
```

### API Responses

API should return Spanish labels for display:

```json
{
  "id": 1,
  "type": "EXPENSE",
  "type_display": "Gasto",  // Spanish for frontend
  "payment_method": "CASH",
  "payment_method_display": "Efectivo"  // Spanish for frontend
}
```

### Frontend i18n (Future)

If we need to support multiple languages later, we can use i18n:

```typescript
// Future multi-language support
const t = useTranslation();
<button>{t('save_transaction')}</button>
```

---

## 📚 Common Terms Translation

| English (Code)        | Spanish (UI)              |
|-----------------------|---------------------------|
| Transaction           | Transacción               |
| Income                | Ingreso                   |
| Expense               | Gasto                     |
| Category              | Categoría                 |
| Subcategory           | Subcategoría              |
| Amount                | Monto                     |
| Payment Method        | Método de Pago            |
| Cash                  | Efectivo                  |
| Transfer              | Transferencia             |
| Debit Card            | Tarjeta de Débito         |
| Credit Card           | Tarjeta de Crédito        |
| Date                  | Fecha                     |
| Description           | Descripción               |
| Notes                 | Notas                     |
| Receipt               | Comprobante               |
| Client                | Cliente                   |
| Service               | Servicio                  |
| Product               | Producto                  |
| Branch                | Sucursal                  |
| Account Receivable    | Cuenta por Cobrar         |
| Total Amount          | Monto Total               |
| Paid Amount           | Monto Pagado              |
| Pending Amount        | Monto Pendiente           |
| Due Date              | Fecha de Vencimiento      |
| Overdue               | Vencido                   |

---

## 🎯 Team Guidelines

### For Backend Developers

1. Write all code in English
2. Add Spanish `verbose_name` to all models
3. Add Spanish `help_text` to all fields
4. Use Spanish labels in choices
5. Return Spanish labels in API responses (use `get_FOO_display()`)

### For Frontend Developers

1. Write all code in English (variables, functions, components)
2. Use Spanish for ALL user-facing text
3. Labels, buttons, messages → Spanish
4. Validation errors → Spanish
5. Success messages → Spanish

### For QA/Testing

1. Verify all UI text is in Spanish
2. Verify code is in English
3. Check that error messages are clear and in Spanish
4. Ensure Spanish text is grammatically correct

---

## 📖 Examples by Feature

### Financial Categories

```python
# Code structure: English
class TransactionCategory(models.Model):
    name = models.CharField(max_length=100)
    parent_category = models.ForeignKey('self', ...)

# Category names in database: Spanish
categories = [
    'Alquileres',
    'Servicios',
    'Insumos y Productos'
]
```

### Auto-generated Descriptions

```python
# Code: English, description content: Spanish
description = f"Compra de {quantity} {unit} de {product_name}"
# NOT: f"Purchase of {quantity} {unit} of {product_name}"
```

### Validation Messages

```python
# Validation logic: English, message: Spanish
if amount <= 0:
    raise ValidationError("El monto debe ser mayor a cero")
# NOT: "Amount must be greater than zero"
```

---

## 🚀 Benefits of This Approach

1. ✅ **Code Quality**: English code is easier to maintain
2. ✅ **Team Scalability**: Can hire developers worldwide
3. ✅ **User Experience**: Spanish UI for target market
4. ✅ **Documentation**: Leverage English resources
5. ✅ **Future-Proof**: Easy to add i18n later if needed
6. ✅ **Best Practices**: Follows industry standards

---

## ⚠️ Common Mistakes to Avoid

1. ❌ Mixing Spanish and English in variable names
2. ❌ Using English in UI text visible to users
3. ❌ Using Spanish in code comments
4. ❌ Inconsistent naming conventions
5. ❌ Forgetting to translate error messages
6. ❌ Using English in database content meant for users

---

## ✅ Code Review Checklist

Before submitting code for review:

- [ ] All variables/functions/classes in English?
- [ ] All code comments in English?
- [ ] All docstrings in English?
- [ ] All UI text in Spanish?
- [ ] All error messages in Spanish?
- [ ] Database content for users in Spanish?
- [ ] Follows naming conventions?
- [ ] No Spanglish (mixed Spanish-English)?

---

**Remember**: Code is for developers (English), UI is for users (Spanish)!

This convention ensures professional code while providing excellent UX for our Spanish-speaking users. 🇦🇷🇪🇸

---

**Questions?** Check this document or ask the team lead.

**Last Updated:** November 17, 2025

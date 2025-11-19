import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useFinanzas } from '@/hooks/useFinanzas'
import {
  Transaction,
  TransactionCategory,
  TransactionType,
  PaymentMethod,
  CategoryType,
} from '@/types/models'
import { Button, Input, Select } from '@/components/ui'

interface TransactionFormData {
  type: TransactionType
  category: number
  amount: number
  date: string
  payment_method: PaymentMethod
  description: string
  notes: string
  receipt_number: string
}

interface TransactionFormProps {
  transaction?: Transaction | null
  onSubmit: (data: TransactionFormData) => Promise<void>
  onCancel: () => void
  loading?: boolean
  formId?: string
  showButtons?: boolean
}

/**
 * TransactionForm - Form for creating/editing transactions
 *
 * Features:
 * - Dynamic category loading based on type
 * - Validation with Spanish messages
 * - All payment methods supported
 * - Receipt number tracking
 */
export default function TransactionForm({
  transaction,
  onSubmit,
  onCancel,
  loading = false,
  formId = 'transaction-form',
  showButtons = true,
}: TransactionFormProps) {
  const { getCategoriesByType } = useFinanzas()
  const [categoriesByType, setCategoriesByType] = useState<{
    income: TransactionCategory[]
    expense: TransactionCategory[]
  }>({ income: [], expense: [] })
  const [loadingCategories, setLoadingCategories] = useState(true)

  // Form setup
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TransactionFormData>({
    defaultValues: {
      type: transaction?.type || TransactionType.EXPENSE,
      category: transaction?.category || 0,
      amount: transaction?.amount || 0,
      date: transaction?.date || new Date().toISOString().split('T')[0],
      payment_method: transaction?.payment_method || PaymentMethod.CASH,
      description: transaction?.description || '',
      notes: transaction?.notes || '',
      receipt_number: transaction?.receipt_number || '',
    },
  })

  // Watch type to filter categories
  const selectedType = watch('type')

  /**
   * Load categories grouped by type
   */
  useEffect(() => {
    const loadCategories = async () => {
      setLoadingCategories(true)
      try {
        const data = await getCategoriesByType()
        setCategoriesByType(data)
      } catch (error) {
        console.error('Error loading categories:', error)
      } finally {
        setLoadingCategories(false)
      }
    }
    loadCategories()
  }, [getCategoriesByType])

  /**
   * Get categories for current type
   */
  const getFilteredCategories = (): TransactionCategory[] => {
    const isIncome = selectedType === TransactionType.INCOME_SERVICE ||
                     selectedType === TransactionType.INCOME_PRODUCT ||
                     selectedType === TransactionType.INCOME_OTHER

    return isIncome ? categoriesByType.income : categoriesByType.expense
  }

  /**
   * Check if type is income
   */
  const isIncomeType = (type: TransactionType): boolean => {
    return type === TransactionType.INCOME_SERVICE ||
           type === TransactionType.INCOME_PRODUCT ||
           type === TransactionType.INCOME_OTHER
  }

  /**
   * Handle type change - reset category when type changes
   */
  const handleTypeChange = (newType: TransactionType) => {
    setValue('type', newType)
    setValue('category', 0) // Reset category
  }

  /**
   * Handle form submission
   */
  const onFormSubmit = handleSubmit(async (data) => {
    await onSubmit(data)
  })

  return (
    <form id={formId} onSubmit={onFormSubmit} className="space-y-6">
      {/* Transaction Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tipo de Transacción *
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => handleTypeChange(TransactionType.INCOME_OTHER)}
            className={`p-4 rounded-lg border-2 transition-all ${
              isIncomeType(selectedType)
                ? 'border-green-500 bg-green-50 text-green-700'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
              <span className="font-medium">Ingreso</span>
            </div>
          </button>
          <button
            type="button"
            onClick={() => handleTypeChange(TransactionType.EXPENSE)}
            className={`p-4 rounded-lg border-2 transition-all ${
              !isIncomeType(selectedType)
                ? 'border-red-500 bg-red-50 text-red-700'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
              </svg>
              <span className="font-medium">Gasto</span>
            </div>
          </button>
        </div>
      </div>

      {/* Income Subtype (only for income) */}
      {isIncomeType(selectedType) && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tipo de Ingreso *
          </label>
          <select
            {...register('type', { required: 'Este campo es requerido' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={TransactionType.INCOME_SERVICE}>Ingreso por Servicio</option>
            <option value={TransactionType.INCOME_PRODUCT}>Ingreso por Venta de Producto</option>
            <option value={TransactionType.INCOME_OTHER}>Otro Ingreso</option>
          </select>
        </div>
      )}

      {/* Category */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Categoría *
        </label>
        {loadingCategories ? (
          <div className="text-sm text-gray-500">Cargando categorías...</div>
        ) : (
          <select
            {...register('category', {
              required: 'Selecciona una categoría',
              validate: (value) => value > 0 || 'Selecciona una categoría',
            })}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.category ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value={0}>Seleccionar categoría...</option>
            {getFilteredCategories().map((cat) => (
              <optgroup key={cat.id} label={cat.name}>
                <option value={cat.id}>{cat.name}</option>
                {cat.subcategories?.map((subcat) => (
                  <option key={subcat.id} value={subcat.id}>
                    └ {subcat.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        )}
        {errors.category && (
          <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
        )}
      </div>

      {/* Amount and Date Row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Monto *
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
              $
            </span>
            <input
              type="number"
              step="0.01"
              min="0"
              {...register('amount', {
                required: 'El monto es requerido',
                min: { value: 0.01, message: 'El monto debe ser mayor a 0' },
              })}
              className={`w-full pl-8 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.amount ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="0.00"
            />
          </div>
          {errors.amount && (
            <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
          )}
        </div>

        {/* Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Fecha *
          </label>
          <input
            type="date"
            {...register('date', { required: 'La fecha es requerida' })}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.date ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.date && (
            <p className="mt-1 text-sm text-red-600">{errors.date.message}</p>
          )}
        </div>
      </div>

      {/* Payment Method */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Método de Pago *
        </label>
        <select
          {...register('payment_method', { required: 'Selecciona un método de pago' })}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.payment_method ? 'border-red-500' : 'border-gray-300'
          }`}
        >
          <option value={PaymentMethod.CASH}>Efectivo</option>
          <option value={PaymentMethod.BANK_TRANSFER}>Transferencia Bancaria</option>
          <option value={PaymentMethod.DEBIT_CARD}>Tarjeta de Débito</option>
          <option value={PaymentMethod.CREDIT_CARD}>Tarjeta de Crédito</option>
          <option value={PaymentMethod.MERCADOPAGO}>MercadoPago</option>
          <option value={PaymentMethod.OTHER}>Otro</option>
        </select>
        {errors.payment_method && (
          <p className="mt-1 text-sm text-red-600">{errors.payment_method.message}</p>
        )}
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Descripción *
        </label>
        <input
          type="text"
          {...register('description', {
            required: 'La descripción es requerida',
            minLength: { value: 3, message: 'Mínimo 3 caracteres' },
          })}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.description ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Ej: Pago de alquiler mensual"
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
        )}
      </div>

      {/* Receipt Number */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Número de Comprobante
        </label>
        <input
          type="text"
          {...register('receipt_number')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Ej: FC-001234"
        />
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Notas
        </label>
        <textarea
          {...register('notes')}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Notas adicionales..."
        />
      </div>

      {/* Buttons */}
      {showButtons && (
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button type="button" variant="secondary" onClick={onCancel} disabled={loading}>
            Cancelar
          </Button>
          <Button type="submit" variant="primary" loading={loading}>
            {transaction ? 'Actualizar' : 'Crear'} Transacción
          </Button>
        </div>
      )}
    </form>
  )
}

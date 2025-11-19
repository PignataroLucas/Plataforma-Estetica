import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useFinanzas } from '@/hooks/useFinanzas'
import { TransactionCategory, CategoryType } from '@/types/models'
import { Button } from '@/components/ui'

interface CategoryFormData {
  name: string
  type: CategoryType
  parent_category: number | null
  color: string
  order: number
}

interface CategoryFormProps {
  category?: TransactionCategory | null
  onSubmit: (data: CategoryFormData) => Promise<void>
  onCancel: () => void
  loading?: boolean
  formId?: string
  showButtons?: boolean
}

/**
 * CategoryForm - Form for creating/editing transaction categories
 *
 * Features:
 * - Type selection (Income/Expense)
 * - Parent category selection for subcategories
 * - Color picker
 * - Order/priority setting
 */
export default function CategoryForm({
  category,
  onSubmit,
  onCancel,
  loading = false,
  formId = 'category-form',
  showButtons = true,
}: CategoryFormProps) {
  const { fetchCategories } = useFinanzas()
  const [parentCategories, setParentCategories] = useState<TransactionCategory[]>([])
  const [loadingCategories, setLoadingCategories] = useState(false)

  // Form setup
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CategoryFormData>({
    defaultValues: {
      name: category?.name || '',
      type: category?.type || CategoryType.EXPENSE,
      parent_category: category?.parent_category || null,
      color: category?.color || '#3B82F6',
      order: category?.order || 0,
    },
  })

  // Watch type to filter parent categories
  const selectedType = watch('type')

  /**
   * Load parent categories based on selected type
   */
  useEffect(() => {
    const loadParentCategories = async () => {
      setLoadingCategories(true)
      try {
        const categories = await fetchCategories({ type: selectedType })
        // Filter to only show main categories (no parent)
        const mainCategories = categories.filter(
          (cat: TransactionCategory) => !cat.parent_category && cat.id !== category?.id
        )
        setParentCategories(mainCategories)
      } catch (error) {
        console.error('Error loading categories:', error)
      } finally {
        setLoadingCategories(false)
      }
    }
    loadParentCategories()
  }, [selectedType, fetchCategories, category?.id])

  /**
   * Handle type change - reset parent when type changes
   */
  const handleTypeChange = (newType: CategoryType) => {
    setValue('type', newType)
    setValue('parent_category', null)
  }

  /**
   * Handle form submission
   */
  const onFormSubmit = handleSubmit(async (data) => {
    // Convert empty parent_category to null
    const cleanedData = {
      ...data,
      parent_category: data.parent_category || null,
    }
    await onSubmit(cleanedData)
  })

  // Predefined colors for quick selection
  const colorOptions = [
    '#3B82F6', // Blue
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#EF4444', // Red
    '#8B5CF6', // Purple
    '#EC4899', // Pink
    '#06B6D4', // Cyan
    '#F97316', // Orange
    '#6366F1', // Indigo
    '#84CC16', // Lime
  ]

  return (
    <form id={formId} onSubmit={onFormSubmit} className="space-y-6">
      {/* Category Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Nombre de la Categoría *
        </label>
        <input
          type="text"
          {...register('name', {
            required: 'El nombre es requerido',
            minLength: { value: 2, message: 'Mínimo 2 caracteres' },
            maxLength: { value: 100, message: 'Máximo 100 caracteres' },
          })}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.name ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Ej: Alquiler, Sueldos, Servicios..."
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
        )}
      </div>

      {/* Category Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tipo *
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => handleTypeChange(CategoryType.INCOME)}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedType === CategoryType.INCOME
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
            onClick={() => handleTypeChange(CategoryType.EXPENSE)}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedType === CategoryType.EXPENSE
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

      {/* Parent Category (optional - for subcategories) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Categoría Padre (opcional)
        </label>
        {loadingCategories ? (
          <div className="text-sm text-gray-500">Cargando categorías...</div>
        ) : (
          <select
            {...register('parent_category')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Sin categoría padre (principal)</option>
            {parentCategories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        )}
        <p className="mt-1 text-xs text-gray-500">
          Selecciona una categoría padre para crear una subcategoría
        </p>
      </div>

      {/* Color */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Color
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {colorOptions.map((color) => (
            <button
              key={color}
              type="button"
              onClick={() => setValue('color', color)}
              className={`w-8 h-8 rounded-full border-2 transition-all ${
                watch('color') === color ? 'border-gray-800 scale-110' : 'border-transparent'
              }`}
              style={{ backgroundColor: color }}
              title={color}
            />
          ))}
        </div>
        <div className="flex items-center gap-2">
          <input
            type="color"
            {...register('color')}
            className="w-10 h-10 rounded cursor-pointer"
          />
          <input
            type="text"
            value={watch('color')}
            onChange={(e) => setValue('color', e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="#3B82F6"
          />
        </div>
      </div>

      {/* Order */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Orden de Prioridad
        </label>
        <input
          type="number"
          min="0"
          {...register('order', { valueAsNumber: true })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="0"
        />
        <p className="mt-1 text-xs text-gray-500">
          Las categorías con número menor aparecen primero
        </p>
      </div>

      {/* Buttons */}
      {showButtons && (
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button type="button" variant="secondary" onClick={onCancel} disabled={loading}>
            Cancelar
          </Button>
          <Button type="submit" variant="primary" loading={loading}>
            {category ? 'Actualizar' : 'Crear'} Categoría
          </Button>
        </div>
      )}
    </form>
  )
}

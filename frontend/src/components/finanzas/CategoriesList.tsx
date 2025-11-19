import { useState, useEffect } from 'react'
import { useFinanzas } from '@/hooks/useFinanzas'
import { TransactionCategory, CategoryType } from '@/types/models'
import { Button, Modal, ModalHeader, ModalBody, ModalFooter } from '@/components/ui'

interface CategoriesListProps {
  onEdit: (category: TransactionCategory) => void
  onRefresh?: () => void
}

/**
 * CategoriesList - Displays transaction categories in hierarchical view
 *
 * Features:
 * - Grouped by type (Income/Expense)
 * - Shows subcategories nested under parent
 * - Edit and delete actions
 * - Color indicators
 * - System category protection
 */
export default function CategoriesList({ onEdit, onRefresh }: CategoriesListProps) {
  const { fetchCategories, deleteCategory, loading: hookLoading } = useFinanzas()
  const [categories, setCategories] = useState<TransactionCategory[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [categoryToDelete, setCategoryToDelete] = useState<TransactionCategory | null>(null)
  const [activeTab, setActiveTab] = useState<'INCOME' | 'EXPENSE'>('EXPENSE')

  /**
   * Load categories on mount
   */
  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    setLoading(true)
    try {
      const data = await fetchCategories()
      setCategories(data)
    } catch (error) {
      console.error('Error loading categories:', error)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle delete confirmation
   */
  const handleDeleteClick = (category: TransactionCategory) => {
    setCategoryToDelete(category)
    setDeleteModalOpen(true)
  }

  /**
   * Perform delete
   */
  const handleConfirmDelete = async () => {
    if (!categoryToDelete) return

    const success = await deleteCategory(categoryToDelete.id)
    if (success) {
      setDeleteModalOpen(false)
      setCategoryToDelete(null)
      loadCategories()
      if (onRefresh) onRefresh()
    }
  }

  /**
   * Filter categories by type and get main categories
   */
  const getMainCategories = (type: CategoryType): TransactionCategory[] => {
    return categories.filter(
      (cat) => cat.type === type && !cat.parent_category
    )
  }

  /**
   * Get subcategories for a parent
   */
  const getSubcategories = (parentId: number): TransactionCategory[] => {
    return categories.filter((cat) => cat.parent_category === parentId)
  }

  /**
   * Render a single category row
   */
  const renderCategoryRow = (category: TransactionCategory, isSubcategory = false) => {
    const subcategories = getSubcategories(category.id)

    return (
      <div key={category.id}>
        <div
          className={`flex items-center justify-between p-4 ${
            isSubcategory ? 'pl-10 bg-gray-50' : 'bg-white'
          } border-b border-gray-100 hover:bg-gray-50 transition-colors`}
        >
          <div className="flex items-center gap-3">
            {/* Color indicator */}
            <div
              className="w-4 h-4 rounded-full flex-shrink-0"
              style={{ backgroundColor: category.color }}
            />

            {/* Category name */}
            <div>
              <span className={`font-medium ${isSubcategory ? 'text-gray-700' : 'text-gray-900'}`}>
                {isSubcategory && '└ '}
                {category.name}
              </span>
              {category.is_system_category && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                  Sistema
                </span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {subcategories.length > 0 && (
              <span className="text-xs text-gray-500 mr-2">
                {subcategories.length} subcategoría{subcategories.length !== 1 ? 's' : ''}
              </span>
            )}

            <Button
              variant="secondary"
              size="sm"
              onClick={() => onEdit(category)}
            >
              Editar
            </Button>

            {!category.is_system_category && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleDeleteClick(category)}
              >
                Eliminar
              </Button>
            )}
          </div>
        </div>

        {/* Render subcategories */}
        {subcategories.map((subcat) => renderCategoryRow(subcat, true))}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const incomeCategories = getMainCategories(CategoryType.INCOME)
  const expenseCategories = getMainCategories(CategoryType.EXPENSE)

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex space-x-1 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('EXPENSE')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'EXPENSE'
              ? 'border-red-500 text-red-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Gastos ({expenseCategories.length})
        </button>
        <button
          onClick={() => setActiveTab('INCOME')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'INCOME'
              ? 'border-green-500 text-green-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Ingresos ({incomeCategories.length})
        </button>
      </div>

      {/* Categories List */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {activeTab === 'EXPENSE' ? (
          expenseCategories.length > 0 ? (
            expenseCategories.map((cat) => renderCategoryRow(cat))
          ) : (
            <div className="p-8 text-center text-gray-500">
              No hay categorías de gastos
            </div>
          )
        ) : (
          incomeCategories.length > 0 ? (
            incomeCategories.map((cat) => renderCategoryRow(cat))
          ) : (
            <div className="p-8 text-center text-gray-500">
              No hay categorías de ingresos
            </div>
          )
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
      >
        <ModalHeader>Eliminar Categoría</ModalHeader>
        <ModalBody>
          {categoryToDelete && (
            <div>
              <p className="mb-3">
                ¿Estás seguro de que deseas eliminar la categoría{' '}
                <strong>{categoryToDelete.name}</strong>?
              </p>

              {getSubcategories(categoryToDelete.id).length > 0 && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800 mb-3">
                  <p className="font-semibold">⚠️ Advertencia:</p>
                  <p>
                    Esta categoría tiene {getSubcategories(categoryToDelete.id).length} subcategoría(s).
                    Se eliminarán también.
                  </p>
                </div>
              )}

              <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800">
                <p className="font-semibold">⚠️ Importante:</p>
                <p>
                  Si hay transacciones asociadas a esta categoría, no podrá ser eliminada.
                </p>
              </div>
            </div>
          )}
        </ModalBody>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setDeleteModalOpen(false)}
          >
            Cancelar
          </Button>
          <Button
            variant="danger"
            onClick={handleConfirmDelete}
            loading={hookLoading}
          >
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}

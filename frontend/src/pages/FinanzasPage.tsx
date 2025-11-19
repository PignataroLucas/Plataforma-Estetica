import { useState } from 'react'
import FinancialSummary from '@/components/finanzas/FinancialSummary'
import TransactionsList from '@/components/finanzas/TransactionsList'
import TransactionForm from '@/components/finanzas/TransactionForm'
import CategoriesList from '@/components/finanzas/CategoriesList'
import CategoryForm from '@/components/finanzas/CategoryForm'
import { useFinanzas } from '@/hooks/useFinanzas'
import { TransactionList, TransactionCategory } from '@/types/models'
import {
  Button,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from '@/components/ui'

/**
 * FinanzasPage - Main Financial Management Page
 *
 * Features:
 * - Financial dashboard with summary cards and charts
 * - Transactions list and management (coming soon)
 * - Categories management (coming soon)
 * - Accounts receivable (coming soon)
 */
export default function FinanzasPage() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'transactions' | 'categories' | 'receivables'>('dashboard')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [transactionToEdit, setTransactionToEdit] = useState<TransactionList | null>(null)

  // Category modal state
  const [isCategoryCreateModalOpen, setIsCategoryCreateModalOpen] = useState(false)
  const [categoryToEdit, setCategoryToEdit] = useState<TransactionCategory | null>(null)
  const [categoriesRefreshKey, setCategoriesRefreshKey] = useState(0)

  // Salary processing modal state
  const [isSalaryModalOpen, setIsSalaryModalOpen] = useState(false)
  const [salaryMonth, setSalaryMonth] = useState(new Date().getMonth() + 1)
  const [salaryYear, setSalaryYear] = useState(new Date().getFullYear())

  const { createTransaction, updateTransaction, fetchTransaction, createCategory, updateCategory, processSalaries, loading } = useFinanzas()

  /**
   * Handle create transaction
   */
  const handleCreateTransaction = async (data: any) => {
    await createTransaction(data)
    setIsCreateModalOpen(false)
  }

  /**
   * Handle edit transaction
   */
  const handleEditTransaction = async (data: any) => {
    if (transactionToEdit) {
      await updateTransaction(transactionToEdit.id, data)
      setTransactionToEdit(null)
    }
  }

  /**
   * Open edit modal
   */
  const handleOpenEditModal = async (transaction: TransactionList) => {
    // Fetch full transaction details
    const fullTransaction = await fetchTransaction(transaction.id)
    setTransactionToEdit(transaction)
  }

  /**
   * Handle create category
   */
  const handleCreateCategory = async (data: any) => {
    await createCategory(data)
    setIsCategoryCreateModalOpen(false)
    setCategoriesRefreshKey(prev => prev + 1)
  }

  /**
   * Handle edit category
   */
  const handleEditCategory = async (data: any) => {
    if (categoryToEdit) {
      await updateCategory(categoryToEdit.id, data)
      setCategoryToEdit(null)
      setCategoriesRefreshKey(prev => prev + 1)
    }
  }

  /**
   * Open category edit modal
   */
  const handleOpenCategoryEditModal = (category: TransactionCategory) => {
    setCategoryToEdit(category)
  }

  /**
   * Handle process salaries
   */
  const handleProcessSalaries = async () => {
    await processSalaries({
      month: salaryMonth,
      year: salaryYear
    })
    setIsSalaryModalOpen(false)
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Sistema Financiero
        </h1>
        <p className="text-gray-600">
          Control total de ingresos, gastos y finanzas de tu centro
        </p>
      </div>

      {/* Tabs Navigation */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'dashboard'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📊 Dashboard
          </button>
          <button
            onClick={() => setActiveTab('transactions')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'transactions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            💰 Transacciones
          </button>
          <button
            onClick={() => setActiveTab('categories')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'categories'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🏷️ Categorías
          </button>
          <button
            onClick={() => setActiveTab('receivables')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'receivables'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📋 Cuentas por Cobrar
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'dashboard' && <FinancialSummary />}

        {activeTab === 'transactions' && (
          <div className="space-y-6">
            {/* Action Buttons */}
            <div className="flex justify-end space-x-3">
              <Button
                variant="secondary"
                onClick={() => setIsSalaryModalOpen(true)}
                leftIcon={
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                }
              >
                Procesar Sueldos
              </Button>
              <Button
                variant="primary"
                onClick={() => setIsCreateModalOpen(true)}
                leftIcon={
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                }
              >
                Nueva Transacción
              </Button>
            </div>

            {/* Transactions List */}
            <TransactionsList
              onEdit={handleOpenEditModal}
              onView={(transaction) => {
                // TODO: Open view modal
                console.log('View transaction', transaction)
              }}
            />
          </div>
        )}

        {activeTab === 'categories' && (
          <div className="space-y-6">
            {/* Action Button */}
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={() => setIsCategoryCreateModalOpen(true)}
                leftIcon={
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                }
              >
                Nueva Categoría
              </Button>
            </div>

            {/* Categories List */}
            <CategoriesList
              key={categoriesRefreshKey}
              onEdit={handleOpenCategoryEditModal}
              onRefresh={() => setCategoriesRefreshKey(prev => prev + 1)}
            />
          </div>
        )}

        {activeTab === 'receivables' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Cuentas por Cobrar</h2>
            <p className="text-gray-600">Gestión de cuentas por cobrar (próximamente)</p>
          </div>
        )}
      </div>

      {/* Create Transaction Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        size="lg"
        showCloseButton={true}
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            Nueva Transacción
          </h2>
        </ModalHeader>
        <ModalBody>
          <TransactionForm
            onSubmit={handleCreateTransaction}
            onCancel={() => setIsCreateModalOpen(false)}
            loading={loading}
            formId="create-transaction-form"
            showButtons={false}
          />
        </ModalBody>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setIsCreateModalOpen(false)}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="create-transaction-form"
            variant="primary"
            loading={loading}
          >
            Crear Transacción
          </Button>
        </ModalFooter>
      </Modal>

      {/* Edit Transaction Modal */}
      <Modal
        isOpen={!!transactionToEdit}
        onClose={() => setTransactionToEdit(null)}
        size="lg"
        showCloseButton={true}
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            Editar Transacción
          </h2>
        </ModalHeader>
        <ModalBody>
          <TransactionForm
            onSubmit={handleEditTransaction}
            onCancel={() => setTransactionToEdit(null)}
            loading={loading}
            formId="edit-transaction-form"
            showButtons={false}
          />
        </ModalBody>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setTransactionToEdit(null)}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="edit-transaction-form"
            variant="primary"
            loading={loading}
          >
            Actualizar Transacción
          </Button>
        </ModalFooter>
      </Modal>

      {/* Create Category Modal */}
      <Modal
        isOpen={isCategoryCreateModalOpen}
        onClose={() => setIsCategoryCreateModalOpen(false)}
        size="lg"
        showCloseButton={true}
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            Nueva Categoría
          </h2>
        </ModalHeader>
        <ModalBody>
          <CategoryForm
            onSubmit={handleCreateCategory}
            onCancel={() => setIsCategoryCreateModalOpen(false)}
            loading={loading}
            formId="create-category-form"
            showButtons={false}
          />
        </ModalBody>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setIsCategoryCreateModalOpen(false)}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="create-category-form"
            variant="primary"
            loading={loading}
          >
            Crear Categoría
          </Button>
        </ModalFooter>
      </Modal>

      {/* Edit Category Modal */}
      <Modal
        isOpen={!!categoryToEdit}
        onClose={() => setCategoryToEdit(null)}
        size="lg"
        showCloseButton={true}
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            Editar Categoría
          </h2>
        </ModalHeader>
        <ModalBody>
          <CategoryForm
            category={categoryToEdit}
            onSubmit={handleEditCategory}
            onCancel={() => setCategoryToEdit(null)}
            loading={loading}
            formId="edit-category-form"
            showButtons={false}
          />
        </ModalBody>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setCategoryToEdit(null)}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="edit-category-form"
            variant="primary"
            loading={loading}
          >
            Actualizar Categoría
          </Button>
        </ModalFooter>
      </Modal>

      {/* Process Salaries Modal */}
      <Modal
        isOpen={isSalaryModalOpen}
        onClose={() => setIsSalaryModalOpen(false)}
        size="md"
        showCloseButton={true}
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            Procesar Sueldos Mensuales
          </h2>
        </ModalHeader>
        <ModalBody>
          <div className="space-y-4">
            <p className="text-gray-600 text-sm">
              Se crearán transacciones de gasto para todos los empleados activos que tengan un sueldo configurado.
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mes
                </label>
                <select
                  value={salaryMonth}
                  onChange={(e) => setSalaryMonth(Number(e.target.value))}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value={1}>Enero</option>
                  <option value={2}>Febrero</option>
                  <option value={3}>Marzo</option>
                  <option value={4}>Abril</option>
                  <option value={5}>Mayo</option>
                  <option value={6}>Junio</option>
                  <option value={7}>Julio</option>
                  <option value={8}>Agosto</option>
                  <option value={9}>Septiembre</option>
                  <option value={10}>Octubre</option>
                  <option value={11}>Noviembre</option>
                  <option value={12}>Diciembre</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Año
                </label>
                <select
                  value={salaryYear}
                  onChange={(e) => setSalaryYear(Number(e.target.value))}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value={2024}>2024</option>
                  <option value={2025}>2025</option>
                  <option value={2026}>2026</option>
                </select>
              </div>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setIsSalaryModalOpen(false)}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            variant="primary"
            onClick={handleProcessSalaries}
            loading={loading}
          >
            Procesar Sueldos
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}

import { useState } from 'react'
import FinancialSummary from '@/components/finanzas/FinancialSummary'
import TransactionsList from '@/components/finanzas/TransactionsList'
import TransactionForm from '@/components/finanzas/TransactionForm'
import { useFinanzas } from '@/hooks/useFinanzas'
import { TransactionList } from '@/types/models'
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

  const { createTransaction, updateTransaction, fetchTransaction, loading } = useFinanzas()

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
            {/* Action Button */}
            <div className="flex justify-end">
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
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Categorías</h2>
            <p className="text-gray-600">Gestión de categorías (próximamente)</p>
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
    </div>
  )
}

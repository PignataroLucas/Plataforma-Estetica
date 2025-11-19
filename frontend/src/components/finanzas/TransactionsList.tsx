import { useState, useEffect } from 'react'
import { useFinanzas } from '@/hooks/useFinanzas'
import {
  TransactionList,
  TransactionCategoryList,
  CategoryType,
  TransactionType,
  PaymentMethod,
} from '@/types/models'
import {
  Button,
  Input,
  Card,
  CardHeader,
  CardBody,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Badge,
  Spinner,
  Select,
} from '@/components/ui'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

interface TransactionsListProps {
  onEdit?: (transaction: TransactionList) => void
  onView?: (transaction: TransactionList) => void
}

/**
 * TransactionsList - Transaction management component
 *
 * Features:
 * - List all transactions with pagination
 * - Filter by date range, type, category
 * - Search functionality
 * - Quick actions (view, edit, delete)
 * - Color-coded income/expense
 */
export default function TransactionsList({ onEdit, onView }: TransactionsListProps) {
  const {
    transactions,
    categories,
    loading,
    fetchTransactions,
    fetchCategories,
    deleteTransaction,
  } = useFinanzas()

  // Filter state
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    type: '',
    category_id: '',
    search: '',
  })

  // Delete confirmation modal
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [transactionToDelete, setTransactionToDelete] = useState<TransactionList | null>(null)

  /**
   * Load initial data
   */
  useEffect(() => {
    fetchTransactions()
    fetchCategories()
  }, [fetchTransactions, fetchCategories])

  /**
   * Apply filters
   */
  const handleApplyFilters = async () => {
    const apiFilters: any = {}

    if (filters.date_from) apiFilters.date_from = filters.date_from
    if (filters.date_to) apiFilters.date_to = filters.date_to
    if (filters.type === 'income') apiFilters.is_income = true
    if (filters.type === 'expense') apiFilters.is_expense = true
    if (filters.category_id) apiFilters.category_id = parseInt(filters.category_id)

    await fetchTransactions(apiFilters)
  }

  /**
   * Clear filters
   */
  const handleClearFilters = () => {
    setFilters({
      date_from: '',
      date_to: '',
      type: '',
      category_id: '',
      search: '',
    })
    fetchTransactions()
  }

  /**
   * Handle delete confirmation
   */
  const handleDeleteClick = (transaction: TransactionList) => {
    setTransactionToDelete(transaction)
    setDeleteModalOpen(true)
  }

  /**
   * Confirm delete
   */
  const handleConfirmDelete = async () => {
    if (transactionToDelete) {
      await deleteTransaction(transactionToDelete.id)
      setDeleteModalOpen(false)
      setTransactionToDelete(null)
    }
  }

  /**
   * Format currency
   */
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  /**
   * Format date
   */
  const formatDate = (dateStr: string) => {
    return format(new Date(dateStr), 'dd/MM/yyyy', { locale: es })
  }

  /**
   * Get transaction type badge
   */
  const getTypeBadge = (transaction: TransactionList) => {
    const isIncome = transaction.type === TransactionType.INCOME_SERVICE ||
                     transaction.type === TransactionType.INCOME_PRODUCT ||
                     transaction.type === TransactionType.INCOME_OTHER

    return (
      <Badge variant={isIncome ? 'success' : 'danger'}>
        {transaction.type_display}
      </Badge>
    )
  }

  /**
   * Filter transactions by search term
   */
  const filteredTransactions = transactions.filter(t => {
    if (!filters.search) return true
    const searchLower = filters.search.toLowerCase()
    return (
      t.description.toLowerCase().includes(searchLower) ||
      t.category_name.toLowerCase().includes(searchLower) ||
      (t.client_name && t.client_name.toLowerCase().includes(searchLower))
    )
  })

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardBody>
          <div className="space-y-4">
            {/* First row: Date filters and type */}
            <div className="flex flex-wrap gap-4 items-end">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Desde
                </label>
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Hasta
                </label>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo
                </label>
                <select
                  value={filters.type}
                  onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm min-w-[150px]"
                >
                  <option value="">Todos</option>
                  <option value="income">Ingresos</option>
                  <option value="expense">Gastos</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Categoría
                </label>
                <select
                  value={filters.category_id}
                  onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm min-w-[200px]"
                >
                  <option value="">Todas</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <Button variant="primary" onClick={handleApplyFilters}>
                Filtrar
              </Button>
              <Button variant="secondary" onClick={handleClearFilters}>
                Limpiar
              </Button>
            </div>

            {/* Second row: Search */}
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  placeholder="Buscar por descripción, categoría o cliente..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  fullWidth
                />
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Transactions Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">
              Transacciones ({filteredTransactions.length})
            </h3>
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Spinner size="lg" />
            </div>
          ) : filteredTransactions.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No hay transacciones para mostrar
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Categoría
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Descripción
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Método de Pago
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Monto
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredTransactions.map((transaction) => {
                    const isIncome = transaction.type === TransactionType.INCOME_SERVICE ||
                                     transaction.type === TransactionType.INCOME_PRODUCT ||
                                     transaction.type === TransactionType.INCOME_OTHER

                    return (
                      <tr key={transaction.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(transaction.date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getTypeBadge(transaction)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {transaction.category_name}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                          <div className="flex items-center gap-2">
                            <span>{transaction.description}</span>
                            {transaction.auto_generated && (
                              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                                Auto
                              </span>
                            )}
                          </div>
                          {transaction.client_name && (
                            <div className="text-xs text-gray-500">
                              Cliente: {transaction.client_name}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {transaction.payment_method_display}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold text-right ${
                          isIncome ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {isIncome ? '+' : '-'}{formatCurrency(transaction.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          <div className="flex justify-center gap-2">
                            {onView && (
                              <button
                                onClick={() => onView(transaction)}
                                className="text-blue-600 hover:text-blue-800"
                                title="Ver detalle"
                              >
                                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                              </button>
                            )}
                            {onEdit && !transaction.auto_generated && (
                              <button
                                onClick={() => onEdit(transaction)}
                                className="text-yellow-600 hover:text-yellow-800"
                                title="Editar"
                              >
                                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                              </button>
                            )}
                            {!transaction.auto_generated && (
                              <button
                                onClick={() => handleDeleteClick(transaction)}
                                className="text-red-600 hover:text-red-800"
                                title="Eliminar"
                              >
                                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        size="sm"
      >
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            Confirmar Eliminación
          </h2>
        </ModalHeader>
        <ModalBody>
          <p className="text-gray-700">
            ¿Estás seguro que deseas eliminar esta transacción?
          </p>
          {transactionToDelete && (
            <div className="mt-3 p-3 bg-gray-50 rounded-md">
              <p className="text-sm font-medium">{transactionToDelete.description}</p>
              <p className="text-sm text-gray-500">
                {formatDate(transactionToDelete.date)} - {formatCurrency(transactionToDelete.amount)}
              </p>
            </div>
          )}
          <p className="text-sm text-red-600 mt-3">
            Esta acción no se puede deshacer.
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setDeleteModalOpen(false)}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleConfirmDelete} loading={loading}>
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}

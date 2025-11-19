import { useState, useCallback } from 'react'
import api from '@/services/api'
import toast from 'react-hot-toast'
import {
  Transaction,
  TransactionList,
  TransactionCategory,
  TransactionCategoryList,
  AccountReceivable,
  FinancialSummary,
  TransactionByCategory,
  TransactionByPaymentMethod,
  AccountsReceivableSummary,
  PaginatedResponse,
} from '@/types/models'

/**
 * useFinanzas Hook - Custom Hook for financial system management
 * Applies SOLID principles:
 * - SRP: Only handles financial operations (transactions, categories, receivables)
 * - DIP: Components depend on this hook, not on axios directly
 * - OCP: Extensible for adding more operations
 */
export const useFinanzas = () => {
  // ==================== STATE ====================
  const [transactions, setTransactions] = useState<TransactionList[]>([])
  const [categories, setCategories] = useState<TransactionCategoryList[]>([])
  const [accountsReceivable, setAccountsReceivable] = useState<AccountReceivable[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ==================== TRANSACTIONS ====================

  /**
   * Fetch all transactions with optional filters
   */
  const fetchTransactions = useCallback(async (filters?: {
    date_from?: string
    date_to?: string
    type?: string
    category_id?: number
    is_income?: boolean
    is_expense?: boolean
  }) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<PaginatedResponse<TransactionList>>('/finanzas/transactions/', {
        params: filters
      })
      setTransactions(response.data.results)
      return response.data.results
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar transacciones'
      setError(errorMsg)
      toast.error(errorMsg)
      setTransactions([])
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Fetch a single transaction by ID
   */
  const fetchTransaction = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<Transaction>(`/finanzas/transactions/${id}/`)
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar transacción'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Create a new transaction
   */
  const createTransaction = useCallback(async (data: Partial<Transaction>) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post<Transaction>('/finanzas/transactions/', data)
      toast.success('Transacción creada exitosamente')
      // Refresh transactions list
      await fetchTransactions()
      return response.data
    } catch (err: any) {
      let errorMsg = 'Error al crear transacción'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        } else {
          // Field validation errors
          const firstError = Object.values(err.response.data)[0]
          if (Array.isArray(firstError)) {
            errorMsg = firstError[0] as string
          }
        }
      }
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchTransactions])

  /**
   * Update an existing transaction
   */
  const updateTransaction = useCallback(async (id: number, data: Partial<Transaction>) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.patch<Transaction>(`/finanzas/transactions/${id}/`, data)
      toast.success('Transacción actualizada exitosamente')
      // Refresh transactions list
      await fetchTransactions()
      return response.data
    } catch (err: any) {
      let errorMsg = 'Error al actualizar transacción'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        } else {
          const firstError = Object.values(err.response.data)[0]
          if (Array.isArray(firstError)) {
            errorMsg = firstError[0] as string
          }
        }
      }
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchTransactions])

  /**
   * Delete a transaction
   */
  const deleteTransaction = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      await api.delete(`/finanzas/transactions/${id}/`)
      setTransactions(prev => prev.filter(t => t.id !== id))
      toast.success('Transacción eliminada exitosamente')
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al eliminar transacción'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Get financial summary (income, expense, balance, profit margin)
   */
  const getFinancialSummary = useCallback(async (filters?: {
    date_from?: string
    date_to?: string
  }) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<FinancialSummary>('/finanzas/transactions/summary/', {
        params: filters
      })
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al obtener resumen financiero'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Get transactions breakdown by category
   */
  const getTransactionsByCategory = useCallback(async (filters?: {
    date_from?: string
    date_to?: string
  }) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<TransactionByCategory[]>('/finanzas/transactions/by_category/', {
        params: filters
      })
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al obtener transacciones por categoría'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Get transactions breakdown by payment method
   */
  const getTransactionsByPaymentMethod = useCallback(async (filters?: {
    date_from?: string
    date_to?: string
  }) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<TransactionByPaymentMethod[]>('/finanzas/transactions/by_payment_method/', {
        params: filters
      })
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al obtener transacciones por método de pago'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Get recent transactions (last 10)
   */
  const getRecentTransactions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<TransactionList[]>('/finanzas/transactions/recent/')
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al obtener transacciones recientes'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // ==================== CATEGORIES ====================

  /**
   * Fetch all categories with optional filters
   */
  const fetchCategories = useCallback(async (filters?: {
    type?: string
    is_active?: boolean
  }) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<PaginatedResponse<TransactionCategoryList>>('/finanzas/categories/', {
        params: filters
      })
      setCategories(response.data.results)
      return response.data.results
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar categorías'
      setError(errorMsg)
      toast.error(errorMsg)
      setCategories([])
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Fetch categories as hierarchical tree
   */
  const getCategoriesTree = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<TransactionCategory[]>('/finanzas/categories/tree/')
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar árbol de categorías'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Fetch categories grouped by type (income/expense)
   */
  const getCategoriesByType = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<{
        income: TransactionCategory[]
        expense: TransactionCategory[]
      }>('/finanzas/categories/by_type/')
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar categorías por tipo'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Create a new category
   */
  const createCategory = useCallback(async (data: Partial<TransactionCategory>) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post<TransactionCategory>('/finanzas/categories/', data)
      toast.success('Categoría creada exitosamente')
      // Refresh categories list
      await fetchCategories()
      return response.data
    } catch (err: any) {
      let errorMsg = 'Error al crear categoría'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        } else {
          const firstError = Object.values(err.response.data)[0]
          if (Array.isArray(firstError)) {
            errorMsg = firstError[0] as string
          }
        }
      }
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchCategories])

  /**
   * Update an existing category
   */
  const updateCategory = useCallback(async (id: number, data: Partial<TransactionCategory>) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.patch<TransactionCategory>(`/finanzas/categories/${id}/`, data)
      toast.success('Categoría actualizada exitosamente')
      // Refresh categories list
      await fetchCategories()
      return response.data
    } catch (err: any) {
      let errorMsg = 'Error al actualizar categoría'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        }
      }
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchCategories])

  /**
   * Delete a category
   */
  const deleteCategory = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      await api.delete(`/finanzas/categories/${id}/`)
      setCategories(prev => prev.filter(c => c.id !== id))
      toast.success('Categoría eliminada exitosamente')
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al eliminar categoría'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // ==================== ACCOUNTS RECEIVABLE ====================

  /**
   * Fetch all accounts receivable
   */
  const fetchAccountsReceivable = useCallback(async (filters?: {
    is_paid?: boolean
    is_overdue?: boolean
    client_id?: number
  }) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<PaginatedResponse<AccountReceivable>>('/finanzas/accounts-receivable/', {
        params: filters
      })
      setAccountsReceivable(response.data.results)
      return response.data.results
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al cargar cuentas por cobrar'
      setError(errorMsg)
      toast.error(errorMsg)
      setAccountsReceivable([])
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Get overdue accounts
   */
  const getOverdueAccounts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<AccountReceivable[]>('/finanzas/accounts-receivable/overdue/')
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al obtener cuentas vencidas'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Get accounts receivable summary
   */
  const getAccountsReceivableSummary = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<AccountsReceivableSummary>('/finanzas/accounts-receivable/summary/')
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al obtener resumen de cuentas por cobrar'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Create a new account receivable
   */
  const createAccountReceivable = useCallback(async (data: Partial<AccountReceivable>) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post<AccountReceivable>('/finanzas/accounts-receivable/', data)
      toast.success('Cuenta por cobrar creada exitosamente')
      // Refresh list
      await fetchAccountsReceivable()
      return response.data
    } catch (err: any) {
      let errorMsg = 'Error al crear cuenta por cobrar'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        }
      }
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchAccountsReceivable])

  /**
   * Update an existing account receivable
   */
  const updateAccountReceivable = useCallback(async (id: number, data: Partial<AccountReceivable>) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.patch<AccountReceivable>(`/finanzas/accounts-receivable/${id}/`, data)
      toast.success('Cuenta por cobrar actualizada exitosamente')
      // Refresh list
      await fetchAccountsReceivable()
      return response.data
    } catch (err: any) {
      let errorMsg = 'Error al actualizar cuenta por cobrar'
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data
        } else if (err.response.data.detail) {
          errorMsg = err.response.data.detail
        }
      }
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchAccountsReceivable])

  /**
   * Delete an account receivable
   */
  const deleteAccountReceivable = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      await api.delete(`/finanzas/accounts-receivable/${id}/`)
      setAccountsReceivable(prev => prev.filter(a => a.id !== id))
      toast.success('Cuenta por cobrar eliminada exitosamente')
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al eliminar cuenta por cobrar'
      setError(errorMsg)
      toast.error(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // ==================== RETURN ====================

  return {
    // State
    transactions,
    categories,
    accountsReceivable,
    loading,
    error,

    // Transaction operations
    fetchTransactions,
    fetchTransaction,
    createTransaction,
    updateTransaction,
    deleteTransaction,
    getFinancialSummary,
    getTransactionsByCategory,
    getTransactionsByPaymentMethod,
    getRecentTransactions,

    // Category operations
    fetchCategories,
    getCategoriesTree,
    getCategoriesByType,
    createCategory,
    updateCategory,
    deleteCategory,

    // Accounts Receivable operations
    fetchAccountsReceivable,
    getOverdueAccounts,
    getAccountsReceivableSummary,
    createAccountReceivable,
    updateAccountReceivable,
    deleteAccountReceivable,
  }
}

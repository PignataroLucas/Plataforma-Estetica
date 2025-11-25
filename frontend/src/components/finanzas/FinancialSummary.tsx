import { useState, useEffect } from 'react'
import { useFinanzas } from '@/hooks/useFinanzas'
import {
  FinancialSummary as FinancialSummaryType,
  TransactionByCategory,
  TransactionByPaymentMethod,
} from '@/types/models'
import { Card, CardHeader, CardBody, Spinner, DateInput } from '@/components/ui'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { format, subDays, startOfMonth, endOfMonth, startOfWeek, endOfWeek } from 'date-fns'
import { es } from 'date-fns/locale'

/**
 * FinancialSummary - Dashboard Component
 * Shows financial overview with cards and charts
 *
 * Features:
 * - Summary cards (income, expense, balance, profit margin)
 * - Period filters (today, week, month, custom)
 * - Charts: Income vs Expense, By Category, By Payment Method
 */
export default function FinancialSummary() {
  const {
    getFinancialSummary,
    getTransactionsByCategory,
    getTransactionsByPaymentMethod,
    loading,
  } = useFinanzas()

  // State
  const [summary, setSummary] = useState<FinancialSummaryType | null>(null)
  const [byCategory, setByCategory] = useState<TransactionByCategory[]>([])
  const [byPaymentMethod, setByPaymentMethod] = useState<TransactionByPaymentMethod[]>([])
  const [period, setPeriod] = useState<'today' | 'week' | 'month' | 'custom'>('month')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  /**
   * Calculate date range based on selected period
   */
  const getDateRange = () => {
    const today = new Date()

    switch (period) {
      case 'today':
        return {
          date_from: format(today, 'yyyy-MM-dd'),
          date_to: format(today, 'yyyy-MM-dd'),
        }
      case 'week':
        return {
          date_from: format(startOfWeek(today, { locale: es }), 'yyyy-MM-dd'),
          date_to: format(endOfWeek(today, { locale: es }), 'yyyy-MM-dd'),
        }
      case 'month':
        return {
          date_from: format(startOfMonth(today), 'yyyy-MM-dd'),
          date_to: format(endOfMonth(today), 'yyyy-MM-dd'),
        }
      case 'custom':
        return dateFrom && dateTo ? { date_from: dateFrom, date_to: dateTo } : {}
      default:
        return {}
    }
  }

  /**
   * Load financial data
   */
  const loadData = async () => {
    const filters = getDateRange()

    try {
      const [summaryData, categoryData, paymentMethodData] = await Promise.all([
        getFinancialSummary(filters),
        getTransactionsByCategory(filters),
        getTransactionsByPaymentMethod(filters),
      ])

      setSummary(summaryData)
      setByCategory(categoryData)
      setByPaymentMethod(paymentMethodData)
    } catch (error) {
      console.error('Error loading financial data:', error)
    }
  }

  /**
   * Reload data when period changes
   */
  useEffect(() => {
    loadData()
  }, [period, dateFrom, dateTo])

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
   * Prepare data for Income vs Expense chart
   */
  const getIncomeVsExpenseData = () => {
    if (!summary) return []
    return [
      {
        name: 'Ingresos',
        value: summary.income.total,
        color: '#10B981', // Green
      },
      {
        name: 'Gastos',
        value: summary.expense.total,
        color: '#EF4444', // Red
      },
    ]
  }

  /**
   * Prepare data for category pie chart
   */
  const getCategoryChartData = () => {
    return byCategory.map(item => ({
      name: item.category__name,
      value: item.total_amount,
      color: item.category__color,
    }))
  }

  /**
   * Prepare data for payment method pie chart
   */
  const getPaymentMethodChartData = () => {
    const colors = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#6B7280']
    return byPaymentMethod.map((item, index) => ({
      name: item.payment_method_display,
      value: item.total_amount,
      color: colors[index % colors.length],
    }))
  }

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Period Filters */}
      <Card>
        <CardBody>
          <div className="flex flex-wrap items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Período:</span>

            {/* Period buttons */}
            <div className="flex gap-2">
              <button
                onClick={() => setPeriod('today')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  period === 'today'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Hoy
              </button>
              <button
                onClick={() => setPeriod('week')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  period === 'week'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Esta Semana
              </button>
              <button
                onClick={() => setPeriod('month')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  period === 'month'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Este Mes
              </button>
              <button
                onClick={() => setPeriod('custom')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  period === 'custom'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Personalizado
              </button>
            </div>

            {/* Custom date range */}
            {period === 'custom' && (
              <div className="flex items-center gap-2">
                <div className="min-w-[160px]">
                  <DateInput
                    value={dateFrom}
                    onChange={(value) => setDateFrom(value)}
                  />
                </div>
                <span className="text-gray-500">-</span>
                <div className="min-w-[160px]">
                  <DateInput
                    value={dateTo}
                    onChange={(value) => setDateTo(value)}
                  />
                </div>
              </div>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Income Card */}
        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Ingresos</p>
                <p className="text-2xl font-bold text-green-600">
                  {summary ? formatCurrency(summary.income.total) : '$0'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {summary?.income.count || 0} transacciones
                </p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
                </svg>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Expense Card */}
        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Gastos</p>
                <p className="text-2xl font-bold text-red-600">
                  {summary ? formatCurrency(summary.expense.total) : '$0'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {summary?.expense.count || 0} transacciones
                </p>
              </div>
              <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
                </svg>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Balance Card */}
        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Balance</p>
                <p className={`text-2xl font-bold ${summary && summary.balance >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {summary ? formatCurrency(summary.balance) : '$0'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Ingresos - Gastos
                </p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Profit Margin Card */}
        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Margen de Ganancia</p>
                <p className="text-2xl font-bold text-purple-600">
                  {summary ? `${summary.profit_margin.toFixed(1)}%` : '0%'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Balance / Ingresos
                </p>
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
                <svg className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Income vs Expense Bar Chart */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Ingresos vs Gastos</h3>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getIncomeVsExpenseData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.375rem',
                  }}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {getIncomeVsExpenseData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* By Category Pie Chart */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Por Categoría</h3>
          </CardHeader>
          <CardBody>
            {getCategoryChartData().length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={getCategoryChartData()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name} (${((entry.value / summary!.income.total) * 100).toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {getCategoryChartData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '0.375rem',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                No hay datos para mostrar
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Payment Methods Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Payment Method Pie Chart */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Por Método de Pago</h3>
          </CardHeader>
          <CardBody>
            {getPaymentMethodChartData().length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={getPaymentMethodChartData()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => entry.name}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {getPaymentMethodChartData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '0.375rem',
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                No hay datos para mostrar
              </div>
            )}
          </CardBody>
        </Card>

        {/* Category Breakdown Table */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Detalle por Categoría</h3>
          </CardHeader>
          <CardBody>
            <div className="overflow-y-auto max-h-[300px]">
              {byCategory.length > 0 ? (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Categoría
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Monto
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cant.
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {byCategory.map((item, index) => (
                      <tr key={index}>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center">
                            <div
                              className="h-3 w-3 rounded-full mr-2"
                              style={{ backgroundColor: item.category__color }}
                            />
                            <span className="text-sm font-medium text-gray-900">
                              {item.category__name}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                          {formatCurrency(item.total_amount)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-500">
                          {item.transaction_count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="flex items-center justify-center h-[200px] text-gray-500">
                  No hay transacciones en este período
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

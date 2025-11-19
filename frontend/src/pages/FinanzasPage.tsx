import { useState } from 'react'
import FinancialSummary from '@/components/finanzas/FinancialSummary'

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
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Transacciones</h2>
            <p className="text-gray-600">Gestión de transacciones (próximamente)</p>
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
    </div>
  )
}

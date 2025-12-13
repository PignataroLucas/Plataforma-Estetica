import { useState } from 'react';
import { useAnalytics } from '../hooks/useAnalytics';
import KPICard from '../components/analytics/shared/KPICard';
import DateRangeFilter from '../components/analytics/shared/DateRangeFilter';
import RevenueChart from '../components/analytics/dashboard/RevenueChart';
import TopServicesChart from '../components/analytics/dashboard/TopServicesChart';
import TopProductsChart from '../components/analytics/dashboard/TopProductsChart';

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState({
    startDate: '',
    endDate: '',
  });

  const { summary, revenue, services, products, loading, error } =
    useAnalytics(dateRange);

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Analytics Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Análisis completo de tu negocio
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Filtros */}
          <div className="lg:col-span-1">
            <DateRangeFilter onChange={setDateRange} />
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* KPIs Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <KPICard
                title="Ingresos Totales"
                value={summary?.kpis?.total_revenue || 0}
                change={summary?.kpis?.revenue_change}
                format="currency"
                loading={loading}
                icon={<span>💰</span>}
              />
              <KPICard
                title="Citas Completadas"
                value={summary?.kpis?.total_appointments || 0}
                change={summary?.kpis?.appointments_change}
                format="number"
                loading={loading}
                icon={<span>📅</span>}
              />
              <KPICard
                title="Clientes Activos"
                value={summary?.kpis?.active_clients || 0}
                format="number"
                loading={loading}
                icon={<span>👥</span>}
              />
              <KPICard
                title="Ticket Promedio"
                value={summary?.kpis?.average_ticket || 0}
                change={summary?.kpis?.ticket_change}
                format="currency"
                loading={loading}
                icon={<span>🎫</span>}
              />
            </div>

            {/* Revenue Breakdown */}
            {summary?.kpis?.revenue_breakdown && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">
                  Desglose de Ingresos
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-1">Servicios</p>
                    <p className="text-2xl font-bold text-purple-600">
                      $
                      {summary.kpis.revenue_breakdown.services.toLocaleString(
                        'es-AR'
                      )}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-1">Productos</p>
                    <p className="text-2xl font-bold text-green-600">
                      $
                      {summary.kpis.revenue_breakdown.products.toLocaleString(
                        'es-AR'
                      )}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-1">Otros</p>
                    <p className="text-2xl font-bold text-blue-600">
                      $
                      {summary.kpis.revenue_breakdown.other.toLocaleString(
                        'es-AR'
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Revenue Chart */}
            <RevenueChart
              data={revenue?.evolution || []}
              loading={loading}
            />

            {/* Services and Products Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <TopServicesChart
                data={services?.top_services || []}
                loading={loading}
              />
              <TopProductsChart
                data={products?.top_products || []}
                loading={loading}
              />
            </div>

            {/* Additional Info */}
            {summary?.kpis && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">
                  Métricas Adicionales
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Nuevos Clientes</p>
                    <p className="text-xl font-bold text-gray-900">
                      {summary.kpis.new_clients}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Tasa de Retención</p>
                    <p className="text-xl font-bold text-gray-900">
                      {summary.kpis.retention_rate}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">
                      Tasa de Completitud
                    </p>
                    <p className="text-xl font-bold text-gray-900">
                      {summary.kpis.completion_rate}%
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

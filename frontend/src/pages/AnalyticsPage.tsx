import { useState } from 'react';
import { useAnalytics } from '../hooks/useAnalytics';
import KPICard from '../components/analytics/shared/KPICard';
import DateRangeFilter from '../components/analytics/shared/DateRangeFilter';
import RevenueChart from '../components/analytics/dashboard/RevenueChart';
import TopServicesChart from '../components/analytics/dashboard/TopServicesChart';
import TopProductsChart from '../components/analytics/dashboard/TopProductsChart';
import PaymentMethodChart from '../components/analytics/dashboard/PaymentMethodChart';
import RevenueComparisonChart from '../components/analytics/dashboard/RevenueComparisonChart';
import ServiceProfitabilityChart from '../components/analytics/dashboard/ServiceProfitabilityChart';
import OccupancyHeatmap from '../components/analytics/dashboard/OccupancyHeatmap';
import WeekdayOccupancyChart from '../components/analytics/dashboard/WeekdayOccupancyChart';
import ServicesEvolutionChart from '../components/analytics/dashboard/ServicesEvolutionChart';
import WorkloadDistributionChart from '../components/analytics/dashboard/WorkloadDistributionChart';
import TopClientsTable from '../components/analytics/dashboard/TopClientsTable';
import LTVDistributionChart from '../components/analytics/dashboard/LTVDistributionChart';
import SeasonalTrendsChart from '../components/analytics/dashboard/SeasonalTrendsChart';
import InventoryRotationChart from '../components/analytics/dashboard/InventoryRotationChart';

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState<{
    startDate: string;
    endDate: string;
    compare?: boolean;
  }>({
    startDate: '',
    endDate: '',
  });

  const { summary, revenue, services, products, employees, clients, ocupacion, seasonalTrends, loading, error } =
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
          <div className="flex flex-col gap-4">
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
            {/* Filtros */}
            <div>
              <DateRangeFilter onChange={setDateRange} />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Main Content */}
        <div className="space-y-6">
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

            {/* Payment Method Distribution */}
            <PaymentMethodChart
              data={revenue?.by_payment_method || []}
              loading={loading}
            />

            {/* Period Comparison */}
            <RevenueComparisonChart
              data={revenue?.comparison || null}
              loading={loading}
            />

            {/* Service Profitability Analysis */}
            <ServiceProfitabilityChart
              data={services?.profitability || []}
              loading={loading}
            />

            {/* Occupancy Heatmap */}
            <OccupancyHeatmap
              data={ocupacion?.heatmap || []}
              loading={loading}
            />

            {/* Weekday Occupancy */}
            <WeekdayOccupancyChart
              data={ocupacion?.by_weekday || []}
              loading={loading}
            />

            {/* Services Evolution */}
            <ServicesEvolutionChart
              data={services?.evolution || []}
              loading={loading}
            />

            {/* Workload Distribution */}
            <WorkloadDistributionChart
              data={employees?.workload_distribution || []}
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

            {/* Top Clients */}
            <TopClientsTable
              data={clients?.top_clients || []}
              loading={loading}
            />

            {/* LTV Distribution */}
            <LTVDistributionChart
              data={clients?.ltv_distribution || []}
              loading={loading}
            />

            {/* Seasonal Trends */}
            <SeasonalTrendsChart
              data={seasonalTrends}
              loading={loading}
            />

            {/* Inventory Rotation */}
            <InventoryRotationChart
              data={products?.inventory_rotation || null}
              loading={loading}
            />

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
  );
}

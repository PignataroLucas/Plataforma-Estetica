import { useClientAnalytics } from '../../../hooks/useAnalytics';
import ClientSummaryCard from './ClientSummaryCard';
import ClientSpendingChart from './ClientSpendingChart';
import ClientAlertsPanel from './ClientAlertsPanel';
import ClientProductsHistory from './ClientProductsHistory';
import ServicesTimeline from './ServicesTimeline';
import FavoriteServicesChart from './FavoriteServicesChart';
import MonthlyServicesChart from './MonthlyServicesChart';
import LoyaltyScoreGauge from './LoyaltyScoreGauge';
import ActivityHeatmap from './ActivityHeatmap';
import MonthlyActivityPattern from './MonthlyActivityPattern';
import ProductsVsServicesChart from './ProductsVsServicesChart';
import BehaviorMetrics from './BehaviorMetrics';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';

interface ClientAnalyticsTabProps {
  clienteId: number;
}

export default function ClientAnalyticsTab({
  clienteId,
}: ClientAnalyticsTabProps) {
  const { summary, spending, patterns, alerts, products, behavior, loading, error } =
    useClientAnalytics(clienteId);

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      </div>
    );
  }

  // Helper function to calculate percentage safely
  const calculatePercentage = (value: number, total: number): number => {
    if (total === 0) return 0;
    return (value / total) * 100;
  };

  // Preparar datos para gráfico de días preferidos
  const daysData =
    patterns?.preferred_days &&
    Object.entries(patterns.preferred_days).map(([day, count]) => ({
      name: day,
      value: count as number,
    }));

  // Preparar datos para gráfico de distribución de gasto
  const spendingDistributionData = spending?.spending_distribution && [
    {
      name: 'Servicios',
      value: spending.spending_distribution.services.amount,
    },
    {
      name: 'Productos',
      value: spending.spending_distribution.products.amount,
    },
  ];

  const COLORS = ['#8b5cf6', '#10b981'];

  // Calculate total time slots safely
  const totalTimeSlots = patterns?.preferred_time_slots
    ? patterns.preferred_time_slots.morning +
      patterns.preferred_time_slots.afternoon +
      patterns.preferred_time_slots.evening
    : 0;

  return (
    <div className="space-y-8 p-6">
      {/* ==================== SECCIÓN 1: RESUMEN Y FIDELIZACIÓN ==================== */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 border-b-2 border-blue-500 pb-2">
          📊 Resumen y Fidelización
        </h2>

        {/* Summary Card */}
        <ClientSummaryCard data={summary} loading={loading} />

        {/* Loyalty Score Gauge */}
        <LoyaltyScoreGauge data={behavior} loading={loading} />

        {/* Behavior Metrics */}
        {behavior?.behavior_metrics && (
          <BehaviorMetrics data={behavior.behavior_metrics} loading={loading} />
        )}

        {/* Activity Heatmap */}
        {behavior?.activity_heatmap && (
          <ActivityHeatmap data={behavior.activity_heatmap} loading={loading} />
        )}
      </div>

      {/* ==================== SECCIÓN 2: ALERTAS E INSIGHTS ==================== */}
      {alerts && (alerts.alerts?.length > 0 || alerts.insights?.length > 0) && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 border-b-2 border-amber-500 pb-2">
            🔔 Alertas e Insights
          </h2>
          <ClientAlertsPanel
            alerts={alerts.alerts || []}
            insights={alerts.insights || []}
            recommendations={alerts.recommendations || []}
            loading={loading}
          />
        </div>
      )}

      {/* ==================== SECCIÓN 3: ANÁLISIS DE GASTO ==================== */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 border-b-2 border-green-500 pb-2">
          💰 Análisis de Gasto
        </h2>

        {/* Spending Chart */}
        {spending && (
          <ClientSpendingChart
            data={spending.monthly_spending_12m || []}
            averageMonthly={spending.average_monthly || 0}
            loading={loading}
          />
        )}

        {/* Products vs Services Monthly */}
        {spending?.products_vs_services_monthly && (
          <ProductsVsServicesChart
            data={spending.products_vs_services_monthly}
            loading={loading}
          />
        )}
      </div>

      {/* ==================== SECCIÓN 4: PATRONES DE COMPORTAMIENTO ==================== */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 border-b-2 border-purple-500 pb-2">
          🔮 Patrones de Comportamiento
        </h2>

        {/* Grid con Distribución de Gasto y Horarios Preferidos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Spending Distribution */}
          {spendingDistributionData && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                Distribución de Gasto
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={spendingDistributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {spendingDistributionData.map((_entry: { name: string; value: number }, index: number) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => `$${value.toLocaleString('es-AR')}`}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Horarios Preferidos */}
          {patterns?.preferred_time_slots && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                Horarios Preferidos
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    ☀️ Mañana (9-13h)
                  </span>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                      <div
                        className="bg-yellow-500 h-2 rounded-full"
                        style={{
                          width: `${calculatePercentage(
                            patterns.preferred_time_slots.morning,
                            totalTimeSlots
                          )}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold text-gray-700">
                      {patterns.preferred_time_slots.morning}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    🌤️ Tarde (13-18h)
                  </span>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                      <div
                        className="bg-orange-500 h-2 rounded-full"
                        style={{
                          width: `${calculatePercentage(
                            patterns.preferred_time_slots.afternoon,
                            totalTimeSlots
                          )}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold text-gray-700">
                      {patterns.preferred_time_slots.afternoon}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    🌙 Noche (18-21h)
                  </span>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{
                          width: `${calculatePercentage(
                            patterns.preferred_time_slots.evening,
                            totalTimeSlots
                          )}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold text-gray-700">
                      {patterns.preferred_time_slots.evening}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Días de la Semana Preferidos */}
        {daysData && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              Días de la Semana Preferidos
            </h3>
            <div className="grid grid-cols-7 gap-2">
              {daysData.map((day: { name: string; value: number }) => (
                <div
                  key={day.name}
                  className="text-center p-3 bg-purple-50 rounded-lg"
                >
                  <p className="text-xs text-gray-600 mb-1">{day.name.slice(0, 3)}</p>
                  <p className="text-2xl font-bold text-purple-600">{day.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Servicios Favoritos */}
        {patterns?.favorite_services && (
          <FavoriteServicesChart
            data={patterns.favorite_services}
            loading={loading}
          />
        )}

        {/* Gráfico de Servicios por Mes */}
        {patterns?.monthly_services && (
          <MonthlyServicesChart
            data={patterns.monthly_services}
            loading={loading}
          />
        )}

        {/* Patrón de Actividad Anual */}
        {patterns?.monthly_activity_pattern && (
          <MonthlyActivityPattern
            data={patterns.monthly_activity_pattern}
            loading={loading}
          />
        )}
      </div>

      {/* ==================== SECCIÓN 5: HISTORIAL ==================== */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 border-b-2 border-indigo-500 pb-2">
          📜 Historial
        </h2>

        {/* Products History */}
        <ClientProductsHistory data={products} loading={loading} />

        {/* Services Timeline */}
        <ServicesTimeline clienteId={clienteId} />
      </div>
    </div>
  );
}

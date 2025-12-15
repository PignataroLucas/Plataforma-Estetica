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

  return (
    <div className="space-y-6 p-6">
      {/* Summary Card */}
      <ClientSummaryCard data={summary} loading={loading} />

      {/* Loyalty Score Gauge */}
      <LoyaltyScoreGauge data={behavior} loading={loading} />

      {/* Activity Heatmap */}
      {behavior?.activity_heatmap && (
        <ActivityHeatmap data={behavior.activity_heatmap} loading={loading} />
      )}

      {/* Alerts Panel */}
      {alerts && (
        <ClientAlertsPanel
          alerts={alerts.alerts || []}
          insights={alerts.insights || []}
          recommendations={alerts.recommendations || []}
          loading={loading}
        />
      )}

      {/* Spending Chart */}
      {spending && (
        <ClientSpendingChart
          data={spending.monthly_spending_12m || []}
          averageMonthly={spending.average_monthly || 0}
          loading={loading}
        />
      )}

      {/* Patterns and Distribution */}
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

        {/* Preferred Days */}
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
                        width: `${
                          (patterns.preferred_time_slots.morning /
                            (patterns.preferred_time_slots.morning +
                              patterns.preferred_time_slots.afternoon +
                              patterns.preferred_time_slots.evening)) *
                          100
                        }%`,
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
                        width: `${
                          (patterns.preferred_time_slots.afternoon /
                            (patterns.preferred_time_slots.morning +
                              patterns.preferred_time_slots.afternoon +
                              patterns.preferred_time_slots.evening)) *
                          100
                        }%`,
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
                        width: `${
                          (patterns.preferred_time_slots.evening /
                            (patterns.preferred_time_slots.morning +
                              patterns.preferred_time_slots.afternoon +
                              patterns.preferred_time_slots.evening)) *
                          100
                        }%`,
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

      {/* Preferred Days - Simple Table */}
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

      {/* Favorite Services */}
      {patterns?.favorite_services && (
        <FavoriteServicesChart
          data={patterns.favorite_services}
          loading={loading}
        />
      )}

      {/* Monthly Services Chart */}
      {patterns?.monthly_services && (
        <MonthlyServicesChart
          data={patterns.monthly_services}
          loading={loading}
        />
      )}

      {/* Products History */}
      <ClientProductsHistory data={products} loading={loading} />

      {/* Services Timeline */}
      <ServicesTimeline clienteId={clienteId} />
    </div>
  );
}

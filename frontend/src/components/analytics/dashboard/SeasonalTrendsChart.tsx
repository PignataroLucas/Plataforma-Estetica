import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface MonthlyTrend {
  month: number;
  month_name: string;
  appointments: number;
  revenue: number;
  avg_ticket: number;
}

interface QuarterlyTrend {
  quarter: string;
  appointments: number;
  revenue: number;
  avg_ticket: number;
}

interface SeasonalTrendsData {
  year: number;
  monthly_trends: MonthlyTrend[];
  quarterly_trends: QuarterlyTrend[];
  peak_month: string;
  peak_revenue: number;
  lowest_month: string;
  lowest_revenue: number;
  total_year_revenue: number;
  total_year_appointments: number;
}

interface SeasonalTrendsChartProps {
  data: SeasonalTrendsData | null;
  loading?: boolean;
}

export default function SeasonalTrendsChart({
  data,
  loading = false,
}: SeasonalTrendsChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-96 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || !data.monthly_trends || data.monthly_trends.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Tendencias Estacionales
        </h3>
        <div className="flex items-center justify-center h-96">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Tendencias Estacionales - {data.year}
        </h3>
      </div>

      {/* Estadísticas destacadas */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-600 mb-1">Ingresos Anuales</p>
          <p className="text-2xl font-bold text-gray-900">
            ${data.total_year_revenue.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-blue-700 mt-1">{data.total_year_appointments} citas</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <p className="text-sm text-green-600 mb-1">Mes Pico</p>
          <p className="text-lg font-bold text-gray-900">{data.peak_month}</p>
          <p className="text-sm text-green-700 mt-1">
            ${data.peak_revenue.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <p className="text-sm text-yellow-600 mb-1">Mes Bajo</p>
          <p className="text-lg font-bold text-gray-900">{data.lowest_month}</p>
          <p className="text-sm text-yellow-700 mt-1">
            ${data.lowest_revenue.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
          <p className="text-sm text-purple-600 mb-1">Ticket Promedio Anual</p>
          <p className="text-2xl font-bold text-gray-900">
            ${((data.total_year_revenue / data.total_year_appointments) || 0).toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
        </div>
      </div>

      {/* Gráfico de tendencia mensual */}
      <div className="mb-8">
        <h4 className="text-md font-semibold text-gray-700 mb-3">Evolución Mensual</h4>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.monthly_trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="month_name"
              angle={-45}
              textAnchor="end"
              height={80}
              interval={0}
              style={{ fontSize: '11px' }}
            />
            <YAxis
              yAxisId="left"
              label={{ value: 'Ingresos ($)', angle: -90, position: 'insideLeft' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: 'Citas', angle: 90, position: 'insideRight' }}
            />
            <Tooltip
              formatter={(value: number, name: string) => {
                if (name === 'Ingresos') {
                  return [`$${value.toLocaleString('es-AR')}`, name];
                }
                return [value, name];
              }}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="revenue"
              name="Ingresos"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="appointments"
              name="Citas"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Gráfico de tendencia trimestral */}
      <div className="mb-6">
        <h4 className="text-md font-semibold text-gray-700 mb-3">Resumen por Trimestre</h4>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data.quarterly_trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="quarter" />
            <YAxis
              yAxisId="left"
              label={{ value: 'Ingresos ($)', angle: -90, position: 'insideLeft' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: 'Citas', angle: 90, position: 'insideRight' }}
            />
            <Tooltip
              formatter={(value: number, name: string) => {
                if (name === 'Ingresos') {
                  return [`$${value.toLocaleString('es-AR')}`, name];
                }
                return [value, name];
              }}
            />
            <Legend />
            <Bar yAxisId="left" dataKey="revenue" name="Ingresos" fill="#3b82f6" />
            <Bar yAxisId="right" dataKey="appointments" name="Citas" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tabla detallada */}
      <div className="overflow-x-auto">
        <h4 className="text-md font-semibold text-gray-700 mb-3">Detalle Mensual</h4>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Mes
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Citas
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Ingresos
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Ticket Promedio
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                Tendencia
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.monthly_trends.map((month, index) => {
              const prevMonth = index > 0 ? data.monthly_trends[index - 1] : null;
              const trend = prevMonth
                ? month.revenue > prevMonth.revenue
                  ? 'up'
                  : month.revenue < prevMonth.revenue
                  ? 'down'
                  : 'stable'
                : 'stable';

              return (
                <tr
                  key={month.month}
                  className={`hover:bg-gray-50 ${
                    month.month_name === data.peak_month
                      ? 'bg-green-50'
                      : month.month_name === data.lowest_month
                      ? 'bg-yellow-50'
                      : ''
                  }`}
                >
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {month.month_name}
                    {month.month_name === data.peak_month && (
                      <span className="ml-2 text-xs text-green-600">🏆 Pico</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {month.appointments}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                    ${month.revenue.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-600">
                    ${month.avg_ticket.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {trend === 'up' && <span className="text-green-600">↗️</span>}
                    {trend === 'down' && <span className="text-red-600">↘️</span>}
                    {trend === 'stable' && <span className="text-gray-400">→</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Interpretación */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Interpretación:</span> Este análisis muestra las
          tendencias estacionales de tu negocio. El mes pico es <strong>{data.peak_month}</strong>{' '}
          con ${data.peak_revenue.toLocaleString('es-AR', { maximumFractionDigits: 0 })} en ingresos, mientras que{' '}
          <strong>{data.lowest_month}</strong> es el mes más bajo. Usa esta información para
          planificar campañas de marketing en meses bajos y preparar inventario/personal para meses
          pico.
        </p>
      </div>
    </div>
  );
}

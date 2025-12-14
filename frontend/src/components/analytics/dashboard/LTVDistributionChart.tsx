import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface LTVRange {
  range: string;
  count: number;
  min_value: number;
  max_value: number;
}

interface LTVDistributionChartProps {
  data: LTVRange[] | null;
  loading?: boolean;
}

export default function LTVDistributionChart({
  data,
  loading = false,
}: LTVDistributionChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-80 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Distribución de Lifetime Value (LTV)
        </h3>
        <div className="flex items-center justify-center h-80">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Colores graduales por rango (de claro a oscuro)
  const colors = ['#dbeafe', '#93c5fd', '#60a5fa', '#3b82f6', '#1d4ed8'];

  // Calcular totales
  const totalClients = data.reduce((sum, item) => sum + item.count, 0);
  const maxRange = data.reduce((max, item) =>
    item.count > max.count ? item : max, data[0]
  );

  // Preparar datos para el gráfico
  const chartData = data.map((item, index) => ({
    ...item,
    percentage: ((item.count / totalClients) * 100).toFixed(1),
    color: colors[index % colors.length],
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Distribución de Lifetime Value (LTV)
      </h3>

      {/* Estadísticas destacadas */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-600 mb-1">Total Clientes</p>
          <p className="text-2xl font-bold text-gray-900">{totalClients}</p>
        </div>
        <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
          <p className="text-sm text-indigo-600 mb-1">Rango Más Común</p>
          <p className="text-lg font-bold text-gray-900">{maxRange.range}</p>
          <p className="text-xs text-indigo-700 mt-1">
            {maxRange.count} clientes
          </p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
          <p className="text-sm text-purple-600 mb-1">Clientes Premium</p>
          <p className="text-2xl font-bold text-gray-900">
            {data[data.length - 1]?.count || 0}
          </p>
          <p className="text-xs text-purple-700 mt-1">LTV $50,000+</p>
        </div>
      </div>

      {/* Gráfico de barras */}
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="range"
            angle={-45}
            textAnchor="end"
            height={100}
            interval={0}
            style={{ fontSize: '12px' }}
          />
          <YAxis label={{ value: 'Cantidad de Clientes', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            formatter={(value: number, name: string) => {
              if (name === 'Clientes') {
                return [value, 'Clientes'];
              }
              return [value, name];
            }}
          />
          <Bar dataKey="count" name="Clientes" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Tabla detallada */}
      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Rango de LTV
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Clientes
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                % del Total
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                Indicador
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {chartData.map((item) => (
              <tr key={item.range} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {item.range}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {item.count}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">
                  {item.percentage}%
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center justify-center">
                    <div
                      className="h-3 rounded-full"
                      style={{
                        width: `${item.percentage}%`,
                        backgroundColor: item.color,
                        minWidth: '20px',
                      }}
                    ></div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Interpretación */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Interpretación:</span> Este histograma muestra cómo se
          distribuyen los clientes según su gasto total (LTV). Los clientes en rangos superiores
          ($20,000+) son los más valiosos y requieren estrategias de retención premium. Los rangos
          inferiores representan oportunidades de crecimiento mediante upselling y cross-selling.
        </p>
      </div>
    </div>
  );
}

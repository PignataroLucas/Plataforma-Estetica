import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface FavoriteService {
  service_id: number;
  service_name: string;
  count: number;
  total_spent: number;
  percentage: number;
  last_visit: string | null;
}

interface FavoriteServicesChartProps {
  data: FavoriteService[];
  loading?: boolean;
}

const COLORS = [
  '#8b5cf6', // Purple
  '#3b82f6', // Blue
  '#10b981', // Green
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#ec4899', // Pink
  '#6366f1', // Indigo
  '#14b8a6', // Teal
  '#f97316', // Orange
  '#8b5cf6', // Purple (repeat)
];

export default function FavoriteServicesChart({
  data,
  loading = false,
}: FavoriteServicesChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="h-64 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Servicios Favoritos
        </h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Preparar datos para el pie chart (top 5)
  const chartData = data.slice(0, 5).map((service) => ({
    name: service.service_name,
    value: service.count,
    spent: service.total_spent,
  }));

  // Calcular estadísticas
  const totalVisits = data.reduce((sum, service) => sum + service.count, 0);
  const totalSpent = data.reduce((sum, service) => sum + service.total_spent, 0);
  const topService = data[0];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6 text-gray-800">
        Servicios Favoritos
      </h3>

      {/* Estadísticas */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-3 bg-purple-50 rounded-lg">
          <p className="text-xs text-purple-600 mb-1">Servicios Únicos</p>
          <p className="text-xl font-bold text-gray-900">{data.length}</p>
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-600 mb-1">Total Visitas</p>
          <p className="text-xl font-bold text-gray-900">{totalVisits}</p>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-xs text-green-600 mb-1">Gasto Total</p>
          <p className="text-xl font-bold text-gray-900">
            ${totalSpent.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
        </div>
      </div>

      {/* Servicio más frecuente */}
      {topService && (
        <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
          <p className="text-xs text-purple-600 font-semibold mb-2">
            🏆 SERVICIO MÁS FRECUENTE
          </p>
          <div className="flex justify-between items-center">
            <div>
              <p className="text-lg font-bold text-gray-900">
                {topService.service_name}
              </p>
              <p className="text-sm text-gray-600">
                {topService.count} visitas ({topService.percentage}% del total)
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-purple-600">
                ${topService.total_spent.toLocaleString('es-AR', {
                  maximumFractionDigits: 0,
                })}
              </p>
              <p className="text-xs text-gray-500">gastado</p>
            </div>
          </div>
        </div>
      )}

      {/* Gráfico de torta (top 5) */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-4">
          Distribución Top 5
        </h4>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) =>
                `${name}: ${(percent * 100).toFixed(0)}%`
              }
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string, props: any) => [
                `${value} visitas - $${props.payload.spent.toLocaleString('es-AR')}`,
                name,
              ]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Tabla completa */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">
          Todos los Servicios
        </h4>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  #
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Servicio
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Visitas
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  %
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Gasto Total
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Última Visita
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((service, index) => (
                <tr key={service.service_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {index + 1}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <div
                        className="w-3 h-3 rounded-full mr-2"
                        style={{
                          backgroundColor: COLORS[index % COLORS.length],
                        }}
                      ></div>
                      <span className="text-sm font-medium text-gray-900">
                        {service.service_name}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    <span className="text-sm font-semibold text-gray-900">
                      {service.count}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    <span className="text-sm text-gray-600">
                      {service.percentage}%
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <span className="text-sm font-semibold text-green-600">
                      $
                      {service.total_spent.toLocaleString('es-AR', {
                        maximumFractionDigits: 0,
                      })}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center text-sm text-gray-500">
                    {service.last_visit
                      ? format(new Date(service.last_visit), 'dd/MM/yyyy', {
                          locale: es,
                        })
                      : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

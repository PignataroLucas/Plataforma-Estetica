import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface MonthlyService {
  month: string;
  month_name: string;
  count: number;
  total_amount: number;
}

interface MonthlyServicesChartProps {
  data: MonthlyService[];
  loading?: boolean;
}

export default function MonthlyServicesChart({
  data,
  loading = false,
}: MonthlyServicesChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="h-80 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Servicios por Mes
        </h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Calcular estadísticas
  const totalServices = data.reduce((sum, item) => sum + item.count, 0);
  const totalAmount = data.reduce((sum, item) => sum + item.total_amount, 0);
  const avgServicesPerMonth = totalServices / data.length;
  const avgAmountPerMonth = totalAmount / data.length;

  // Encontrar mes con más servicios
  const maxMonth = data.reduce((max, item) =>
    item.count > max.count ? item : max
  );

  // Preparar datos para el gráfico
  const chartData = data.map((item) => ({
    name: item.month_name,
    Servicios: item.count,
    Monto: item.total_amount,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6 text-gray-800">
        Servicios por Mes (Últimos 12 Meses)
      </h3>

      {/* Estadísticas */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-600 mb-1">Total Servicios</p>
          <p className="text-xl font-bold text-gray-900">{totalServices}</p>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-xs text-green-600 mb-1">Gasto Total</p>
          <p className="text-xl font-bold text-gray-900">
            ${totalAmount.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <p className="text-xs text-purple-600 mb-1">Promedio Mensual</p>
          <p className="text-xl font-bold text-gray-900">
            {avgServicesPerMonth.toFixed(1)}
          </p>
        </div>
        <div className="p-3 bg-amber-50 rounded-lg">
          <p className="text-xs text-amber-600 mb-1">Mes Pico</p>
          <p className="text-sm font-bold text-gray-900">
            {maxMonth.month_name}
          </p>
          <p className="text-xs text-gray-600">{maxMonth.count} servicios</p>
        </div>
      </div>

      {/* Gráfico de barras */}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            yAxisId="left"
            orientation="left"
            label={{
              value: 'Servicios',
              angle: -90,
              position: 'insideLeft',
            }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            label={{
              value: 'Monto ($)',
              angle: 90,
              position: 'insideRight',
            }}
          />
          <Tooltip
            formatter={(value: number, name: string) => {
              if (name === 'Monto') {
                return `$${value.toLocaleString('es-AR', {
                  maximumFractionDigits: 0,
                })}`;
              }
              return value;
            }}
          />
          <Legend />
          <Bar yAxisId="left" dataKey="Servicios" fill="#3b82f6" />
          <Bar yAxisId="right" dataKey="Monto" fill="#10b981" />
        </BarChart>
      </ResponsiveContainer>

      {/* Tabla detallada */}
      <div className="mt-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">
          Detalle Mensual
        </h4>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mes
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Servicios
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monto Total
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Promedio por Servicio
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  % del Total
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((item) => {
                const avgPerService =
                  item.count > 0 ? item.total_amount / item.count : 0;
                const percentOfTotal =
                  totalServices > 0 ? (item.count / totalServices) * 100 : 0;

                return (
                  <tr
                    key={item.month}
                    className={
                      item.month === maxMonth.month
                        ? 'bg-amber-50 hover:bg-amber-100'
                        : 'hover:bg-gray-50'
                    }
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        {item.month_name}
                      </span>
                      {item.month === maxMonth.month && (
                        <span className="ml-2 text-xs bg-amber-200 text-amber-800 px-2 py-1 rounded">
                          Pico
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className="text-sm font-semibold text-blue-600">
                        {item.count}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <span className="text-sm font-semibold text-green-600">
                        $
                        {item.total_amount.toLocaleString('es-AR', {
                          maximumFractionDigits: 0,
                        })}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <span className="text-sm text-gray-600">
                        $
                        {avgPerService.toLocaleString('es-AR', {
                          maximumFractionDigits: 0,
                        })}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className="text-sm text-gray-600">
                        {percentOfTotal.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm font-bold text-gray-900">TOTAL</span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-center">
                  <span className="text-sm font-bold text-blue-600">
                    {totalServices}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right">
                  <span className="text-sm font-bold text-green-600">
                    $
                    {totalAmount.toLocaleString('es-AR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right">
                  <span className="text-sm font-bold text-gray-600">
                    $
                    {avgAmountPerMonth.toLocaleString('es-AR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-center">
                  <span className="text-sm font-bold text-gray-600">100%</span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}

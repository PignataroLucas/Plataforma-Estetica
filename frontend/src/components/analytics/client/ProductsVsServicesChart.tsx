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

interface MonthlyData {
  month: string;
  month_name: string;
  services: number;
  products: number;
  total: number;
  services_percentage: number;
  products_percentage: number;
}

interface ProductsVsServicesChartProps {
  data: {
    data: MonthlyData[];
    totals_12m: {
      services: number;
      products: number;
      total: number;
      services_percentage: number;
      products_percentage: number;
    };
  } | null;
  loading?: boolean;
}

export default function ProductsVsServicesChart({
  data,
  loading = false,
}: ProductsVsServicesChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="h-80 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Gasto: Productos vs Servicios por Mes
        </h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  const { data: monthlyData, totals_12m } = data;

  // Preparar datos para el gráfico
  const chartData = monthlyData.map((item) => ({
    name: item.month_name,
    Servicios: item.services,
    Productos: item.products,
  }));

  // Identificar oportunidades de upselling
  const lowProductsMonths = monthlyData.filter(
    (item) => item.total > 0 && item.products_percentage < 20
  ).length;

  const hasUpsellOpportunity = totals_12m.products_percentage < 30 && totals_12m.services > 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6 text-gray-800">
        Gasto: Productos vs Servicios por Mes
      </h3>

      {/* Estadísticas totales */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-3 bg-purple-50 rounded-lg">
          <p className="text-xs text-purple-600 mb-1">Total Servicios</p>
          <p className="text-xl font-bold text-gray-900">
            ${totals_12m.services.toLocaleString('es-AR', {
              maximumFractionDigits: 0,
            })}
          </p>
          <p className="text-xs text-gray-600">
            {totals_12m.services_percentage}% del total
          </p>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-xs text-green-600 mb-1">Total Productos</p>
          <p className="text-xl font-bold text-gray-900">
            ${totals_12m.products.toLocaleString('es-AR', {
              maximumFractionDigits: 0,
            })}
          </p>
          <p className="text-xs text-gray-600">
            {totals_12m.products_percentage}% del total
          </p>
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-600 mb-1">Total Combinado</p>
          <p className="text-xl font-bold text-gray-900">
            ${totals_12m.total.toLocaleString('es-AR', {
              maximumFractionDigits: 0,
            })}
          </p>
          <p className="text-xs text-gray-600">últimos 12 meses</p>
        </div>
      </div>

      {/* Alerta de oportunidad de upselling */}
      {hasUpsellOpportunity && (
        <div className="mb-6 p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg border border-amber-200">
          <div className="flex items-start">
            <span className="text-2xl mr-3">💡</span>
            <div>
              <p className="text-sm font-semibold text-amber-900 mb-1">
                Oportunidad de Upselling
              </p>
              <p className="text-sm text-amber-800">
                Este cliente gasta principalmente en servicios ({totals_12m.services_percentage}%).
                Existe una oportunidad para ofrecer productos complementarios.
              </p>
              {lowProductsMonths > 0 && (
                <p className="text-xs text-amber-700 mt-1">
                  {lowProductsMonths} de los últimos 12 meses tuvieron compras de productos menores al 20%
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Gráfico de barras apiladas */}
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
            label={{
              value: 'Monto ($)',
              angle: -90,
              position: 'insideLeft',
            }}
          />
          <Tooltip
            formatter={(value: number) =>
              `$${value.toLocaleString('es-AR', { maximumFractionDigits: 0 })}`
            }
          />
          <Legend />
          <Bar dataKey="Servicios" stackId="a" fill="#8b5cf6" />
          <Bar dataKey="Productos" stackId="a" fill="#10b981" />
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
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Servicios
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Productos
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  % Servicios
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  % Productos
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {monthlyData.map((item) => (
                <tr key={item.month} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-sm font-medium text-gray-900">
                      {item.month_name}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <span className="text-sm font-semibold text-purple-600">
                      $
                      {item.services.toLocaleString('es-AR', {
                        maximumFractionDigits: 0,
                      })}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <span className="text-sm font-semibold text-green-600">
                      $
                      {item.products.toLocaleString('es-AR', {
                        maximumFractionDigits: 0,
                      })}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <span className="text-sm font-bold text-gray-900">
                      $
                      {item.total.toLocaleString('es-AR', {
                        maximumFractionDigits: 0,
                      })}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{
                            width: `${item.services_percentage}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-600">
                        {item.services_percentage}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{
                            width: `${item.products_percentage}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-600">
                        {item.products_percentage}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm font-bold text-gray-900">TOTAL</span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right">
                  <span className="text-sm font-bold text-purple-600">
                    $
                    {totals_12m.services.toLocaleString('es-AR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right">
                  <span className="text-sm font-bold text-green-600">
                    $
                    {totals_12m.products.toLocaleString('es-AR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right">
                  <span className="text-sm font-bold text-gray-900">
                    $
                    {totals_12m.total.toLocaleString('es-AR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-center">
                  <span className="text-sm font-bold text-gray-900">
                    {totals_12m.services_percentage}%
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-center">
                  <span className="text-sm font-bold text-gray-900">
                    {totals_12m.products_percentage}%
                  </span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Insights */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Insights</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>
            • El cliente gasta <strong>{totals_12m.services_percentage}%</strong> en servicios
            y <strong>{totals_12m.products_percentage}%</strong> en productos
          </li>
          {totals_12m.services_percentage > 70 && (
            <li>
              • Perfil orientado a servicios - Oportunidad para promocionar líneas de productos
            </li>
          )}
          {totals_12m.products_percentage > 40 && (
            <li>
              • Cliente que invierte en productos - Buen candidato para lanzamientos de nuevas líneas
            </li>
          )}
          {lowProductsMonths > 6 && (
            <li>
              • En más de la mitad de los meses, las compras de productos fueron bajas
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface ServiceProfitabilityData {
  service_id: number;
  service_name: string;
  quantity: number;
  revenue: number;
  cost: number;
  gross_margin: number;
  margin_percentage: number;
}

interface ServiceProfitabilityChartProps {
  data: ServiceProfitabilityData[] | null;
  loading?: boolean;
}

export default function ServiceProfitabilityChart({
  data,
  loading = false,
}: ServiceProfitabilityChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-64 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Análisis de Rentabilidad por Servicio
        </h3>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Preparar datos para el gráfico (top 10)
  const chartData = data.slice(0, 10).map((item) => ({
    name: item.service_name,
    'Ingresos': item.revenue,
    'Costos': item.cost,
    'Margen': item.gross_margin,
    margin_percentage: item.margin_percentage,
  }));

  // Función para determinar el color según el margen
  const getMarginColor = (margin: number) => {
    if (margin >= 70) return '#10b981'; // Verde para márgenes altos
    if (margin >= 40) return '#3b82f6'; // Azul para márgenes medios
    if (margin >= 20) return '#f59e0b'; // Amarillo para márgenes bajos
    return '#ef4444'; // Rojo para márgenes muy bajos o negativos
  };

  // Encontrar el más y menos rentable
  const mostProfitable = [...data].sort((a, b) => b.margin_percentage - a.margin_percentage)[0];
  const leastProfitable = [...data].sort((a, b) => a.margin_percentage - b.margin_percentage)[0];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Análisis de Rentabilidad por Servicio
      </h3>

      {/* Insights destacados */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <p className="text-sm text-green-600 mb-1">Más Rentable</p>
          <p className="text-lg font-bold text-gray-900">{mostProfitable.service_name}</p>
          <p className="text-sm text-green-700 mt-1">
            {mostProfitable.margin_percentage.toFixed(1)}% de margen
          </p>
        </div>
        <div className="p-4 bg-red-50 rounded-lg border border-red-200">
          <p className="text-sm text-red-600 mb-1">Menos Rentable</p>
          <p className="text-lg font-bold text-gray-900">{leastProfitable.service_name}</p>
          <p className="text-sm text-red-700 mt-1">
            {leastProfitable.margin_percentage.toFixed(1)}% de margen
          </p>
        </div>
      </div>

      {/* Gráfico de barras */}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            interval={0}
            style={{ fontSize: '12px' }}
          />
          <YAxis />
          <Tooltip
            formatter={(value: number) => `$${value.toLocaleString('es-AR')}`}
          />
          <Legend />
          <Bar dataKey="Ingresos" fill="#3b82f6" />
          <Bar dataKey="Costos" fill="#ef4444" />
          <Bar dataKey="Margen" fill="#10b981" />
        </BarChart>
      </ResponsiveContainer>

      {/* Tabla detallada */}
      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Servicio
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Cantidad
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Ingresos
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Costos
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Margen Bruto
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                % Margen
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((item) => (
              <tr key={item.service_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {item.service_name}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">
                  {item.quantity}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  ${item.revenue.toLocaleString('es-AR')}
                </td>
                <td className="px-4 py-3 text-sm text-right text-red-600">
                  ${item.cost.toLocaleString('es-AR')}
                </td>
                <td className="px-4 py-3 text-sm text-right text-green-600 font-medium">
                  ${item.gross_margin.toLocaleString('es-AR')}
                </td>
                <td className="px-4 py-3 text-sm text-right">
                  <span
                    className="px-2 py-1 rounded-full text-xs font-semibold"
                    style={{
                      backgroundColor: `${getMarginColor(item.margin_percentage)}20`,
                      color: getMarginColor(item.margin_percentage),
                    }}
                  >
                    {item.margin_percentage.toFixed(1)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Leyenda de interpretación */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Interpretación:</span> El margen de rentabilidad considera
          los costos de máquinas alquiladas para servicios que las requieren. Un margen alto (70%+)
          indica alta rentabilidad. Márgenes bajos (menos de 20%) sugieren revisar precios o costos
          operativos.
        </p>
      </div>
    </div>
  );
}

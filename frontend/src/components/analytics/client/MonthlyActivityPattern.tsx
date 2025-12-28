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

interface MonthData {
  month: number;
  month_name: string;
  total_visits: number;
  average_visits: number;
  years_counted: number;
}

interface MonthlyActivityPatternProps {
  data: {
    data: MonthData[];
    peak_month: string | null;
    low_month: string | null;
    preferred_season: string | null;
    years_analyzed: number;
  } | null;
  loading?: boolean;
}

export default function MonthlyActivityPattern({
  data,
  loading = false,
}: MonthlyActivityPatternProps) {
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
          Patrón de Actividad Anual
        </h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  const { data: monthlyData, peak_month, low_month, preferred_season, years_analyzed } = data;

  // Determinar colores para cada barra
  const getBarColor = (monthName: string) => {
    if (monthName === peak_month) return '#10b981'; // Verde - Mes pico
    if (monthName === low_month) return '#ef4444';  // Rojo - Mes bajo
    return '#3b82f6'; // Azul - Normal
  };

  // Preparar datos para el gráfico
  const chartData = monthlyData.map((item) => ({
    name: item.month_name.slice(0, 3), // Abreviatura (Ene, Feb, etc)
    fullName: item.month_name,
    value: item.average_visits,
    total: item.total_visits,
    color: getBarColor(item.month_name),
  }));

  // Calcular promedio general
  const overallAvg = monthlyData.reduce((sum, item) => sum + item.average_visits, 0) / 12;

  // Determinar mensaje interpretativo
  const getInterpretation = () => {
    if (!preferred_season) return 'No hay suficientes datos para determinar un patrón estacional';

    const seasonMessages = {
      'Verano': '☀️ Este cliente tiende a visitarnos más en verano (Dic-Feb)',
      'Otoño': '🍂 Este cliente tiende a visitarnos más en otoño (Mar-May)',
      'Invierno': '❄️ Este cliente tiende a visitarnos más en invierno (Jun-Ago)',
      'Primavera': '🌸 Este cliente tiende a visitarnos más en primavera (Sep-Nov)',
    };

    return seasonMessages[preferred_season as keyof typeof seasonMessages] || '';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6 text-gray-800">
        Patrón de Actividad Anual
      </h3>

      {/* Estadísticas */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-xs text-green-600 mb-1">Mes Pico</p>
          <p className="text-xl font-bold text-gray-900">{peak_month || 'N/A'}</p>
          {peak_month && (
            <p className="text-xs text-gray-600">
              Mayor actividad
            </p>
          )}
        </div>
        <div className="p-3 bg-red-50 rounded-lg">
          <p className="text-xs text-red-600 mb-1">Mes Bajo</p>
          <p className="text-xl font-bold text-gray-900">{low_month || 'N/A'}</p>
          {low_month && (
            <p className="text-xs text-gray-600">
              Menor actividad
            </p>
          )}
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-600 mb-1">Años Analizados</p>
          <p className="text-xl font-bold text-gray-900">{years_analyzed}</p>
          <p className="text-xs text-gray-600">
            {years_analyzed === 1 ? 'año' : 'años'} de historia
          </p>
        </div>
      </div>

      {/* Mensaje interpretativo */}
      {preferred_season && (
        <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
          <p className="text-sm font-medium text-gray-900">
            {getInterpretation()}
          </p>
        </div>
      )}

      {/* Gráfico de barras */}
      <ResponsiveContainer width="100%" height={300}>
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
            tick={{ fontSize: 12 }}
          />
          <YAxis
            label={{
              value: 'Promedio de Visitas',
              angle: -90,
              position: 'insideLeft',
            }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 rounded shadow-lg border border-gray-200">
                    <p className="font-semibold text-gray-900">{data.fullName}</p>
                    <p className="text-sm text-gray-600">
                      Promedio: <span className="font-semibold">{data.value.toFixed(2)}</span> visitas
                    </p>
                    <p className="text-sm text-gray-600">
                      Total histórico: <span className="font-semibold">{data.total}</span> visitas
                    </p>
                    {data.fullName === peak_month && (
                      <p className="text-xs text-green-600 mt-1">🏆 Mes pico</p>
                    )}
                    {data.fullName === low_month && (
                      <p className="text-xs text-red-600 mt-1">📉 Mes bajo</p>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Línea de promedio general */}
      <div className="mt-4 flex items-center justify-center">
        <div className="text-sm text-gray-600">
          Promedio anual: <span className="font-semibold">{overallAvg.toFixed(2)}</span> visitas por mes
        </div>
      </div>

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
                  Total Visitas
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Promedio Anual
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  vs Promedio
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {monthlyData.map((item) => {
                const diffFromAvg = item.average_visits - overallAvg;
                const percentDiff = overallAvg > 0 ? (diffFromAvg / overallAvg) * 100 : 0;

                return (
                  <tr
                    key={item.month}
                    className={
                      item.month_name === peak_month
                        ? 'bg-green-50'
                        : item.month_name === low_month
                        ? 'bg-red-50'
                        : 'hover:bg-gray-50'
                    }
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-900">
                          {item.month_name}
                        </span>
                        {item.month_name === peak_month && (
                          <span className="ml-2 text-xs bg-green-200 text-green-800 px-2 py-1 rounded">
                            Pico
                          </span>
                        )}
                        {item.month_name === low_month && (
                          <span className="ml-2 text-xs bg-red-200 text-red-800 px-2 py-1 rounded">
                            Bajo
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className="text-sm font-semibold text-gray-900">
                        {item.total_visits}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className="text-sm text-gray-900">
                        {item.average_visits.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span
                        className={`text-sm font-semibold ${
                          diffFromAvg > 0
                            ? 'text-green-600'
                            : diffFromAvg < 0
                            ? 'text-red-600'
                            : 'text-gray-600'
                        }`}
                      >
                        {diffFromAvg > 0 ? '+' : ''}
                        {percentDiff.toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Insights</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>
            • Analizando <strong>{years_analyzed}</strong> {years_analyzed === 1 ? 'año' : 'años'} de historia del cliente
          </li>
          {peak_month && (
            <li>
              • <strong>{peak_month}</strong> es el mes con mayor actividad histórica
            </li>
          )}
          {low_month && (
            <li>
              • <strong>{low_month}</strong> es el mes con menor actividad
            </li>
          )}
          {preferred_season && (
            <li>
              • La temporada preferida del cliente es <strong>{preferred_season}</strong>
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}

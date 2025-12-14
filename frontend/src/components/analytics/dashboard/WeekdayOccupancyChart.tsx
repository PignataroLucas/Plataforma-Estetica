import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';

interface WeekdayData {
  day: string;
  count: number;
  occupancy_percentage: number;
}

interface WeekdayOccupancyChartProps {
  data: WeekdayData[] | null;
  loading?: boolean;
}

export default function WeekdayOccupancyChart({
  data,
  loading = false,
}: WeekdayOccupancyChartProps) {
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
          Ocupación por Día de la Semana
        </h3>
        <div className="flex items-center justify-center h-80">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  const dayLabels: Record<string, string> = {
    Monday: 'Lunes',
    Tuesday: 'Martes',
    Wednesday: 'Miércoles',
    Thursday: 'Jueves',
    Friday: 'Viernes',
    Saturday: 'Sábado',
    Sunday: 'Domingo',
  };

  // Ordenar días de lunes a domingo
  const orderedDays = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
  ];

  const chartData = orderedDays
    .map((day) => {
      const dayData = data.find((d) => d.day === day);
      return {
        day: dayLabels[day],
        occupancy: dayData?.occupancy_percentage || 0,
        count: dayData?.count || 0,
      };
    });

  // Función para obtener color según el porcentaje de ocupación
  const getBarColor = (value: number): string => {
    if (value >= 70) return '#10b981'; // Verde para ocupación ideal o alta
    if (value >= 50) return '#3b82f6'; // Azul para ocupación media-alta
    if (value >= 30) return '#f59e0b'; // Naranja para ocupación media-baja
    return '#ef4444'; // Rojo para ocupación baja
  };

  // Encontrar el día con mayor y menor ocupación
  const maxOccupancy = Math.max(...chartData.map((d) => d.occupancy));
  const minOccupancy = Math.min(...chartData.map((d) => d.occupancy));
  const bestDay = chartData.find((d) => d.occupancy === maxOccupancy);
  const worstDay = chartData.find((d) => d.occupancy === minOccupancy);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Ocupación por Día de la Semana
      </h3>

      {/* Insights destacados */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <p className="text-sm text-green-600 mb-1">Día Más Ocupado</p>
          <p className="text-lg font-bold text-gray-900">{bestDay?.day}</p>
          <p className="text-sm text-green-700 mt-1">
            {bestDay?.occupancy.toFixed(1)}% de ocupación
          </p>
        </div>
        <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
          <p className="text-sm text-orange-600 mb-1">Día Menos Ocupado</p>
          <p className="text-lg font-bold text-gray-900">{worstDay?.day}</p>
          <p className="text-sm text-orange-700 mt-1">
            {worstDay?.occupancy.toFixed(1)}% de ocupación
          </p>
        </div>
      </div>

      {/* Gráfico */}
      <ResponsiveContainer width="100%" height={350}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" domain={[0, 100]} unit="%" />
          <YAxis dataKey="day" type="category" width={80} />
          <Tooltip
            formatter={(value: number, name: string) => {
              if (name === 'Ocupación') {
                return [`${value.toFixed(1)}%`, 'Ocupación'];
              }
              return [value, name];
            }}
            labelFormatter={(label) => `${label}`}
          />
          <Legend />
          <ReferenceLine
            x={70}
            stroke="#10b981"
            strokeDasharray="3 3"
            label={{ value: 'Meta: 70%', position: 'top', fill: '#10b981' }}
          />
          <Bar dataKey="occupancy" name="Ocupación" radius={[0, 8, 8, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.occupancy)} />
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
                Día
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Turnos Completados
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                % Ocupación
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {chartData.map((item) => (
              <tr key={item.day} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {item.day}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">
                  {item.count}
                </td>
                <td className="px-4 py-3 text-sm text-right">
                  <span
                    className="px-2 py-1 rounded-full text-xs font-semibold"
                    style={{
                      backgroundColor: `${getBarColor(item.occupancy)}20`,
                      color: getBarColor(item.occupancy),
                    }}
                  >
                    {item.occupancy.toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {item.occupancy >= 70 ? (
                    <span className="text-green-600 font-medium">Óptimo</span>
                  ) : item.occupancy >= 50 ? (
                    <span className="text-blue-600 font-medium">Bueno</span>
                  ) : item.occupancy >= 30 ? (
                    <span className="text-orange-600 font-medium">Mejorable</span>
                  ) : (
                    <span className="text-red-600 font-medium">Bajo</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recomendaciones */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Recomendaciones:</span> La línea verde punteada
          marca el 70% de ocupación ideal. Días con ocupación baja pueden beneficiarse de
          promociones o ajustes en los horarios del personal. Días con alta ocupación
          requieren suficiente personal asignado.
        </p>
      </div>
    </div>
  );
}

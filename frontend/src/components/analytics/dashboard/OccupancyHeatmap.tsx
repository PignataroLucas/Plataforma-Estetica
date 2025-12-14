interface HeatmapData {
  day: string;
  morning: number;
  afternoon: number;
  evening: number;
}

interface OccupancyHeatmapProps {
  data: HeatmapData[] | null;
  loading?: boolean;
}

export default function OccupancyHeatmap({
  data,
  loading = false,
}: OccupancyHeatmapProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-96 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Mapa de Calor - Ocupación por Horario
        </h3>
        <div className="flex items-center justify-center h-96">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Función para obtener color según porcentaje de ocupación
  const getHeatColor = (percentage: number): string => {
    if (percentage >= 80) return 'bg-green-600';
    if (percentage >= 60) return 'bg-green-400';
    if (percentage >= 40) return 'bg-yellow-400';
    if (percentage >= 20) return 'bg-orange-400';
    if (percentage > 0) return 'bg-red-400';
    return 'bg-gray-200';
  };

  // Función para obtener color de texto según fondo
  const getTextColor = (percentage: number): string => {
    if (percentage >= 40) return 'text-white';
    return 'text-gray-800';
  };

  const timeSlots = [
    { key: 'morning', label: 'Mañana', time: '6AM - 12PM' },
    { key: 'afternoon', label: 'Tarde', time: '12PM - 6PM' },
    { key: 'evening', label: 'Noche', time: '6PM - 12AM' },
  ];

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

  const orderedData = orderedDays
    .map((day) => data.find((d) => d.day === day))
    .filter((d) => d !== undefined) as HeatmapData[];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Mapa de Calor - Ocupación por Horario
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="p-2 text-left text-xs font-medium text-gray-500 uppercase border-b-2">
                Día
              </th>
              {timeSlots.map((slot) => (
                <th
                  key={slot.key}
                  className="p-2 text-center text-xs font-medium text-gray-500 uppercase border-b-2"
                >
                  <div>{slot.label}</div>
                  <div className="text-xs font-normal text-gray-400">
                    {slot.time}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {orderedData.map((dayData) => (
              <tr key={dayData.day} className="border-b">
                <td className="p-2 text-sm font-medium text-gray-700">
                  {dayLabels[dayData.day]}
                </td>
                {timeSlots.map((slot) => {
                  const value = dayData[slot.key as keyof Omit<HeatmapData, 'day'>];
                  return (
                    <td key={slot.key} className="p-2">
                      <div
                        className={`
                          ${getHeatColor(value)}
                          ${getTextColor(value)}
                          rounded-lg p-4 text-center font-bold text-lg
                          transition-all duration-200 hover:scale-105 hover:shadow-lg
                          cursor-pointer
                        `}
                        title={`${dayLabels[dayData.day]} - ${slot.label}: ${value}% ocupación`}
                      >
                        {value}%
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Leyenda */}
      <div className="mt-6 flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">
            Nivel de ocupación:
          </span>
          <div className="flex items-center space-x-1">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-gray-200 rounded mr-1"></div>
              <span className="text-xs text-gray-600">0%</span>
            </div>
            <div className="flex items-center ml-2">
              <div className="w-6 h-6 bg-red-400 rounded mr-1"></div>
              <span className="text-xs text-gray-600">1-20%</span>
            </div>
            <div className="flex items-center ml-2">
              <div className="w-6 h-6 bg-orange-400 rounded mr-1"></div>
              <span className="text-xs text-gray-600">20-40%</span>
            </div>
            <div className="flex items-center ml-2">
              <div className="w-6 h-6 bg-yellow-400 rounded mr-1"></div>
              <span className="text-xs text-gray-600">40-60%</span>
            </div>
            <div className="flex items-center ml-2">
              <div className="w-6 h-6 bg-green-400 rounded mr-1"></div>
              <span className="text-xs text-gray-600">60-80%</span>
            </div>
            <div className="flex items-center ml-2">
              <div className="w-6 h-6 bg-green-600 rounded mr-1"></div>
              <span className="text-xs text-gray-600">80-100%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Interpretación:</span> Este mapa de calor muestra
          los horarios con mayor demanda. Los colores verdes indican alta ocupación (ideal
          para asignar más personal), mientras que los rojos/naranjas sugieren horarios con
          baja demanda (oportunidades para promociones o ajuste de horarios).
        </p>
      </div>
    </div>
  );
}

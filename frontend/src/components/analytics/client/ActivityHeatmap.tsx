import { useState } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface ActivityDay {
  date: string;
  count: number;
  day_of_week: number;
  week_of_year: number;
}

interface ActivityHeatmapProps {
  data: {
    data: ActivityDay[];
    max_activity: number;
    total_days: number;
    active_days: number;
  } | null;
  loading?: boolean;
}

export default function ActivityHeatmap({
  data,
  loading = false,
}: ActivityHeatmapProps) {
  const [hoveredDay, setHoveredDay] = useState<ActivityDay | null>(null);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="h-40 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Actividad de los Últimos 365 Días
        </h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Obtener color basado en la actividad
  const getActivityColor = (count: number, maxActivity: number) => {
    if (count === 0) return '#ebedf0'; // Gris claro
    const intensity = count / maxActivity;

    if (intensity >= 0.75) return '#10b981'; // Verde oscuro
    if (intensity >= 0.5) return '#34d399';  // Verde medio
    if (intensity >= 0.25) return '#6ee7b7'; // Verde claro
    return '#a7f3d0'; // Verde muy claro
  };

  // Organizar datos por semana
  const weeks: ActivityDay[][] = [];
  let currentWeek: ActivityDay[] = [];
  let lastWeek = -1;

  data.data.forEach((day) => {
    if (day.week_of_year !== lastWeek && currentWeek.length > 0) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
    currentWeek.push(day);
    lastWeek = day.week_of_year;
  });

  if (currentWeek.length > 0) {
    weeks.push(currentWeek);
  }

  // Calcular porcentaje de días activos
  const activePercentage = data.total_days > 0
    ? ((data.active_days / data.total_days) * 100).toFixed(1)
    : '0';

  const avgVisitsPerActiveDay = data.active_days > 0
    ? (data.data.reduce((sum, day) => sum + day.count, 0) / data.active_days).toFixed(1)
    : '0';

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6 text-gray-800">
        Actividad de los Últimos 365 Días
      </h3>

      {/* Estadísticas */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-xs text-green-600 mb-1">Días Activos</p>
          <p className="text-xl font-bold text-gray-900">
            {data.active_days} <span className="text-sm font-normal text-gray-600">({activePercentage}%)</span>
          </p>
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-600 mb-1">Actividad Máxima</p>
          <p className="text-xl font-bold text-gray-900">
            {data.max_activity} <span className="text-sm font-normal text-gray-600">visitas/día</span>
          </p>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <p className="text-xs text-purple-600 mb-1">Promedio por Día Activo</p>
          <p className="text-xl font-bold text-gray-900">{avgVisitsPerActiveDay}</p>
        </div>
      </div>

      {/* Heatmap */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Labels de días de la semana */}
          <div className="flex mb-2">
            <div className="w-8"></div>
            <div className="flex-1">
              <div className="grid grid-cols-[repeat(53,_minmax(12px,_1fr))] gap-1">
                {weeks.map((week, weekIndex) => {
                  if (weekIndex % 4 === 0 && week.length > 0) {
                    return (
                      <div key={weekIndex} className="col-span-1 text-xs text-gray-500 text-center">
                        {format(new Date(week[0].date), 'MMM', { locale: es })}
                      </div>
                    );
                  }
                  return <div key={weekIndex}></div>;
                })}
              </div>
            </div>
          </div>

          {/* Días de la semana + celdas */}
          <div className="flex">
            {/* Labels días */}
            <div className="w-8 flex flex-col justify-around text-xs text-gray-500">
              <div>Lun</div>
              <div>Mié</div>
              <div>Vie</div>
            </div>

            {/* Grid del heatmap */}
            <div className="flex-1">
              <div className="grid grid-cols-[repeat(53,_minmax(12px,_1fr))] gap-1">
                {weeks.map((week, weekIndex) => (
                  <div key={weekIndex} className="grid grid-rows-7 gap-1">
                    {/* Rellenar días vacíos al inicio de la primera semana */}
                    {weekIndex === 0 &&
                      Array.from({ length: week[0].day_of_week }).map((_, i) => (
                        <div key={`empty-${i}`} className="w-3 h-3"></div>
                      ))}

                    {/* Días de la semana */}
                    {week.map((day) => (
                      <div
                        key={day.date}
                        className="w-3 h-3 rounded-sm cursor-pointer transition-all hover:ring-2 hover:ring-blue-400"
                        style={{
                          backgroundColor: getActivityColor(day.count, data.max_activity),
                        }}
                        onMouseEnter={() => setHoveredDay(day)}
                        onMouseLeave={() => setHoveredDay(null)}
                        title={`${format(new Date(day.date), 'dd/MM/yyyy', { locale: es })}: ${day.count} visitas`}
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tooltip información del día */}
      {hoveredDay && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm font-medium text-gray-900">
            {format(new Date(hoveredDay.date), "EEEE, d 'de' MMMM 'de' yyyy", { locale: es })}
          </p>
          <p className="text-sm text-gray-600">
            {hoveredDay.count === 0
              ? 'Sin actividad'
              : hoveredDay.count === 1
              ? '1 visita'
              : `${hoveredDay.count} visitas`
            }
          </p>
        </div>
      )}

      {/* Leyenda */}
      <div className="mt-6 flex items-center justify-between text-xs text-gray-600">
        <span>Menos actividad</span>
        <div className="flex gap-1 items-center">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#ebedf0' }}></div>
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#a7f3d0' }}></div>
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#6ee7b7' }}></div>
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#34d399' }}></div>
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#10b981' }}></div>
        </div>
        <span>Más actividad</span>
      </div>

      {/* Insights */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Insights</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>
            • Has tenido actividad en <strong>{data.active_days}</strong> de los últimos <strong>{data.total_days}</strong> días
          </li>
          <li>
            • Tu día más activo tuvo <strong>{data.max_activity}</strong> {data.max_activity === 1 ? 'visita' : 'visitas'}
          </li>
          <li>
            • En promedio, realizas <strong>{avgVisitsPerActiveDay}</strong> {parseFloat(avgVisitsPerActiveDay) === 1 ? 'visita' : 'visitas'} por día activo
          </li>
        </ul>
      </div>
    </div>
  );
}

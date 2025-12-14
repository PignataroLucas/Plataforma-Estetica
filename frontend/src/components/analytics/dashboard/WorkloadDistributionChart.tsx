import { useState } from 'react';
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

interface WorkloadDistributionChartProps {
  data: any[] | null;
  loading?: boolean;
}

export default function WorkloadDistributionChart({
  data,
  loading = false,
}: WorkloadDistributionChartProps) {
  const [viewMode, setViewMode] = useState<'weekday' | 'time_slot'>('weekday');

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
          Distribución de Carga de Trabajo
        </h3>
        <div className="flex items-center justify-center h-96">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Extraer nombres de empleados (todas las keys excepto 'day' o 'time_slot')
  const employeeNames = Object.keys(data[0] || {}).filter(
    (key) => key !== 'day' && key !== 'time_slot'
  );

  // Colores para las barras de diferentes empleados
  const colors = [
    '#3b82f6',
    '#10b981',
    '#f59e0b',
    '#ef4444',
    '#8b5cf6',
    '#ec4899',
    '#06b6d4',
    '#84cc16',
  ];

  // Traducir días
  const dayLabels: Record<string, string> = {
    Monday: 'Lunes',
    Tuesday: 'Martes',
    Wednesday: 'Miércoles',
    Thursday: 'Jueves',
    Friday: 'Viernes',
    Saturday: 'Sábado',
    Sunday: 'Domingo',
  };

  // Preparar datos para el gráfico
  const chartData = data.map((item) => {
    if (item.day) {
      return {
        ...item,
        label: dayLabels[item.day] || item.day,
      };
    } else {
      return {
        ...item,
        label: item.time_slot,
      };
    }
  });

  // Calcular estadísticas por empleado
  const employeeStats = employeeNames.map((employeeName) => {
    const total = data.reduce((sum, item) => sum + (item[employeeName] || 0), 0);
    return {
      name: employeeName,
      total,
    };
  }).sort((a, b) => b.total - a.total);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Distribución de Carga de Trabajo
        </h3>

        {/* Selector de vista */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('weekday')}
            className={`
              px-4 py-2 rounded-md text-sm font-medium transition-all duration-200
              ${
                viewMode === 'weekday'
                  ? 'bg-white text-blue-600 shadow'
                  : 'text-gray-600 hover:text-gray-800'
              }
            `}
          >
            Por Día
          </button>
          <button
            onClick={() => setViewMode('time_slot')}
            className={`
              px-4 py-2 rounded-md text-sm font-medium transition-all duration-200
              ${
                viewMode === 'time_slot'
                  ? 'bg-white text-blue-600 shadow'
                  : 'text-gray-600 hover:text-gray-800'
              }
            `}
          >
            Por Franja Horaria
          </button>
        </div>
      </div>

      {/* Gráfico */}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12 }}
            angle={viewMode === 'weekday' ? -45 : 0}
            textAnchor={viewMode === 'weekday' ? 'end' : 'middle'}
            height={viewMode === 'weekday' ? 80 : 30}
          />
          <YAxis label={{ value: 'Cantidad de Servicios', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          {employeeNames.map((employeeName, index) => (
            <Bar
              key={employeeName}
              dataKey={employeeName}
              stackId="a"
              fill={colors[index % colors.length]}
              name={employeeName}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* Estadísticas por empleado */}
      <div className="mt-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">
          Total de Servicios por Empleado
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {employeeStats.map((stat, index) => (
            <div
              key={stat.name}
              className="p-3 rounded-lg border-2"
              style={{
                borderColor: colors[index % colors.length],
                backgroundColor: `${colors[index % colors.length]}10`,
              }}
            >
              <p className="text-xs font-medium text-gray-600 mb-1 truncate" title={stat.name}>
                {stat.name}
              </p>
              <p
                className="text-2xl font-bold"
                style={{ color: colors[index % colors.length] }}
              >
                {stat.total}
              </p>
              <p className="text-xs text-gray-500">servicios</p>
            </div>
          ))}
        </div>
      </div>

      {/* Análisis de balanceo */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Análisis de balanceo:</span>{' '}
          {(() => {
            const max = Math.max(...employeeStats.map((s) => s.total));
            const min = Math.min(...employeeStats.map((s) => s.total));
            const diff = max - min;
            const avgDiff = (diff / max) * 100;

            if (avgDiff < 20) {
              return (
                <>
                  La carga de trabajo está <span className="font-semibold text-green-600">muy bien balanceada</span>{' '}
                  entre los empleados (diferencia del {avgDiff.toFixed(0)}%).
                </>
              );
            } else if (avgDiff < 40) {
              return (
                <>
                  La carga de trabajo está <span className="font-semibold text-blue-600">razonablemente balanceada</span>{' '}
                  (diferencia del {avgDiff.toFixed(0)}%). Considere ajustes menores.
                </>
              );
            } else {
              return (
                <>
                  Existe un <span className="font-semibold text-orange-600">desbalance significativo</span>{' '}
                  en la carga de trabajo (diferencia del {avgDiff.toFixed(0)}%). Considere redistribuir turnos
                  para optimizar recursos.
                </>
              );
            }
          })()}
        </p>
      </div>
    </div>
  );
}

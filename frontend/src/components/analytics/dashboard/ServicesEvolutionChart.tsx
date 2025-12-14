import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';

interface ServicesEvolutionChartProps {
  data: any[] | null;
  loading?: boolean;
}

export default function ServicesEvolutionChart({
  data,
  loading = false,
}: ServicesEvolutionChartProps) {
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
          Evolución de Servicios en el Tiempo
        </h3>
        <div className="flex items-center justify-center h-96">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Extraer nombres de servicios (todas las keys excepto 'date')
  const serviceNames = Object.keys(data[0] || {}).filter((key) => key !== 'date');

  // Estado para controlar qué servicios se muestran
  const [visibleServices, setVisibleServices] = useState<Set<string>>(
    new Set(serviceNames)
  );

  // Colores para las líneas
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  const toggleService = (serviceName: string) => {
    const newVisible = new Set(visibleServices);
    if (newVisible.has(serviceName)) {
      newVisible.delete(serviceName);
    } else {
      newVisible.add(serviceName);
    }
    setVisibleServices(newVisible);
  };

  // Formatear datos para el gráfico
  const chartData = data.map((item) => ({
    ...item,
    date: format(parseISO(item.date), 'dd/MM'),
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Evolución de Servicios en el Tiempo
        </h3>
        <p className="text-sm text-gray-500">Top 5 servicios más solicitados</p>
      </div>

      {/* Selector de servicios */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg">
        <p className="text-sm font-medium text-gray-700 mb-2">
          Mostrar servicios:
        </p>
        <div className="flex flex-wrap gap-2">
          {serviceNames.map((serviceName, index) => (
            <button
              key={serviceName}
              onClick={() => toggleService(serviceName)}
              className={`
                px-3 py-1 rounded-full text-sm font-medium transition-all duration-200
                ${
                  visibleServices.has(serviceName)
                    ? 'text-white shadow-md'
                    : 'bg-gray-200 text-gray-500 hover:bg-gray-300'
                }
              `}
              style={{
                backgroundColor: visibleServices.has(serviceName)
                  ? colors[index % colors.length]
                  : undefined,
              }}
            >
              {serviceName}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Haz clic en un servicio para mostrarlo/ocultarlo
        </p>
      </div>

      {/* Gráfico */}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis label={{ value: 'Cantidad de Servicios', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            labelFormatter={(label) => `Fecha: ${label}`}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          {serviceNames.map((serviceName, index) => (
            <Line
              key={serviceName}
              type="monotone"
              dataKey={serviceName}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              hide={!visibleServices.has(serviceName)}
              name={serviceName}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Estadísticas por servicio */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-5 gap-4">
        {serviceNames.map((serviceName, index) => {
          const total = data.reduce((sum, item) => sum + (item[serviceName] || 0), 0);
          const average = Math.round(total / data.length);

          return (
            <div
              key={serviceName}
              className="p-3 rounded-lg border-2"
              style={{
                borderColor: colors[index % colors.length],
                backgroundColor: `${colors[index % colors.length]}10`,
              }}
            >
              <p className="text-xs font-medium text-gray-600 mb-1 truncate" title={serviceName}>
                {serviceName}
              </p>
              <p className="text-2xl font-bold" style={{ color: colors[index % colors.length] }}>
                {total}
              </p>
              <p className="text-xs text-gray-500">Total en período</p>
              <p className="text-sm text-gray-600 mt-1">
                Promedio: <span className="font-semibold">{average}</span>/día
              </p>
            </div>
          );
        })}
      </div>

      {/* Interpretación */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Interpretación:</span> Este gráfico muestra cómo
          varía la demanda de los servicios más populares a lo largo del tiempo. Las
          tendencias crecientes indican mayor popularidad, mientras que las decrecientes
          pueden requerir promociones o ajustes.
        </p>
      </div>
    </div>
  );
}

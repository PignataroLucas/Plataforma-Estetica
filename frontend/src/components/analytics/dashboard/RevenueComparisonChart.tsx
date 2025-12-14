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

interface ComparisonData {
  current: {
    start: string;
    end: string;
    total: number;
  };
  previous: {
    start: string;
    end: string;
    total: number;
  };
  change: number;
}

interface RevenueComparisonChartProps {
  data: ComparisonData | null;
  loading?: boolean;
}

export default function RevenueComparisonChart({
  data,
  loading = false,
}: RevenueComparisonChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-64 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Comparativa de Períodos
        </h3>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">
            Activa la comparación en los filtros para ver este gráfico
          </p>
        </div>
      </div>
    );
  }

  // Formatear fechas para mostrar
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-AR', { day: '2-digit', month: 'short' });
  };

  const currentLabel = `${formatDate(data.current.start)} - ${formatDate(data.current.end)}`;
  const previousLabel = `${formatDate(data.previous.start)} - ${formatDate(data.previous.end)}`;

  // Preparar datos para el gráfico
  const chartData = [
    {
      name: 'Período Anterior',
      revenue: data.previous.total,
      label: previousLabel,
    },
    {
      name: 'Período Actual',
      revenue: data.current.total,
      label: currentLabel,
    },
  ];

  // Determinar color según cambio
  const changeColor = data.change > 0 ? 'text-green-600' : data.change < 0 ? 'text-red-600' : 'text-gray-600';
  const changeIcon = data.change > 0 ? '↑' : data.change < 0 ? '↓' : '−';

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Comparativa de Períodos
        </h3>
        <div className={`text-sm font-medium ${changeColor}`}>
          {changeIcon} {Math.abs(data.change)}% vs período anterior
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            formatter={(value: number) => `$${value.toLocaleString('es-AR')}`}
            labelFormatter={(label) => {
              const item = chartData.find((d) => d.name === label);
              return item ? item.label : label;
            }}
          />
          <Legend />
          <Bar dataKey="revenue" fill="#3b82f6" name="Ingresos" />
        </BarChart>
      </ResponsiveContainer>

      {/* Detalles numéricos */}
      <div className="mt-6 grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
        <div>
          <p className="text-xs text-gray-600 mb-1">Período Anterior</p>
          <p className="text-sm font-medium text-gray-500">{previousLabel}</p>
          <p className="text-xl font-bold text-gray-900 mt-1">
            ${data.previous.total.toLocaleString('es-AR')}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-600 mb-1">Período Actual</p>
          <p className="text-sm font-medium text-gray-500">{currentLabel}</p>
          <p className="text-xl font-bold text-gray-900 mt-1">
            ${data.current.total.toLocaleString('es-AR')}
          </p>
        </div>
      </div>

      {/* Análisis del cambio */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          {data.change > 0 ? (
            <>
              <span className="font-semibold text-green-700">Crecimiento:</span>{' '}
              Los ingresos aumentaron{' '}
              <span className="font-bold">${(data.current.total - data.previous.total).toLocaleString('es-AR')}</span>{' '}
              ({data.change}%) respecto al período anterior.
            </>
          ) : data.change < 0 ? (
            <>
              <span className="font-semibold text-red-700">Decrecimiento:</span>{' '}
              Los ingresos disminuyeron{' '}
              <span className="font-bold">${(data.previous.total - data.current.total).toLocaleString('es-AR')}</span>{' '}
              ({Math.abs(data.change)}%) respecto al período anterior.
            </>
          ) : (
            <>
              <span className="font-semibold text-gray-700">Sin cambios:</span>{' '}
              Los ingresos se mantuvieron estables respecto al período anterior.
            </>
          )}
        </p>
      </div>
    </div>
  );
}

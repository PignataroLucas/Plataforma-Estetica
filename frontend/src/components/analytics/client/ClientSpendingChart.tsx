import {
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from 'recharts';

interface MonthlySpending {
  month: string;
  amount: number;
  visits: number;
}

interface ClientSpendingChartProps {
  data: MonthlySpending[];
  averageMonthly: number;
  loading?: boolean;
}

export default function ClientSpendingChart({
  data,
  averageMonthly,
  loading = false,
}: ClientSpendingChartProps) {
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
        <h3 className="text-lg font-semibold mb-4">
          Gasto Mensual (Últimos 12 Meses)
        </h3>
        <div className="h-80 flex items-center justify-center text-gray-400">
          No hay datos disponibles
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Gasto Mensual (Últimos 12 Meses)
        </h3>
        <div className="text-right">
          <p className="text-sm text-gray-600">Promedio Mensual</p>
          <p className="text-xl font-bold text-purple-600">
            ${averageMonthly.toLocaleString('es-AR')}
          </p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="month" stroke="#6b7280" style={{ fontSize: '12px' }} />
          <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
          <Tooltip
            formatter={(value: number, name: string) => {
              if (name === 'Gasto') {
                return [`$${value.toLocaleString('es-AR')}`, name];
              }
              return [value, name];
            }}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '14px' }} />

          <Bar
            dataKey="amount"
            fill="#8b5cf6"
            name="Gasto"
            radius={[8, 8, 0, 0]}
          />

          {/* Línea de promedio */}
          <Line
            type="monotone"
            dataKey={() => averageMonthly}
            stroke="#ef4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Promedio"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

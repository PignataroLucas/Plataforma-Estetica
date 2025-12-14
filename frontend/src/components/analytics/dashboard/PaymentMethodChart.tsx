import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface PaymentMethodData {
  method: string;
  amount: number;
  percentage: number;
  count: number;
}

interface PaymentMethodChartProps {
  data: PaymentMethodData[] | null;
  loading?: boolean;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  CASH: 'Efectivo',
  BANK_TRANSFER: 'Transferencia',
  DEBIT_CARD: 'Débito',
  CREDIT_CARD: 'Crédito',
  MERCADOPAGO: 'MercadoPago',
  OTHER: 'Otro',
};

export default function PaymentMethodChart({
  data,
  loading = false,
}: PaymentMethodChartProps) {
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
          Distribución por Método de Pago
        </h3>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Preparar datos para el gráfico
  const chartData = data.map((item) => ({
    name: PAYMENT_METHOD_LABELS[item.method] || item.method,
    value: item.amount,
    percentage: item.percentage,
    count: item.count,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Distribución por Método de Pago
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((_entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => `$${value.toLocaleString('es-AR')}`}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      {/* Tabla de detalles */}
      <div className="mt-6">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Método
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                Monto
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                %
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                Transacciones
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((item, index) => (
              <tr key={item.method} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900 flex items-center">
                  <div
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  ></div>
                  {PAYMENT_METHOD_LABELS[item.method] || item.method}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  ${item.amount.toLocaleString('es-AR')}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">
                  {item.percentage.toFixed(1)}%
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">
                  {item.count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

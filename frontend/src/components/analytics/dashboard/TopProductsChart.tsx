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

interface ProductData {
  product_id: number;
  product_name: string;
  quantity_sold: number;
  revenue: number;
  unit_price: number;
}

interface TopProductsChartProps {
  data: ProductData[];
  loading?: boolean;
}

export default function TopProductsChart({
  data,
  loading = false,
}: TopProductsChartProps) {
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
        <h3 className="text-lg font-semibold mb-4">Top 10 Productos</h3>
        <div className="h-80 flex items-center justify-center text-gray-400">
          No hay datos disponibles
        </div>
      </div>
    );
  }

  const topData = data.slice(0, 10);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Top 10 Productos Más Vendidos
      </h3>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={topData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis type="number" stroke="#6b7280" style={{ fontSize: '12px' }} />
          <YAxis
            type="category"
            dataKey="product_name"
            stroke="#6b7280"
            style={{ fontSize: '11px' }}
            width={150}
          />
          <Tooltip
            formatter={(value: number, name: string) => {
              if (name === 'Cantidad') return [value, name];
              return [`$${value.toLocaleString('es-AR')}`, name];
            }}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '14px' }} />

          <Bar
            dataKey="quantity_sold"
            fill="#10b981"
            name="Cantidad"
            radius={[0, 4, 4, 0]}
          />
          <Bar
            dataKey="revenue"
            fill="#3b82f6"
            name="Ingresos"
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

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

interface InventoryProduct {
  product_id: number;
  product_name: string;
  category: string;
  current_stock: number;
  sales_count: number;
  rotation_rate: number;
  days_of_inventory: number;
  speed: 'FAST' | 'MEDIUM' | 'SLOW' | 'DEAD';
  speed_label: string;
  stock_value: number;
  unit_price: number;
}

interface InventoryRotationData {
  period_days: number;
  products: InventoryProduct[];
  top_rotation: InventoryProduct[];
  dead_stock_items: InventoryProduct[];
  summary: {
    total_products: number;
    total_stock_value: number;
    fast_moving_count: number;
    medium_moving_count: number;
    slow_moving_count: number;
    dead_stock_count: number;
    avg_rotation_rate: number;
  };
}

interface InventoryRotationChartProps {
  data: InventoryRotationData | null;
  loading?: boolean;
}

export default function InventoryRotationChart({
  data,
  loading = false,
}: InventoryRotationChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-96 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || !data.products || data.products.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Rotación de Inventario
        </h3>
        <div className="flex items-center justify-center h-96">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Preparar datos para el gráfico de distribución
  const distributionData = [
    { name: 'Rápida', count: data.summary.fast_moving_count, color: '#10b981' },
    { name: 'Media', count: data.summary.medium_moving_count, color: '#3b82f6' },
    { name: 'Lenta', count: data.summary.slow_moving_count, color: '#f59e0b' },
    { name: 'Sin Movimiento', count: data.summary.dead_stock_count, color: '#ef4444' },
  ];

  // Función para obtener badge de velocidad
  const getSpeedBadge = (speed: string, speedLabel: string) => {
    const badges = {
      FAST: { bg: 'bg-green-100', text: 'text-green-800' },
      MEDIUM: { bg: 'bg-blue-100', text: 'text-blue-800' },
      SLOW: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
      DEAD: { bg: 'bg-red-100', text: 'text-red-800' },
    };

    const badge = badges[speed as keyof typeof badges] || badges.MEDIUM;

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badge.bg} ${badge.text}`}>
        {speedLabel}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Rotación de Inventario
        </h3>
        <span className="text-sm text-gray-600">Últimos {data.period_days} días</span>
      </div>

      {/* Estadísticas destacadas */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-600 mb-1">Valor Total de Stock</p>
          <p className="text-2xl font-bold text-gray-900">
            ${data.summary.total_stock_value.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-blue-700 mt-1">{data.summary.total_products} productos</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <p className="text-sm text-green-600 mb-1">Rotación Rápida</p>
          <p className="text-2xl font-bold text-gray-900">{data.summary.fast_moving_count}</p>
          <p className="text-xs text-green-700 mt-1">Productos top</p>
        </div>
        <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <p className="text-sm text-yellow-600 mb-1">Rotación Lenta</p>
          <p className="text-2xl font-bold text-gray-900">{data.summary.slow_moving_count}</p>
          <p className="text-xs text-yellow-700 mt-1">Revisar stock</p>
        </div>
        <div className="p-4 bg-red-50 rounded-lg border border-red-200">
          <p className="text-sm text-red-600 mb-1">Sin Movimiento</p>
          <p className="text-2xl font-bold text-gray-900">{data.summary.dead_stock_count}</p>
          <p className="text-xs text-red-700 mt-1">⚠️ Acción requerida</p>
        </div>
      </div>

      {/* Gráfico de distribución */}
      <div className="mb-6">
        <h4 className="text-md font-semibold text-gray-700 mb-3">Distribución por Velocidad</h4>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={distributionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis label={{ value: 'Cantidad de Productos', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Bar dataKey="count" name="Productos" radius={[8, 8, 0, 0]}>
              {distributionData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top 10 productos de mayor rotación */}
      {data.top_rotation.length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-semibold text-gray-700 mb-3">
            Top 10 Productos de Mayor Rotación
          </h4>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Producto
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Ventas
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Stock
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Tasa/Día
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Días Rest.
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    Velocidad
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.top_rotation.map((product, index) => (
                  <tr key={product.product_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {index + 1}. {product.product_name}
                        </p>
                        <p className="text-xs text-gray-500">{product.category}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">
                      {product.sales_count}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">
                      {product.current_stock}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-semibold text-green-600">
                      {product.rotation_rate.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">
                      {product.days_of_inventory === 999
                        ? '∞'
                        : Math.round(product.days_of_inventory)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {getSpeedBadge(product.speed, product.speed_label)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Productos sin movimiento (Dead Stock) */}
      {data.dead_stock_items.length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-semibold text-red-700 mb-3">
            ⚠️ Productos sin Movimiento ({data.dead_stock_items.length})
          </h4>
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-red-200">
                <thead className="bg-red-100">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-red-700 uppercase">
                      Producto
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-red-700 uppercase">
                      Stock
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-red-700 uppercase">
                      Valor
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-red-700 uppercase">
                      Acción
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-red-100">
                  {data.dead_stock_items.slice(0, 10).map((product) => (
                    <tr key={product.product_id} className="hover:bg-red-50">
                      <td className="px-4 py-3">
                        <p className="text-sm font-medium text-gray-900">
                          {product.product_name}
                        </p>
                        <p className="text-xs text-gray-500">{product.category}</p>
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-gray-900">
                        {product.current_stock}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-semibold text-red-600">
                        ${product.stock_value.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-xs text-red-600">Promoción / Descuento</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.dead_stock_items.length > 10 && (
              <p className="text-sm text-red-600 mt-3 text-center">
                +{data.dead_stock_items.length - 10} productos más sin movimiento
              </p>
            )}
          </div>
        </div>
      )}

      {/* Tabla completa de todos los productos */}
      <div>
        <h4 className="text-md font-semibold text-gray-700 mb-3">
          Todos los Productos ({data.products.length})
        </h4>
        <div className="overflow-x-auto max-h-96">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Producto
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Stock
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Ventas
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Tasa/Día
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Días Rest.
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Valor Stock
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Velocidad
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.products.map((product) => (
                <tr key={product.product_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium text-gray-900">
                      {product.product_name}
                    </p>
                    <p className="text-xs text-gray-500">{product.category}</p>
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {product.current_stock}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {product.sales_count}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                    {product.rotation_rate.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-600">
                    {product.days_of_inventory === 999
                      ? '∞'
                      : Math.round(product.days_of_inventory)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    ${product.stock_value.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {getSpeedBadge(product.speed, product.speed_label)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Interpretación */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Interpretación:</span> La rotación de inventario mide
          qué tan rápido vendes tus productos. Productos con rotación <strong>Rápida</strong> (más
          de 1 venta/día) son tus bestsellers - asegura stock suficiente. Productos{' '}
          <strong>Sin Movimiento</strong> representan capital inmovilizado - considera promociones
          o descuentos. La tasa promedio de rotación es{' '}
          <strong>{data.summary.avg_rotation_rate.toFixed(2)} ventas/día</strong>.
        </p>
      </div>
    </div>
  );
}

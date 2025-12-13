import { formatDateArgentina } from '@/utils/dateUtils';

interface ProductData {
  product_id: number;
  product_name: string;
  quantity: number;
  total_spent: number;
}

interface PurchaseData {
  date: string;
  product_id: number;
  product_name: string;
  amount: number;
  payment_method: string;
}

interface ClientProductsHistoryProps {
  data: {
    has_purchases: boolean;
    message?: string;
    top_products: ProductData[];
    recent_purchases: PurchaseData[];
    total_spent: number;
    total_products: number;
  } | null;
  loading?: boolean;
}

const paymentMethodLabels: Record<string, string> = {
  CASH: 'Efectivo',
  BANK_TRANSFER: 'Transferencia',
  DEBIT_CARD: 'Débito',
  CREDIT_CARD: 'Crédito',
  MERCADOPAGO: 'MercadoPago',
  OTHER: 'Otro',
};

export default function ClientProductsHistory({
  data,
  loading = false,
}: ClientProductsHistoryProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="space-y-3">
          <div className="h-20 bg-gray-100 rounded"></div>
          <div className="h-20 bg-gray-100 rounded"></div>
          <div className="h-20 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Si no tiene compras de productos
  if (!data.has_purchases) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Historial de Productos
        </h3>
        <div className="flex flex-col items-center justify-center py-12">
          <div className="text-6xl mb-4">📦</div>
          <p className="text-gray-500 text-center">
            {data.message || 'Este cliente aún no ha comprado productos'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Estadísticas generales */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 mb-1">Total Gastado en Productos</p>
          <p className="text-3xl font-bold text-green-600">
            ${data.total_spent.toLocaleString('es-AR')}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 mb-1">Total de Compras</p>
          <p className="text-3xl font-bold text-blue-600">{data.total_products}</p>
        </div>
      </div>

      {/* Top 5 Productos Favoritos */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Productos Favoritos (Top 5)
        </h3>
        {data.top_products && data.top_products.length > 0 ? (
          <div className="space-y-3">
            {data.top_products.map((product, index) => (
              <div
                key={product.product_id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-purple-100 text-purple-700 font-bold text-sm">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {product.product_name}
                    </p>
                    <p className="text-sm text-gray-600">
                      {product.quantity} {product.quantity === 1 ? 'compra' : 'compras'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">
                    ${product.total_spent.toLocaleString('es-AR')}
                  </p>
                  <p className="text-xs text-gray-500">Total gastado</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">
            No hay datos de productos favoritos
          </p>
        )}
      </div>

      {/* Historial de Compras Recientes */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Compras Recientes
        </h3>
        {data.recent_purchases && data.recent_purchases.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Fecha
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Producto
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Método de Pago
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Monto
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.recent_purchases.map((purchase, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatDateArgentina(purchase.date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {purchase.product_name}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {paymentMethodLabels[purchase.payment_method] ||
                          purchase.payment_method}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium text-gray-900">
                      ${purchase.amount.toLocaleString('es-AR')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">
            No hay compras recientes
          </p>
        )}
      </div>
    </div>
  );
}

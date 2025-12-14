import { useState } from 'react';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

interface TopClient {
  client_id: number;
  client_name: string;
  email: string;
  phone: string;
  ltv: number;
  visits_count: number;
  last_visit: string | null;
  status: 'VIP' | 'ACTIVE' | 'AT_RISK' | 'INACTIVE' | 'NEW';
}

interface TopClientsTableProps {
  data: TopClient[] | null;
  loading?: boolean;
}

export default function TopClientsTable({
  data,
  loading = false,
}: TopClientsTableProps) {
  const [sortBy, setSortBy] = useState<'ltv' | 'visits'>('ltv');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

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
          Top 20 Clientes por Gasto
        </h3>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Ordenar datos
  const sortedData = [...data].sort((a, b) => {
    const multiplier = sortOrder === 'desc' ? -1 : 1;
    if (sortBy === 'ltv') {
      return (a.ltv - b.ltv) * multiplier;
    } else {
      return (a.visits_count - b.visits_count) * multiplier;
    }
  });

  // Función para obtener badge de estado
  const getStatusBadge = (status: string) => {
    const badges = {
      VIP: { bg: 'bg-purple-100', text: 'text-purple-800', label: 'VIP' },
      ACTIVE: { bg: 'bg-green-100', text: 'text-green-800', label: 'Activo' },
      AT_RISK: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'En Riesgo' },
      INACTIVE: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Inactivo' },
      NEW: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Nuevo' },
    };

    const badge = badges[status as keyof typeof badges] || badges.ACTIVE;

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const handleSort = (column: 'ltv' | 'visits') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  // Calcular estadísticas
  const totalLTV = data.reduce((sum, client) => sum + client.ltv, 0);
  const avgLTV = totalLTV / data.length;
  const topClient = data[0];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Top 20 Clientes por Gasto
        </h3>
        <div className="text-sm text-gray-600">
          Total: {data.length} clientes
        </div>
      </div>

      {/* Estadísticas destacadas */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
          <p className="text-sm text-purple-600 mb-1">Cliente #1</p>
          <p className="text-lg font-bold text-gray-900">{topClient.client_name}</p>
          <p className="text-sm text-purple-700 mt-1">
            ${topClient.ltv.toLocaleString('es-AR')}
          </p>
        </div>
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-600 mb-1">LTV Promedio</p>
          <p className="text-2xl font-bold text-gray-900">
            ${avgLTV.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-blue-700 mt-1">Entre top 20</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <p className="text-sm text-green-600 mb-1">LTV Total Top 20</p>
          <p className="text-2xl font-bold text-gray-900">
            ${totalLTV.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-green-700 mt-1">Acumulado</p>
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                #
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Cliente
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Estado
              </th>
              <th
                className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('ltv')}
              >
                LTV {sortBy === 'ltv' && (sortOrder === 'desc' ? '↓' : '↑')}
              </th>
              <th
                className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('visits')}
              >
                Visitas {sortBy === 'visits' && (sortOrder === 'desc' ? '↓' : '↑')}
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Última Visita
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedData.map((client, index) => (
              <tr key={client.client_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-500">
                  {index + 1}
                </td>
                <td className="px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {client.client_name}
                    </p>
                    <p className="text-xs text-gray-500">{client.email || client.phone}</p>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {getStatusBadge(client.status)}
                </td>
                <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                  ${client.ltv.toLocaleString('es-AR')}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">
                  {client.visits_count}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {client.last_visit
                    ? format(parseISO(client.last_visit), 'dd MMM yyyy', { locale: es })
                    : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Interpretación */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Interpretación:</span> Estos son los clientes más
          valiosos por gasto total (LTV). Los clientes VIP tienen un LTV superior a $100,000.
          Enfoca estrategias de retención y beneficios especiales en estos clientes para
          maximizar su valor a largo plazo.
        </p>
      </div>
    </div>
  );
}

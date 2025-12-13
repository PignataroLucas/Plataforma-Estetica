
interface ClientSummary {
  client_info: {
    id: number;
    name: string;
    email: string;
    phone: string;
  };
  summary: {
    lifetime_value: number;
    total_visits: number;
    first_visit: string | null;
    last_visit: string | null;
    days_since_last_visit: number | null;
    average_frequency_days: number | null;
    average_ticket: number;
    status: 'VIP' | 'ACTIVE' | 'AT_RISK' | 'INACTIVE';
    status_color: string;
  };
}

interface ClientSummaryCardProps {
  data: ClientSummary | null;
  loading?: boolean;
}

export default function ClientSummaryCard({
  data,
  loading = false,
}: ClientSummaryCardProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          <div className="h-4 bg-gray-200 rounded w-4/6"></div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const { summary } = data;

  const getStatusBadgeColor = (color: string) => {
    const colors: Record<string, string> = {
      green: 'bg-green-100 text-green-800',
      blue: 'bg-blue-100 text-blue-800',
      yellow: 'bg-yellow-100 text-yellow-800',
      gray: 'bg-gray-100 text-gray-800',
    };
    return colors[color] || colors.gray;
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, string> = {
      VIP: '⭐',
      ACTIVE: '✅',
      AT_RISK: '⚠️',
      INACTIVE: '😴',
    };
    return icons[status] || '👤';
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg shadow-lg p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Resumen del Cliente
        </h2>
        <span
          className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusBadgeColor(
            summary.status_color
          )}`}
        >
          {getStatusIcon(summary.status)} {summary.status}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Lifetime Value */}
        <div className="bg-white rounded-lg p-4 shadow">
          <div className="flex items-center mb-2">
            <span className="text-2xl mr-2">💰</span>
            <p className="text-sm text-gray-600">Lifetime Value</p>
          </div>
          <p className="text-3xl font-bold text-purple-600">
            ${summary.lifetime_value.toLocaleString('es-AR')}
          </p>
        </div>

        {/* Total Visits */}
        <div className="bg-white rounded-lg p-4 shadow">
          <div className="flex items-center mb-2">
            <span className="text-2xl mr-2">🎯</span>
            <p className="text-sm text-gray-600">Total de Visitas</p>
          </div>
          <p className="text-3xl font-bold text-blue-600">
            {summary.total_visits}
          </p>
        </div>

        {/* Average Ticket */}
        <div className="bg-white rounded-lg p-4 shadow">
          <div className="flex items-center mb-2">
            <span className="text-2xl mr-2">🎫</span>
            <p className="text-sm text-gray-600">Ticket Promedio</p>
          </div>
          <p className="text-3xl font-bold text-green-600">
            ${summary.average_ticket.toLocaleString('es-AR')}
          </p>
        </div>

        {/* First Visit */}
        <div className="bg-white rounded-lg p-4 shadow">
          <div className="flex items-center mb-2">
            <span className="text-2xl mr-2">📅</span>
            <p className="text-sm text-gray-600">Cliente Desde</p>
          </div>
          <p className="text-lg font-semibold text-gray-800">
            {summary.first_visit
              ? new Date(summary.first_visit).toLocaleDateString('es-AR')
              : 'N/A'}
          </p>
        </div>

        {/* Last Visit */}
        <div className="bg-white rounded-lg p-4 shadow">
          <div className="flex items-center mb-2">
            <span className="text-2xl mr-2">📆</span>
            <p className="text-sm text-gray-600">Última Visita</p>
          </div>
          <p className="text-lg font-semibold text-gray-800">
            {summary.last_visit
              ? new Date(summary.last_visit).toLocaleDateString('es-AR')
              : 'N/A'}
          </p>
          {summary.days_since_last_visit !== null && (
            <p className="text-xs text-gray-500 mt-1">
              Hace {summary.days_since_last_visit} días
            </p>
          )}
        </div>

        {/* Frequency */}
        <div className="bg-white rounded-lg p-4 shadow">
          <div className="flex items-center mb-2">
            <span className="text-2xl mr-2">⏱️</span>
            <p className="text-sm text-gray-600">Frecuencia Promedio</p>
          </div>
          <p className="text-lg font-semibold text-gray-800">
            {summary.average_frequency_days
              ? `Cada ${summary.average_frequency_days} días`
              : 'N/A'}
          </p>
        </div>
      </div>
    </div>
  );
}

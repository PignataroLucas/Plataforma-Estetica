import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import api from '../../../services/api';

interface Service {
  id: number;
  date: string;
  time: string;
  service_id: number | null;
  service_name: string;
  professional_id: number | null;
  professional_name: string;
  amount: number;
  payment_method: string;
  payment_status: string;
  notes: string;
}

interface ServicesTimelineProps {
  clienteId: number;
}

export default function ServicesTimeline({ clienteId }: ServicesTimelineProps) {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 10;

  // Filtros
  const [servicioId, setServicioId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Estadísticas
  const [stats, setStats] = useState({
    total_services: 0,
    total_spent: 0,
    average_ticket: 0,
  });

  useEffect(() => {
    fetchServices();
  }, [clienteId, currentPage, servicioId, startDate, endDate]);

  const fetchServices = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('page', currentPage.toString());
      params.append('page_size', pageSize.toString());
      if (servicioId) params.append('servicio_id', servicioId);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const response = await api.get(
        `/analytics/client/${clienteId}/services/?${params.toString()}`
      );

      setServices(response.data.services_history);
      setCurrentPage(response.data.pagination.page);
      setTotalPages(response.data.pagination.total_pages);
      setTotalCount(response.data.pagination.total_count);
      setStats(response.data.statistics);
    } catch (err: any) {
      console.error('Error fetching services:', err);
      setError(err.message || 'Error al cargar el historial de servicios');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFilters = () => {
    setCurrentPage(1); // Reset to first page when applying filters
    fetchServices();
  };

  const handleClearFilters = () => {
    setServicioId('');
    setStartDate('');
    setEndDate('');
    setCurrentPage(1);
  };

  const getPaymentStatusBadge = (status: string) => {
    const badges = {
      PAGADO: { bg: 'bg-green-100', text: 'text-green-800', label: 'Pagado' },
      PENDIENTE: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pendiente' },
      CON_SENA: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Con Seña' },
    };

    const badge = badges[status as keyof typeof badges] || badges.PENDIENTE;

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  if (loading && services.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Historial de Servicios ({totalCount})
        </h3>

        {/* Estadísticas */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-blue-600 mb-1">Total Servicios</p>
            <p className="text-xl font-bold text-gray-900">{stats.total_services}</p>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <p className="text-xs text-green-600 mb-1">Gasto Total</p>
            <p className="text-xl font-bold text-gray-900">
              ${stats.total_spent.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg">
            <p className="text-xs text-purple-600 mb-1">Ticket Promedio</p>
            <p className="text-xl font-bold text-gray-900">
              ${stats.average_ticket.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
            </p>
          </div>
        </div>

        {/* Filtros */}
        <div className="flex flex-wrap gap-3 p-4 bg-gray-50 rounded-lg">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-600 mb-1">Desde</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-600 mb-1">Hasta</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={handleApplyFilters}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
            >
              Filtrar
            </button>
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300"
            >
              Limpiar
            </button>
          </div>
        </div>
      </div>

      {/* Timeline de servicios */}
      {services.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No se encontraron servicios</p>
        </div>
      ) : (
        <div className="space-y-4">
          {services.map((service) => (
            <div
              key={service.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="text-md font-semibold text-gray-900">
                      {service.service_name}
                    </h4>
                    {getPaymentStatusBadge(service.payment_status)}
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>
                      📅 {format(new Date(service.date), "EEEE, d 'de' MMMM 'de' yyyy", { locale: es })} - {service.time}
                    </p>
                    <p>👤 {service.professional_name}</p>
                    <p>💳 {service.payment_method}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-blue-600">
                    ${service.amount.toLocaleString('es-AR')}
                  </p>
                </div>
              </div>

              {service.notes && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500 mb-1">Notas:</p>
                  <p className="text-sm text-gray-700">{service.notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="mt-6 flex justify-between items-center">
          <p className="text-sm text-gray-600">
            Mostrando {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, totalCount)} de {totalCount}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            <span className="px-4 py-2 text-sm text-gray-700">
              Página {currentPage} de {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

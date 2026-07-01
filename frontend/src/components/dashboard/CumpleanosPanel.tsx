import { useState } from 'react';
import { Cumpleanos } from '../../hooks/useDashboard';
import { Modal, ModalHeader, ModalBody } from '../ui/Modal';
import ClientSummaryCard from '../analytics/client/ClientSummaryCard';
import api from '../../services/api';

interface CumpleanosPanelProps {
  cumpleanos: Cumpleanos[];
}

export default function CumpleanosPanel({ cumpleanos }: CumpleanosPanelProps) {
  const [selected, setSelected] = useState<Cumpleanos | null>(null);
  const [summary, setSummary] = useState<any | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [errorSummary, setErrorSummary] = useState<string | null>(null);

  const handleSelect = async (cliente: Cumpleanos) => {
    setSelected(cliente);
    setSummary(null);
    setErrorSummary(null);
    setLoadingSummary(true);
    try {
      const response = await api.get(`/analytics/client/${cliente.cliente_id}/summary/`);
      setSummary(response.data);
    } catch (err: any) {
      setErrorSummary(
        err.response?.data?.error || 'No se pudo cargar el resumen del cliente'
      );
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleClose = () => {
    setSelected(null);
    setSummary(null);
    setErrorSummary(null);
  };

  const etiquetaDias = (c: Cumpleanos) => {
    if (c.cumple_hoy) return '¡Hoy! 🎉';
    if (c.dias_para_cumple === 1) return 'Mañana';
    return `En ${c.dias_para_cumple} días`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        🎂 Próximos Cumpleaños{cumpleanos.length > 0 ? ` (${cumpleanos.length})` : ''}
      </h3>

      {cumpleanos.length === 0 ? (
        <div className="text-center py-8">
          <span className="text-5xl">🎈</span>
          <p className="text-gray-500 mt-4">
            No hay cumpleaños en los próximos 7 días
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {cumpleanos.map((c) => (
            <button
              key={c.cliente_id}
              onClick={() => handleSelect(c)}
              className={`w-full text-left border rounded-lg p-4 flex items-center gap-4 transition-colors hover:bg-pink-50 ${
                c.cumple_hoy
                  ? 'border-pink-300 bg-pink-50'
                  : 'border-gray-200 bg-white'
              }`}
            >
              <div className="bg-pink-100 text-pink-700 rounded-full w-11 h-11 flex items-center justify-center flex-shrink-0 text-xl">
                🎁
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 truncate">
                  {c.nombre_completo}
                </p>
                <p className="text-sm text-gray-600">
                  {c.dia_mes} · Cumple {c.edad_a_cumplir} años
                  {c.telefono ? ` · ${c.telefono}` : ''}
                </p>
              </div>
              <div className="flex flex-col items-end flex-shrink-0">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    c.cumple_hoy
                      ? 'bg-pink-600 text-white'
                      : 'bg-pink-100 text-pink-700'
                  }`}
                >
                  {etiquetaDias(c)}
                </span>
                <span className="text-xs text-gray-500 mt-1">
                  Valor: ${c.lifetime_value.toLocaleString('es-AR')}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      <Modal isOpen={selected !== null} onClose={handleClose} size="xl">
        <ModalHeader>
          <h2 className="text-xl font-bold text-gray-900">
            {selected?.nombre_completo}
          </h2>
          <p className="text-sm text-gray-500">
            {selected
              ? `${selected.dia_mes} · Cumple ${selected.edad_a_cumplir} años`
              : ''}
          </p>
        </ModalHeader>
        <ModalBody>
          {errorSummary ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center text-red-700">
              {errorSummary}
            </div>
          ) : (
            <ClientSummaryCard data={summary} loading={loadingSummary} />
          )}
        </ModalBody>
      </Modal>
    </div>
  );
}

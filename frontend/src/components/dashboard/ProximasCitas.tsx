import { ProximaCita } from '../../hooks/useDashboard';
import { useNavigate } from 'react-router-dom';

interface ProximasCitasProps {
  citas: ProximaCita[];
}

export default function ProximasCitas({ citas }: ProximasCitasProps) {
  const navigate = useNavigate();

  const getEstadoStyles = (estado: string) => {
    switch (estado) {
      case 'CONFIRMADO':
        return 'bg-green-100 text-green-800';
      case 'PENDIENTE':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getEstadoLabel = (estado: string) => {
    switch (estado) {
      case 'CONFIRMADO':
        return 'Confirmado';
      case 'PENDIENTE':
        return 'Pendiente';
      default:
        return estado;
    }
  };

  if (citas.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Próximas Citas de Hoy</h3>
        <div className="text-center py-8">
          <span className="text-6xl">📅</span>
          <p className="text-gray-500 mt-4">No hay citas pendientes para hoy</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Próximas Citas de Hoy</h3>
        <button
          onClick={() => navigate('/turnos')}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          Ver todas →
        </button>
      </div>
      <div className="space-y-3">
        {citas.map((cita) => (
          <div
            key={cita.id}
            className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
            onClick={() => navigate('/turnos')}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <div className="bg-blue-100 text-blue-800 rounded-lg px-3 py-2 font-semibold text-sm">
                  {cita.hora}
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{cita.cliente}</p>
                  <p className="text-sm text-gray-600">{cita.servicio}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEstadoStyles(cita.estado)}`}>
                {getEstadoLabel(cita.estado)}
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>👨‍⚕️</span>
              <span>{cita.profesional}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

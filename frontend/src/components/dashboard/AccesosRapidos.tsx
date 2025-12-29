import { useNavigate } from 'react-router-dom';

export default function AccesosRapidos() {
  const navigate = useNavigate();

  const accesos = [
    {
      title: 'Nueva Cita',
      description: 'Agendar una nueva cita',
      icon: '📅',
      color: 'bg-blue-500',
      hoverColor: 'hover:bg-blue-600',
      onClick: () => navigate('/turnos')
    },
    {
      title: 'Nueva Venta',
      description: 'Registrar venta o servicio',
      icon: '💰',
      color: 'bg-green-500',
      hoverColor: 'hover:bg-green-600',
      onClick: () => navigate('/mi-caja')
    },
    {
      title: 'Ver Calendario',
      description: 'Ver todas las citas',
      icon: '📆',
      color: 'bg-purple-500',
      hoverColor: 'hover:bg-purple-600',
      onClick: () => navigate('/turnos')
    },
    {
      title: 'Mi Caja',
      description: 'Ver cierre del día',
      icon: '💵',
      color: 'bg-orange-500',
      hoverColor: 'hover:bg-orange-600',
      onClick: () => navigate('/mi-caja')
    },
    {
      title: 'Clientes',
      description: 'Gestionar clientes',
      icon: '👥',
      color: 'bg-pink-500',
      hoverColor: 'hover:bg-pink-600',
      onClick: () => navigate('/clientes')
    },
    {
      title: 'Inventario',
      description: 'Ver productos y stock',
      icon: '📦',
      color: 'bg-indigo-500',
      hoverColor: 'hover:bg-indigo-600',
      onClick: () => navigate('/inventario')
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Accesos Rápidos</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {accesos.map((acceso, index) => (
          <button
            key={index}
            onClick={acceso.onClick}
            className={`${acceso.color} ${acceso.hoverColor} text-white rounded-lg p-4 transition-colors flex flex-col items-center justify-center gap-2 min-h-[120px]`}
          >
            <span className="text-4xl">{acceso.icon}</span>
            <div className="text-center">
              <p className="font-semibold text-sm">{acceso.title}</p>
              <p className="text-xs opacity-90 mt-1">{acceso.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

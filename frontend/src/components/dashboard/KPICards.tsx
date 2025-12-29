import { DashboardHomeData, DashboardStats } from '../../hooks/useDashboard';

interface KPICardsProps {
  dashboardData: DashboardHomeData | null;
  stats: DashboardStats | null;
}

export default function KPICards({ dashboardData, stats }: KPICardsProps) {
  if (!dashboardData || !stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  const canViewFinancials = dashboardData.can_view_financials;

  // Tarjetas diferentes según rol
  const cards = canViewFinancials ? [
    // Admin/Manager: Tarjetas completas con datos financieros
    {
      title: 'Citas de Hoy',
      value: dashboardData.citas_hoy.total,
      subtitle: `${dashboardData.citas_hoy.completadas} completadas`,
      icon: '📅',
      color: 'blue'
    },
    {
      title: 'Ingresos de Hoy',
      value: `$${dashboardData.ingresos_hoy.neto.toLocaleString('es-AR', { minimumFractionDigits: 2 })}`,
      subtitle: `Ingresos: $${dashboardData.ingresos_hoy.ingresos.toLocaleString('es-AR')}`,
      icon: '💰',
      color: 'green'
    },
    {
      title: 'Clientes Atendidos',
      value: dashboardData.clientes_atendidos_hoy,
      subtitle: `${stats.total_clientes} clientes totales`,
      icon: '👥',
      color: 'purple'
    },
    {
      title: 'Ocupación Hoy',
      value: `${stats.ocupacion_hoy}%`,
      subtitle: `${stats.servicios_mes} servicios este mes`,
      icon: '📊',
      color: 'orange'
    }
  ] : [
    // Empleado: Solo datos operativos, sin financieros
    {
      title: 'Mis Citas de Hoy',
      value: dashboardData.citas_hoy.total,
      subtitle: `${dashboardData.citas_hoy.completadas} completadas`,
      icon: '📅',
      color: 'blue'
    },
    {
      title: 'Citas Pendientes',
      value: dashboardData.citas_hoy.pendientes,
      subtitle: `${dashboardData.citas_hoy.confirmadas} confirmadas`,
      icon: '⏰',
      color: 'yellow'
    },
    {
      title: 'Clientes Atendidos',
      value: dashboardData.clientes_atendidos_hoy,
      subtitle: 'Clientes de hoy',
      icon: '👥',
      color: 'purple'
    },
    {
      title: 'Servicios del Mes',
      value: stats.servicios_mes,
      subtitle: 'Servicios realizados',
      icon: '✂️',
      color: 'green'
    }
  ];

  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
    yellow: 'bg-yellow-50 text-yellow-600'
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <div key={index} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-medium text-gray-600">{card.title}</p>
            <span className={`text-2xl ${colorClasses[card.color as keyof typeof colorClasses]} rounded-full w-12 h-12 flex items-center justify-center`}>
              {card.icon}
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mb-1">{card.value}</p>
          <p className="text-xs text-gray-500">{card.subtitle}</p>
        </div>
      ))}
    </div>
  );
}

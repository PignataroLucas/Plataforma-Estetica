import { useDashboard } from '../hooks/useDashboard';
import KPICards from '../components/dashboard/KPICards';
import AlertasPanel from '../components/dashboard/AlertasPanel';
import ProximasCitas from '../components/dashboard/ProximasCitas';
import AccesosRapidos from '../components/dashboard/AccesosRapidos';

export default function DashboardPage() {
  const { dashboardData, stats, loading, error, refetch } = useDashboard();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <span className="text-6xl">❌</span>
            <h2 className="text-xl font-semibold text-red-800 mt-4">Error al cargar el dashboard</h2>
            <p className="text-red-600 mt-2">{error}</p>
            <button
              onClick={refetch}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  const fecha = new Date(dashboardData?.fecha || new Date());
  const fechaFormateada = fecha.toLocaleDateString('es-AR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600 capitalize">{fechaFormateada}</p>
        </div>

        {/* KPI Cards */}
        <div className="mb-8">
          <KPICards dashboardData={dashboardData} stats={stats} />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Próximas Citas - 2 columnas */}
          <div className="lg:col-span-2">
            <ProximasCitas citas={dashboardData?.citas_hoy.proximas || []} />
          </div>

          {/* Alertas - 1 columna */}
          <div>
            <AlertasPanel alertas={dashboardData?.alertas || []} />
          </div>
        </div>

        {/* Accesos Rápidos */}
        <div className="mb-8">
          <AccesosRapidos />
        </div>

        {/* Resumen del Mes - Solo para Admin/Manager */}
        {dashboardData?.can_view_financials && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Resumen del Mes</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Ingresos del Mes</p>
                <p className="text-2xl font-bold text-green-600">
                  ${dashboardData?.ingresos_mes.ingresos.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Gastos del Mes</p>
                <p className="text-2xl font-bold text-red-600">
                  ${dashboardData?.ingresos_mes.gastos.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Ganancia Neta</p>
                <p className="text-2xl font-bold text-blue-600">
                  ${dashboardData?.ingresos_mes.neto.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface BehaviorMetricsProps {
  data: {
    no_show_rate: number;
    cancellation_rate: number;
    average_interval_days: number;
    punctuality_score: number;
    total_appointments: number;
    completed_appointments: number;
    no_show_count: number;
    cancelled_count: number;
  } | null;
  loading?: boolean;
}

export default function BehaviorMetrics({
  data,
  loading = false,
}: BehaviorMetricsProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-gray-100 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Métricas de Comportamiento
        </h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  // Función para determinar color del indicador
  const getSeverityColor = (rate: number, type: 'negative' | 'positive') => {
    if (type === 'negative') {
      // Para métricas negativas (no-show, cancelación)
      if (rate >= 20) return { bg: 'bg-red-50', text: 'text-red-600', bar: 'bg-red-500' };
      if (rate >= 10) return { bg: 'bg-yellow-50', text: 'text-yellow-600', bar: 'bg-yellow-500' };
      return { bg: 'bg-green-50', text: 'text-green-600', bar: 'bg-green-500' };
    } else {
      // Para métricas positivas (puntualidad)
      if (rate >= 80) return { bg: 'bg-green-50', text: 'text-green-600', bar: 'bg-green-500' };
      if (rate >= 60) return { bg: 'bg-yellow-50', text: 'text-yellow-600', bar: 'bg-yellow-500' };
      return { bg: 'bg-red-50', text: 'text-red-600', bar: 'bg-red-500' };
    }
  };

  const noShowColors = getSeverityColor(data.no_show_rate, 'negative');
  const cancellationColors = getSeverityColor(data.cancellation_rate, 'negative');
  const punctualityColors = getSeverityColor(data.punctuality_score, 'positive');

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6 text-gray-800">
        Métricas de Comportamiento
      </h3>

      {/* Grid de tarjetas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Tasa de No-Show */}
        <div className={`p-4 rounded-lg ${noShowColors.bg}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">⚠️</span>
            <span className={`text-sm font-medium ${noShowColors.text}`}>
              No-Show
            </span>
          </div>
          <div className="mb-3">
            <p className={`text-3xl font-bold ${noShowColors.text}`}>
              {data.no_show_rate}%
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {data.no_show_count} de {data.total_appointments} citas
            </p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`${noShowColors.bar} h-2 rounded-full transition-all`}
              style={{ width: `${Math.min(data.no_show_rate, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Tasa de Cancelación */}
        <div className={`p-4 rounded-lg ${cancellationColors.bg}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">🚫</span>
            <span className={`text-sm font-medium ${cancellationColors.text}`}>
              Cancelaciones
            </span>
          </div>
          <div className="mb-3">
            <p className={`text-3xl font-bold ${cancellationColors.text}`}>
              {data.cancellation_rate}%
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {data.cancelled_count} de {data.total_appointments} citas
            </p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`${cancellationColors.bar} h-2 rounded-full transition-all`}
              style={{ width: `${Math.min(data.cancellation_rate, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Puntualidad/Completitud */}
        <div className={`p-4 rounded-lg ${punctualityColors.bg}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">⏰</span>
            <span className={`text-sm font-medium ${punctualityColors.text}`}>
              Completitud
            </span>
          </div>
          <div className="mb-3">
            <p className={`text-3xl font-bold ${punctualityColors.text}`}>
              {data.punctuality_score}%
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {data.completed_appointments} completadas
            </p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`${punctualityColors.bar} h-2 rounded-full transition-all`}
              style={{ width: `${data.punctuality_score}%` }}
            ></div>
          </div>
        </div>

        {/* Tiempo entre Visitas */}
        <div className="p-4 rounded-lg bg-blue-50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">📅</span>
            <span className="text-sm font-medium text-blue-600">
              Frecuencia
            </span>
          </div>
          <div className="mb-3">
            <p className="text-3xl font-bold text-blue-600">
              {data.average_interval_days}
            </p>
            <p className="text-xs text-gray-600 mt-1">
              días entre visitas
            </p>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            {data.average_interval_days === 0
              ? 'Cliente nuevo'
              : data.average_interval_days <= 15
              ? 'Muy frecuente'
              : data.average_interval_days <= 30
              ? 'Frecuente'
              : data.average_interval_days <= 60
              ? 'Ocasional'
              : 'Poco frecuente'}
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">
          Análisis de Comportamiento
        </h4>
        <ul className="text-sm text-gray-600 space-y-1">
          {/* Análisis de no-show */}
          {data.no_show_rate === 0 ? (
            <li>
              ✅ <strong>Excelente:</strong> El cliente nunca falta a sus citas
            </li>
          ) : data.no_show_rate < 10 ? (
            <li>
              ✅ <strong>Bueno:</strong> Tasa de ausencias baja ({data.no_show_rate}%)
            </li>
          ) : data.no_show_rate < 20 ? (
            <li>
              ⚠️ <strong>Atención:</strong> Tasa de ausencias moderada ({data.no_show_rate}%) - considerar recordatorios
            </li>
          ) : (
            <li>
              🚨 <strong>Crítico:</strong> Tasa de ausencias alta ({data.no_show_rate}%) - requiere seguimiento
            </li>
          )}

          {/* Análisis de cancelaciones */}
          {data.cancellation_rate === 0 ? (
            <li>
              ✅ El cliente nunca ha cancelado una cita
            </li>
          ) : data.cancellation_rate < 10 ? (
            <li>
              ✅ Tasa de cancelación aceptable ({data.cancellation_rate}%)
            </li>
          ) : data.cancellation_rate >= 20 ? (
            <li>
              ⚠️ Alta tasa de cancelación ({data.cancellation_rate}%) - investigar motivos
            </li>
          ) : null}

          {/* Análisis de completitud */}
          {data.punctuality_score >= 80 ? (
            <li>
              🏆 <strong>Cliente confiable:</strong> {data.punctuality_score}% de completitud
            </li>
          ) : data.punctuality_score >= 60 ? (
            <li>
              ⚠️ Completitud moderada ({data.punctuality_score}%)
            </li>
          ) : (
            <li>
              🚨 Baja completitud ({data.punctuality_score}%) - requiere atención especial
            </li>
          )}

          {/* Análisis de frecuencia */}
          {data.average_interval_days > 0 && data.average_interval_days <= 20 && (
            <li>
              🔄 Cliente muy activo - visita cada {data.average_interval_days} días aproximadamente
            </li>
          )}
          {data.average_interval_days > 60 && (
            <li>
              📆 Visitas espaciadas - podría beneficiarse de programas de fidelización
            </li>
          )}

          {/* Estadística general */}
          <li>
            • Total de citas registradas: <strong>{data.total_appointments}</strong> ({data.completed_appointments} completadas)
          </li>
        </ul>
      </div>

      {/* Indicadores de calidad */}
      <div className="mt-6 flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
        <div>
          <p className="text-sm font-semibold text-gray-900">
            Índice de Confiabilidad del Cliente
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Basado en completitud y puntualidad
          </p>
        </div>
        <div className="text-right">
          <p className={`text-3xl font-bold ${punctualityColors.text}`}>
            {data.punctuality_score >= 80
              ? 'A'
              : data.punctuality_score >= 60
              ? 'B'
              : data.punctuality_score >= 40
              ? 'C'
              : 'D'}
          </p>
          <p className="text-xs text-gray-600">Calificación</p>
        </div>
      </div>
    </div>
  );
}

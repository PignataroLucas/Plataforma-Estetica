import {
  RadialBarChart,
  RadialBar,
  Legend,
  ResponsiveContainer,
  PolarAngleAxis,
} from 'recharts';

interface LoyaltyScoreGaugeProps {
  data: {
    loyalty_score: number;
    score_breakdown: {
      frequency_score: number;
      frequency_max: number;
      recency_score: number;
      recency_max: number;
      monetary_score: number;
      monetary_max: number;
      consistency_score: number;
      consistency_max: number;
      engagement_score: number;
      engagement_max: number;
    };
    interpretation: string;
    level: string;
    metrics: {
      total_visits: number;
      lifetime_value: number;
      days_since_last_visit: number;
      unique_services: number;
      first_visit: string;
      last_visit: string;
      customer_lifetime_days: number;
    };
  } | null;
  loading?: boolean;
}

export default function LoyaltyScoreGauge({
  data,
  loading = false,
}: LoyaltyScoreGaugeProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="h-64 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Score de Fidelización
        </h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No hay datos disponibles</p>
        </div>
      </div>
    );
  }

  const { loyalty_score, score_breakdown, interpretation, level, metrics } = data;

  // Determinar color basado en el score
  const getScoreColor = (score: number) => {
    if (score >= 85) return '#10b981'; // Verde - Excelente
    if (score >= 70) return '#3b82f6'; // Azul - Muy Bueno
    if (score >= 55) return '#8b5cf6'; // Púrpura - Bueno
    if (score >= 40) return '#f59e0b'; // Ámbar - Regular
    if (score >= 25) return '#ef4444'; // Rojo - Bajo
    return '#6b7280'; // Gris - Muy Bajo
  };

  const scoreColor = getScoreColor(loyalty_score);

  // Datos para el radial bar chart
  const chartData = [
    {
      name: 'Score',
      value: loyalty_score,
      fill: scoreColor,
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6 text-gray-800">
        Score de Fidelización
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gauge circular */}
        <div className="flex flex-col items-center justify-center">
          <ResponsiveContainer width="100%" height={300}>
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="90%"
              barSize={40}
              data={chartData}
              startAngle={180}
              endAngle={0}
            >
              <PolarAngleAxis
                type="number"
                domain={[0, 100]}
                angleAxisId={0}
                tick={false}
              />
              <RadialBar
                background
                dataKey="value"
                cornerRadius={10}
                fill={scoreColor}
              />
            </RadialBarChart>
          </ResponsiveContainer>

          <div className="text-center mt-[-80px]">
            <p className="text-6xl font-bold" style={{ color: scoreColor }}>
              {loyalty_score}
            </p>
            <p className="text-sm text-gray-500 mt-1">de 100</p>
            <p
              className="text-xl font-semibold mt-2"
              style={{ color: scoreColor }}
            >
              {interpretation}
            </p>
            <p className="text-sm text-gray-600">{level}</p>
          </div>
        </div>

        {/* Score breakdown */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            Desglose del Score
          </h4>

          {/* Frecuencia */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-gray-600">
                Frecuencia de Visitas
              </span>
              <span className="text-xs font-semibold text-gray-700">
                {score_breakdown.frequency_score}/{score_breakdown.frequency_max}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{
                  width: `${
                    (score_breakdown.frequency_score /
                      score_breakdown.frequency_max) *
                    100
                  }%`,
                }}
              ></div>
            </div>
          </div>

          {/* Recencia */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-gray-600">
                Recencia (Última Visita)
              </span>
              <span className="text-xs font-semibold text-gray-700">
                {score_breakdown.recency_score}/{score_breakdown.recency_max}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{
                  width: `${
                    (score_breakdown.recency_score /
                      score_breakdown.recency_max) *
                    100
                  }%`,
                }}
              ></div>
            </div>
          </div>

          {/* Valor Monetario */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-gray-600">Valor Monetario (LTV)</span>
              <span className="text-xs font-semibold text-gray-700">
                {score_breakdown.monetary_score}/{score_breakdown.monetary_max}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-purple-600 h-2 rounded-full"
                style={{
                  width: `${
                    (score_breakdown.monetary_score /
                      score_breakdown.monetary_max) *
                    100
                  }%`,
                }}
              ></div>
            </div>
          </div>

          {/* Consistencia */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-gray-600">
                Consistencia de Visitas
              </span>
              <span className="text-xs font-semibold text-gray-700">
                {score_breakdown.consistency_score}/
                {score_breakdown.consistency_max}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-amber-600 h-2 rounded-full"
                style={{
                  width: `${
                    (score_breakdown.consistency_score /
                      score_breakdown.consistency_max) *
                    100
                  }%`,
                }}
              ></div>
            </div>
          </div>

          {/* Engagement */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-gray-600">
                Engagement (Variedad)
              </span>
              <span className="text-xs font-semibold text-gray-700">
                {score_breakdown.engagement_score}/
                {score_breakdown.engagement_max}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-pink-600 h-2 rounded-full"
                style={{
                  width: `${
                    (score_breakdown.engagement_score /
                      score_breakdown.engagement_max) *
                    100
                  }%`,
                }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Métricas adicionales */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-4">
          Métricas del Cliente
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-blue-600 mb-1">Total Visitas</p>
            <p className="text-xl font-bold text-gray-900">
              {metrics.total_visits}
            </p>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <p className="text-xs text-green-600 mb-1">Lifetime Value</p>
            <p className="text-xl font-bold text-gray-900">
              ${metrics.lifetime_value.toLocaleString('es-AR', {
                maximumFractionDigits: 0,
              })}
            </p>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg">
            <p className="text-xs text-purple-600 mb-1">Servicios Únicos</p>
            <p className="text-xl font-bold text-gray-900">
              {metrics.unique_services}
            </p>
          </div>
          <div className="p-3 bg-amber-50 rounded-lg">
            <p className="text-xs text-amber-600 mb-1">Días desde Última Visita</p>
            <p className="text-xl font-bold text-gray-900">
              {metrics.days_since_last_visit}
            </p>
          </div>
        </div>
      </div>

      {/* Información adicional */}
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Primera visita:</span>
            <span className="ml-2 font-medium text-gray-900">
              {new Date(metrics.first_visit).toLocaleDateString('es-AR')}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Última visita:</span>
            <span className="ml-2 font-medium text-gray-900">
              {new Date(metrics.last_visit).toLocaleDateString('es-AR')}
            </span>
          </div>
          <div className="col-span-2">
            <span className="text-gray-600">Cliente activo por:</span>
            <span className="ml-2 font-medium text-gray-900">
              {metrics.customer_lifetime_days} días (
              {(metrics.customer_lifetime_days / 365).toFixed(1)} años)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

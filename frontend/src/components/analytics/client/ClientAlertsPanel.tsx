
interface Alert {
  type: 'risk' | 'opportunity' | 'insight';
  severity?: 'high' | 'medium' | 'low';
  icon: string;
  title: string;
  message: string;
  action?: string;
}

interface Insight {
  icon: string;
  message: string;
}

interface Recommendation {
  icon: string;
  message: string;
  action?: string;
}

interface ClientAlertsPanelProps {
  alerts: Alert[];
  insights: Insight[];
  recommendations: Recommendation[];
  loading?: boolean;
}

export default function ClientAlertsPanel({
  alerts,
  insights,
  recommendations,
  loading = false,
}: ClientAlertsPanelProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-16 bg-gray-100 rounded"></div>
          <div className="h-16 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  const getAlertBgColor = (type: string, severity?: string) => {
    if (type === 'risk') {
      return severity === 'high'
        ? 'bg-red-50 border-red-200'
        : 'bg-orange-50 border-orange-200';
    }
    if (type === 'opportunity') {
      return 'bg-green-50 border-green-200';
    }
    return 'bg-blue-50 border-blue-200';
  };

  const getAlertTextColor = (type: string) => {
    if (type === 'risk') return 'text-red-800';
    if (type === 'opportunity') return 'text-green-800';
    return 'text-blue-800';
  };

  const hasContent =
    alerts.length > 0 || insights.length > 0 || recommendations.length > 0;

  if (!hasContent) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          Alertas e Insights
        </h3>
        <p className="text-gray-500 text-center py-8">
          No hay alertas en este momento
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Alertas e Insights
      </h3>

      <div className="space-y-4">
        {/* Alertas */}
        {alerts.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">
              🚨 Alertas
            </h4>
            <div className="space-y-2">
              {alerts.map((alert, index) => (
                <div
                  key={index}
                  className={`border rounded-lg p-4 ${getAlertBgColor(
                    alert.type,
                    alert.severity
                  )}`}
                >
                  <div className="flex items-start">
                    <span className="text-2xl mr-3">{alert.icon}</span>
                    <div className="flex-1">
                      <p
                        className={`font-semibold ${getAlertTextColor(
                          alert.type
                        )}`}
                      >
                        {alert.title}
                      </p>
                      <p className="text-sm text-gray-700 mt-1">
                        {alert.message}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Insights */}
        {insights.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">
              💡 Insights
            </h4>
            <div className="space-y-2">
              {insights.map((insight, index) => (
                <div
                  key={index}
                  className="bg-blue-50 border border-blue-200 rounded-lg p-3"
                >
                  <div className="flex items-center">
                    <span className="text-xl mr-2">{insight.icon}</span>
                    <p className="text-sm text-blue-800">{insight.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">
              ✅ Recomendaciones
            </h4>
            <div className="space-y-2">
              {recommendations.map((rec, index) => (
                <div
                  key={index}
                  className="bg-purple-50 border border-purple-200 rounded-lg p-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center flex-1">
                      <span className="text-xl mr-2">{rec.icon}</span>
                      <p className="text-sm text-purple-800">{rec.message}</p>
                    </div>
                    {rec.action && (
                      <button className="ml-4 px-3 py-1 bg-purple-600 text-white text-xs rounded-md hover:bg-purple-700">
                        Ejecutar
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

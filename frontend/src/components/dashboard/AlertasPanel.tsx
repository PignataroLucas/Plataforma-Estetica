import { Alerta } from '../../hooks/useDashboard';

interface AlertasPanelProps {
  alertas: Alerta[];
}

export default function AlertasPanel({ alertas }: AlertasPanelProps) {
  if (alertas.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Alertas</h3>
        <div className="text-center py-8">
          <span className="text-6xl">✅</span>
          <p className="text-gray-500 mt-4">No hay alertas pendientes</p>
        </div>
      </div>
    );
  }

  const getSeverityStyles = (severidad: string) => {
    switch (severidad) {
      case 'error':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: 'text-red-600',
          iconBg: 'bg-red-100',
          text: 'text-red-800',
          emoji: '🚨'
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          icon: 'text-yellow-600',
          iconBg: 'bg-yellow-100',
          text: 'text-yellow-800',
          emoji: '⚠️'
        };
      case 'info':
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: 'text-blue-600',
          iconBg: 'bg-blue-100',
          text: 'text-blue-800',
          emoji: 'ℹ️'
        };
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Alertas ({alertas.length})
      </h3>
      <div className="space-y-3">
        {alertas.map((alerta, index) => {
          const styles = getSeverityStyles(alerta.severidad);
          return (
            <div
              key={index}
              className={`${styles.bg} ${styles.border} border rounded-lg p-4 flex items-start gap-3`}
            >
              <div className={`${styles.iconBg} rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0`}>
                <span className="text-xl">{styles.emoji}</span>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className={`font-semibold ${styles.text} mb-1`}>
                  {alerta.titulo}
                </h4>
                <p className="text-sm text-gray-700">{alerta.mensaje}</p>
              </div>
              {alerta.count > 0 && (
                <div className={`${styles.iconBg} ${styles.icon} px-3 py-1 rounded-full text-sm font-semibold`}>
                  {alerta.count}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

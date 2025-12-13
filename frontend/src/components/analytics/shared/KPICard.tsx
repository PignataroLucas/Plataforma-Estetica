import React from 'react';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
  format?: 'currency' | 'number' | 'percentage';
  loading?: boolean;
}

export default function KPICard({
  title,
  value,
  change,
  icon,
  format = 'number',
  loading = false,
}: KPICardProps) {
  const formatValue = (val: string | number) => {
    if (loading) return '...';

    const numVal = typeof val === 'string' ? parseFloat(val) : val;

    if (format === 'currency') {
      return `$${numVal.toLocaleString('es-AR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })}`;
    } else if (format === 'percentage') {
      return `${numVal.toFixed(1)}%`;
    }
    return numVal.toLocaleString('es-AR');
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return '↑';
    if (change < 0) return '↓';
    return '−';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="h-8 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <div className="text-gray-400 text-xl">{icon}</div>}
      </div>

      <div className="flex items-end justify-between">
        <p className="text-3xl font-bold text-gray-900">{formatValue(value)}</p>

        {change !== undefined && (
          <div
            className={`flex items-center text-sm font-medium ${getChangeColor(
              change
            )}`}
          >
            <span className="text-lg">{getChangeIcon(change)}</span>
            <span className="ml-1">{Math.abs(change).toFixed(1)}%</span>
          </div>
        )}
      </div>

      {change !== undefined && (
        <p className="text-xs text-gray-500 mt-2">vs período anterior</p>
      )}
    </div>
  );
}

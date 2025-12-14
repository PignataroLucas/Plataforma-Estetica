import React, { useState } from 'react';
import { format, subDays, subMonths, startOfMonth, endOfMonth } from 'date-fns';

interface DateRangeFilterProps {
  onChange: (range: { startDate: string; endDate: string; compare?: boolean }) => void;
}

type PresetRange = '7days' | '30days' | '3months' | '6months' | 'thisMonth' | 'lastMonth' | 'custom';

export default function DateRangeFilter({ onChange }: DateRangeFilterProps) {
  const today = new Date();
  const [preset, setPreset] = useState<PresetRange>('30days');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [compare, setCompare] = useState(false);

  const presets = [
    { value: '7days', label: 'Últimos 7 días' },
    { value: '30days', label: 'Últimos 30 días' },
    { value: '3months', label: 'Últimos 3 meses' },
    { value: '6months', label: 'Últimos 6 meses' },
    { value: 'thisMonth', label: 'Este mes' },
    { value: 'lastMonth', label: 'Mes pasado' },
    { value: 'custom', label: 'Personalizado' },
  ];

  const getDateRange = (presetValue: PresetRange) => {
    const end = today;
    let start: Date;

    switch (presetValue) {
      case '7days':
        start = subDays(end, 7);
        break;
      case '30days':
        start = subDays(end, 30);
        break;
      case '3months':
        start = subMonths(end, 3);
        break;
      case '6months':
        start = subMonths(end, 6);
        break;
      case 'thisMonth':
        start = startOfMonth(end);
        break;
      case 'lastMonth':
        const lastMonth = subMonths(end, 1);
        start = startOfMonth(lastMonth);
        return {
          startDate: format(start, 'yyyy-MM-dd'),
          endDate: format(endOfMonth(lastMonth), 'yyyy-MM-dd'),
          compare,
        };
      default:
        return null;
    }

    return {
      startDate: format(start, 'yyyy-MM-dd'),
      endDate: format(end, 'yyyy-MM-dd'),
      compare,
    };
  };

  const handlePresetChange = (value: PresetRange) => {
    setPreset(value);

    if (value !== 'custom') {
      const range = getDateRange(value);
      if (range) {
        onChange(range);
      }
    }
  };

  const handleCustomApply = () => {
    if (customStart && customEnd) {
      onChange({ startDate: customStart, endDate: customEnd, compare });
    }
  };

  const handleCompareChange = (checked: boolean) => {
    setCompare(checked);

    // Re-aplicar el rango actual con el nuevo valor de compare
    if (preset !== 'custom') {
      const range = getDateRange(preset);
      if (range) {
        onChange({ ...range, compare: checked });
      }
    } else if (customStart && customEnd) {
      onChange({ startDate: customStart, endDate: customEnd, compare: checked });
    }
  };

  // Aplicar preset inicial
  React.useEffect(() => {
    const range = getDateRange('30days');
    if (range) {
      onChange(range);
    }
  }, []);

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Botones de preset en formato horizontal */}
      <div className="flex flex-wrap gap-2">
        {presets.map((p) => (
          <button
            key={p.value}
            onClick={() => handlePresetChange(p.value as PresetRange)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              preset === p.value
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Inputs personalizados si está en modo custom */}
      {preset === 'custom' && (
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            placeholder="Desde"
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          <span className="text-gray-500">→</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            placeholder="Hasta"
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          <button
            onClick={handleCustomApply}
            className="bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Aplicar
          </button>
        </div>
      )}

      {/* Opción de comparación */}
      <div className="ml-auto">
        <label className="flex items-center gap-2 cursor-pointer bg-white px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50">
          <input
            type="checkbox"
            checked={compare}
            onChange={(e) => handleCompareChange(e.target.checked)}
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-700">Comparar períodos</span>
        </label>
      </div>
    </div>
  );
}

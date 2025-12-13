import React, { useState } from 'react';
import { format, subDays, subMonths, startOfMonth, endOfMonth } from 'date-fns';

interface DateRangeFilterProps {
  onChange: (range: { startDate: string; endDate: string }) => void;
}

type PresetRange = '7days' | '30days' | '3months' | '6months' | 'thisMonth' | 'lastMonth' | 'custom';

export default function DateRangeFilter({ onChange }: DateRangeFilterProps) {
  const today = new Date();
  const [preset, setPreset] = useState<PresetRange>('30days');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

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
        };
      default:
        return null;
    }

    return {
      startDate: format(start, 'yyyy-MM-dd'),
      endDate: format(end, 'yyyy-MM-dd'),
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
      onChange({ startDate: customStart, endDate: customEnd });
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
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Período</h3>

      <div className="space-y-2">
        {presets.map((p) => (
          <label key={p.value} className="flex items-center cursor-pointer">
            <input
              type="radio"
              name="dateRange"
              value={p.value}
              checked={preset === p.value}
              onChange={(e) => handlePresetChange(e.target.value as PresetRange)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">{p.label}</span>
          </label>
        ))}
      </div>

      {preset === 'custom' && (
        <div className="mt-4 space-y-2">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Desde</label>
            <input
              type="date"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Hasta</label>
            <input
              type="date"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <button
            onClick={handleCustomApply}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Aplicar
          </button>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { Calendar, Clock } from 'lucide-react';
import { TimeRange } from '../types';

interface TimeRangeSelectorProps {
  startDate: string;
  endDate: string;
  onChange: (start: string, end: string) => void;
}

const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({
  startDate,
  endDate,
  onChange,
}) => {
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  // Preset time ranges
  const presets: { label: string; days: number }[] = [
    { label: 'Last 1 Week', days: 7 },
    { label: 'Last 1 Month', days: 30 },
    { label: 'Last 3 Months', days: 90 },
    { label: 'Last 6 Months', days: 180 },
    { label: 'Last 1 Year', days: 365 },
    { label: 'Last 2 Years', days: 730 },
    { label: 'Last 3 Years', days: 1095 },
    { label: 'Last 5 Years', days: 1825 },
  ];

  const applyPreset = (days: number, label: string) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    
    const startStr = start.toISOString().split('T')[0];
    const endStr = end.toISOString().split('T')[0];
    
    onChange(startStr, endStr);
    setSelectedPreset(label);
  };

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value, endDate);
    setSelectedPreset(''); // Clear preset selection
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(startDate, e.target.value);
    setSelectedPreset(''); // Clear preset selection
  };

  // Check if current dates match a preset
  useEffect(() => {
    const end = new Date(endDate);
    const start = new Date(startDate);
    const diffDays = Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
    
    const matchingPreset = presets.find(p => Math.abs(p.days - diffDays) <= 2);
    if (matchingPreset) {
      setSelectedPreset(matchingPreset.label);
    } else {
      setSelectedPreset('');
    }
  }, [startDate, endDate]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
        <Clock className="w-5 h-5" />
        <h3 className="font-semibold">Time Range</h3>
      </div>

      {/* Preset buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {presets.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => applyPreset(preset.days, preset.label)}
            className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
              selectedPreset === preset.label
                ? 'bg-blue-500 text-white border-blue-500'
                : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Custom date inputs */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Start Date
          </label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="date"
              value={startDate}
              onChange={handleStartDateChange}
              max={endDate}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            End Date
          </label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="date"
              value={endDate}
              onChange={handleEndDateChange}
              min={startDate}
              max={new Date().toISOString().split('T')[0]}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Date range summary */}
      {startDate && endDate && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <span className="font-medium">Selected:</span> {startDate} to {endDate}
          {' '}
          ({Math.round((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24))} days)
        </div>
      )}
    </div>
  );
};

export default TimeRangeSelector;

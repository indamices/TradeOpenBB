import React, { useState, useEffect, useMemo } from 'react';
import {
  Settings, Play, Loader2, TrendingUp, Target, AlertCircle,
  CheckCircle, X, Plus, Trash2, BarChart3
} from 'lucide-react';
import { Strategy, ParameterOptimizationRequest, ParameterOptimizationResult } from '../types';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';
import TimeRangeSelector from './TimeRangeSelector';
import BacktestSymbolList from './BacktestSymbolList';

/**
 * Deep comparison function for objects
 * More efficient than JSON.stringify and handles key ordering correctly
 */
function deepEqual(obj1: Record<string, any>, obj2: Record<string, any>): boolean {
  const keys1 = Object.keys(obj1).sort();
  const keys2 = Object.keys(obj2).sort();

  if (keys1.length !== keys2.length) return false;

  for (let i = 0; i < keys1.length; i++) {
    const key = keys1[i];
    if (key !== keys2[i]) return false;
    if (obj1[key] !== obj2[key]) return false;
  }

  return true;
}

interface ParameterRange {
  name: string;
  values: number[];
}

interface ParameterOptimizationProps {
  strategyId?: number;
  onOptimizationComplete?: (result: ParameterOptimizationResult) => void;
}

const ParameterOptimization: React.FC<ParameterOptimizationProps> = ({
  strategyId: propStrategyId,
  onOptimizationComplete
}) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | null>(propStrategyId || null);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedPoolId, setSelectedPoolId] = useState<number | null>(null);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [manualSymbols, setManualSymbols] = useState<string>('AAPL');
  const [useManualSymbols, setUseManualSymbols] = useState<boolean>(true);
  const [initialCash, setInitialCash] = useState<number>(100000);
  const [parameterRanges, setParameterRanges] = useState<ParameterRange[]>([]);
  const [newParamName, setNewParamName] = useState<string>('');
  const [newParamValues, setNewParamValues] = useState<string>('');
  const [optimizationMetric, setOptimizationMetric] = useState<'sharpe_ratio' | 'total_return' | 'annualized_return' | 'sortino_ratio'>('sharpe_ratio');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ParameterOptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<{ current: number; total: number } | null>(null);

  useEffect(() => {
    loadStrategies();
    // Set default dates (last 1 year)
    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - 1);
    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
  }, []);

  const loadStrategies = async () => {
    try {
      const data = await tradingService.getStrategies();
      setStrategies(data);
      if (data.length > 0 && !selectedStrategyId) {
        setSelectedStrategyId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load strategies:', err);
    }
  };

  const addParameterRange = () => {
    if (!newParamName || !newParamValues) {
      setError('请填写参数名称和值');
      return;
    }

    const values = newParamValues.split(',').map(v => {
      const num = parseFloat(v.trim());
      if (isNaN(num)) {
        throw new Error(`无效的数值: ${v.trim()}`);
      }
      return num;
    });

    if (values.length === 0) {
      setError('至少需要一个参数值');
      return;
    }

    setParameterRanges([...parameterRanges, {
      name: newParamName.trim(),
      values: values.sort((a, b) => a - b)
    }]);
    setNewParamName('');
    setNewParamValues('');
    setError(null);
  };

  const removeParameterRange = (index: number) => {
    setParameterRanges(parameterRanges.filter((_, i) => i !== index));
  };

  const calculateTotalCombinations = () => {
    if (parameterRanges.length === 0) return 0;
    return parameterRanges.reduce((total, param) => total * param.values.length, 1);
  };

  const handleOptimize = async () => {
    if (!selectedStrategyId) {
      setError('请选择策略');
      return;
    }

    if (!startDate || !endDate) {
      setError('请选择日期范围');
      return;
    }

    if (parameterRanges.length === 0) {
      setError('请至少添加一个参数范围');
      return;
    }

    const symbolList = useManualSymbols
      ? manualSymbols.split(',').map(s => s.trim()).filter(s => s)
      : selectedSymbols;

    if (symbolList.length === 0) {
      setError('请选择或输入股票代码');
      return;
    }

    const totalCombinations = calculateTotalCombinations();
    if (totalCombinations > 1000) {
      if (!confirm(`将生成 ${totalCombinations} 种参数组合，可能需要较长时间。是否继续？`)) {
        return;
      }
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setProgress({ current: 0, total: totalCombinations });

    try {
      const request: ParameterOptimizationRequest = {
        strategy_id: selectedStrategyId,
        start_date: startDate,
        end_date: endDate,
        initial_cash: initialCash,
        symbols: symbolList,
        parameter_ranges: parameterRanges.reduce((acc, param) => {
          acc[param.name] = param.values;
          return acc;
        }, {} as { [key: string]: any[] }),
        optimization_metric: optimizationMetric
      };

      const optimizationResult = await tradingService.optimizeStrategyParameters(request);
      setResult(optimizationResult);
      if (onOptimizationComplete) {
        onOptimizationComplete(optimizationResult);
      }
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || '参数优化失败');
      console.error('Optimization error:', err);
    } finally {
      setLoading(false);
      setProgress(null);
    }
  };

  const selectedStrategy = strategies.find(s => s.id === selectedStrategyId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="text-emerald-400" size={24} />
          <h2 className="text-2xl font-bold text-slate-200">参数优化</h2>
        </div>
        <p className="text-slate-400">自动寻找策略参数的最优组合</p>
      </div>

      {/* Configuration Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-slate-200 mb-4">优化配置</h3>

        <div className="space-y-6">
          {/* Strategy Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              选择策略
            </label>
            <select
              value={selectedStrategyId || ''}
              onChange={(e) => setSelectedStrategyId(parseInt(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              disabled={loading}
            >
              <option value="">请选择策略</option>
              {strategies.map(strategy => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.name} {strategy.is_active && '(激活)'}
                </option>
              ))}
            </select>
          </div>

          {/* Date Range */}
          <TimeRangeSelector
            startDate={startDate}
            endDate={endDate}
            onStartDateChange={setStartDate}
            onEndDateChange={setEndDate}
            disabled={loading}
          />

          {/* Symbols */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              股票代码
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="checkbox"
                id="useManualSymbols"
                checked={useManualSymbols}
                onChange={(e) => setUseManualSymbols(e.target.checked)}
                className="mt-1"
                disabled={loading}
              />
              <label htmlFor="useManualSymbols" className="text-sm text-slate-400">
                手动输入（用逗号分隔）
              </label>
            </div>
            {useManualSymbols ? (
              <input
                type="text"
                value={manualSymbols}
                onChange={(e) => setManualSymbols(e.target.value)}
                placeholder="AAPL,GOOGL,MSFT"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                disabled={loading}
              />
            ) : (
              <BacktestSymbolList
                selectedPoolId={selectedPoolId}
                selectedSymbols={selectedSymbols}
                onPoolChange={setSelectedPoolId}
                onSymbolsChange={setSelectedSymbols}
                disabled={loading}
              />
            )}
          </div>

          {/* Initial Cash */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              初始资金
            </label>
            <input
              type="number"
              value={initialCash}
              onChange={(e) => setInitialCash(parseFloat(e.target.value) || 0)}
              min="1000"
              step="1000"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              disabled={loading}
            />
          </div>

          {/* Optimization Metric */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              优化指标
            </label>
            <select
              value={optimizationMetric}
              onChange={(e) => setOptimizationMetric(e.target.value as 'sharpe_ratio' | 'total_return' | 'annualized_return' | 'sortino_ratio')}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              disabled={loading}
            >
              <option value="sharpe_ratio">Sharpe Ratio (夏普比率)</option>
              <option value="total_return">总收益率</option>
              <option value="annualized_return">年化收益率</option>
              <option value="sortino_ratio">Sortino Ratio (索提诺比率)</option>
            </select>
          </div>

          {/* Parameter Ranges */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              参数范围
            </label>
            <div className="space-y-3">
              {parameterRanges.map((param, idx) => (
                <div key={`param-${param.name || idx}`} className="flex items-center gap-2 p-3 bg-slate-800 rounded-lg">
                  <div className="flex-1">
                    <span className="text-slate-300 font-medium">{param.name}:</span>
                    <span className="text-slate-400 ml-2">
                      [{param.values.join(', ')}] ({param.values.length} 个值)
                    </span>
                  </div>
                  <button
                    onClick={() => removeParameterRange(index)}
                    className="p-1 text-red-400 hover:text-red-300"
                    disabled={loading}
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              ))}

              <div className="flex gap-2 p-3 bg-slate-800 rounded-lg">
                <input
                  type="text"
                  value={newParamName}
                  onChange={(e) => setNewParamName(e.target.value)}
                  placeholder="参数名 (如: short_sma)"
                  className="flex-1 bg-slate-700 border border-slate-600 rounded px-3 py-1 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  disabled={loading}
                />
                <input
                  type="text"
                  value={newParamValues}
                  onChange={(e) => setNewParamValues(e.target.value)}
                  placeholder="参数值 (如: 10,20,30,40,50)"
                  className="flex-1 bg-slate-700 border border-slate-600 rounded px-3 py-1 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  disabled={loading}
                />
                <button
                  onClick={addParameterRange}
                  className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm flex items-center gap-1"
                  disabled={loading}
                >
                  <Plus size={16} />
                  添加
                </button>
              </div>
            </div>
            {parameterRanges.length > 0 && (
              <div className="mt-2 text-sm text-slate-400">
                总组合数: <span className="text-emerald-400 font-bold">{calculateTotalCombinations()}</span>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {/* Progress Display */}
          {loading && progress && (
            <div className="p-4 bg-slate-800 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="animate-spin text-emerald-400" size={18} />
                <span className="text-slate-300">
                  优化中... {progress.current} / {progress.total}
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-emerald-500 h-2 rounded-full transition-all"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Optimize Button */}
          <button
            onClick={handleOptimize}
            disabled={loading || !selectedStrategyId || parameterRanges.length === 0}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                <span>优化中...</span>
              </>
            ) : (
              <>
                <Play size={20} />
                <span>开始优化</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="text-emerald-400" size={24} />
            <h3 className="text-xl font-bold text-slate-200">优化结果</h3>
          </div>

          {/* Best Parameters */}
          <div className="mb-6 p-4 bg-emerald-900/20 border border-emerald-700 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Target className="text-emerald-400" size={20} />
              <span className="text-slate-300 font-semibold">最优参数组合</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
              {Object.entries(result.best_parameters).map(([key, value]) => (
                <div key={key} className="bg-slate-800 p-2 rounded">
                  <div className="text-xs text-slate-400">{key}</div>
                  <div className="text-lg font-bold text-emerald-400">{value}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-emerald-700/50">
              <div className="flex items-center gap-2">
                <TrendingUp className="text-emerald-400" size={18} />
                <span className="text-slate-300">
                  最优 {optimizationMetric.replace('_', ' ')}: 
                  <span className="text-emerald-400 font-bold ml-2">
                    {result.best_metric_value.toFixed(4)}
                  </span>
                </span>
              </div>
            </div>
          </div>

          {/* Results Table */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="text-slate-400" size={20} />
              <span className="text-slate-300 font-semibold">所有参数组合结果</span>
              <span className="text-slate-500 text-sm">
                (共 {result.total_combinations} 种组合)
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-2 px-3 text-slate-400">参数</th>
                    <th className="text-right py-2 px-3 text-slate-400">Sharpe Ratio</th>
                    <th className="text-right py-2 px-3 text-slate-400">总收益率</th>
                    <th className="text-right py-2 px-3 text-slate-400">年化收益率</th>
                    <th className="text-right py-2 px-3 text-slate-400">最大回撤</th>
                    <th className="text-right py-2 px-3 text-slate-400">胜率</th>
                  </tr>
                </thead>
                <tbody>
                  {result.results.slice(0, 20).map((item, idx) => {
                    const isBest = deepEqual(item.parameters, result.best_parameters);
                    return (
                      <tr
                        key={`result-${idx}`}
                        className={`border-b border-slate-800 ${isBest ? 'bg-emerald-900/20' : ''}`}
                      >
                        <td className="py-2 px-3 text-slate-300">
                          {Object.entries(item.parameters).map(([k, v]) => `${k}:${v}`).join(', ')}
                        </td>
                        <td className="text-right py-2 px-3 text-slate-300">
                          {item.metrics?.sharpe_ratio?.toFixed(4) || item.sharpe_ratio?.toFixed(4) || '-'}
                        </td>
                        <td className="text-right py-2 px-3 text-slate-300">
                          {item.metrics?.total_return?.toFixed(2) || item.total_return?.toFixed(2)}%
                        </td>
                        <td className="text-right py-2 px-3 text-slate-300">
                          {item.metrics?.annualized_return?.toFixed(2) || item.annualized_return?.toFixed(2)}%
                        </td>
                        <td className="text-right py-2 px-3 text-slate-300">
                          {item.metrics?.max_drawdown?.toFixed(2) || item.max_drawdown?.toFixed(2)}%
                        </td>
                        <td className="text-right py-2 px-3 text-slate-300">
                          {item.metrics?.win_rate !== undefined 
                            ? (item.metrics.win_rate * 100).toFixed(2)
                            : item.win_rate !== undefined 
                              ? (item.win_rate * 100).toFixed(2)
                              : '-'
                          }%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {(result.results || []).length > 20 && (
                <div className="text-center mt-2 text-slate-500 text-sm">
                  显示前20条，共{(result.results || []).length}条结果
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ParameterOptimization;

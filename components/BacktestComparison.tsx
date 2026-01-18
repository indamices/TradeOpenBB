import React, { useState, useEffect } from 'react';
import { 
  CheckSquare, Square, BarChart3, TrendingUp, TrendingDown, 
  Target, Activity, DollarSign, X, Loader2 
} from 'lucide-react';
import { BacktestResult } from '../types';
import { apiClient } from '../services/apiClient';

interface ComparisonItem {
  id: string;
  name: string;
  type: 'strategy' | 'benchmark' | 'index';
  selected: boolean;
  color: string;
}

interface BenchmarkStrategy {
  [key: string]: {
    name: string;
    description: string;
  };
}

interface BacktestComparisonProps {
  mainResult: BacktestResult;
  onCompare: (selectedItems: string[]) => Promise<void>;
  loading?: boolean;
}

const BacktestComparison: React.FC<BacktestComparisonProps> = ({
  mainResult,
  onCompare,
  loading = false
}) => {
  const [benchmarkStrategies, setBenchmarkStrategies] = useState<BenchmarkStrategy>({});
  const [comparisonItems, setComparisonItems] = useState<ComparisonItem[]>([
    { id: 'main', name: '当前策略', type: 'strategy', selected: true, color: '#3b82f6' },
    { id: 'NASDAQ', name: '纳斯达克指数', type: 'index', selected: false, color: '#10b981' },
    { id: 'SP500', name: '标普500指数', type: 'index', selected: false, color: '#8b5cf6' },
    { id: 'CSI300', name: '沪深300指数', type: 'index', selected: false, color: '#f59e0b' },
    { id: 'SMA_CROSS', name: 'SMA交叉策略', type: 'benchmark', selected: false, color: '#ef4444' },
    { id: 'MOMENTUM', name: '动量策略', type: 'benchmark', selected: false, color: '#06b6d4' },
    { id: 'MEAN_REVERSION', name: '均值回归策略', type: 'benchmark', selected: false, color: '#ec4899' },
    { id: 'BUY_AND_HOLD', name: '买入持有策略', type: 'benchmark', selected: false, color: '#84cc16' },
    { id: 'RSI', name: 'RSI策略', type: 'benchmark', selected: false, color: '#f97316' },
  ]);
  const [comparisonResults, setComparisonResults] = useState<{ [key: string]: BacktestResult }>({});
  const [showComparison, setShowComparison] = useState(false);

  useEffect(() => {
    loadBenchmarkStrategies();
  }, []);

  const loadBenchmarkStrategies = async () => {
    try {
      const strategies = await apiClient.get<BenchmarkStrategy>('/api/backtest/benchmark-strategies');
      setBenchmarkStrategies(strategies);
      
      // Update comparison items with loaded strategy names
      setComparisonItems(prev => prev.map(item => {
        if (strategies[item.id]) {
          return { ...item, name: strategies[item.id].name };
        }
        return item;
      }));
    } catch (error) {
      console.error('Failed to load benchmark strategies:', error);
    }
  };

  const handleToggleItem = (id: string) => {
    setComparisonItems(prev => prev.map(item => 
      item.id === id ? { ...item, selected: !item.selected } : item
    ));
  };

  const handleCompare = async () => {
    const selectedIds = comparisonItems
      .filter(item => item.selected && item.id !== 'main')
      .map(item => item.id);
    
    if (selectedIds.length === 0) {
      setShowComparison(false);
      setComparisonResults({});
      return;
    }

    setShowComparison(true);
    await onCompare(selectedIds);
  };

  const getComparisonData = () => {
    const data: { [key: string]: any } = {
      'main': mainResult
    };

    if (mainResult.strategy_comparisons) {
      Object.entries(mainResult.strategy_comparisons).forEach(([key, value]) => {
        if (key !== 'main' && value.result) {
          data[key] = value.result;
        }
      });
    }

    return data;
  };

  const comparisonData = getComparisonData();
  const selectedItems = comparisonItems.filter(item => item.selected);

  // Find best values for highlighting
  const findBestValue = (key: string, higherIsBetter: boolean = true) => {
    let bestId = 'main';
    let bestValue = comparisonData['main']?.[key] ?? 0;

    Object.entries(comparisonData).forEach(([id, result]) => {
      if (id === 'main') return;
      const value = result?.[key];
      if (value !== undefined && value !== null) {
        if (higherIsBetter && value > bestValue) {
          bestValue = value;
          bestId = id;
        } else if (!higherIsBetter && value < bestValue) {
          bestValue = value;
          bestId = id;
        }
      }
    });

    return bestId;
  };

  const bestTotalReturn = findBestValue('total_return', true);
  const bestAnnualized = findBestValue('annualized_return', true);
  const bestSharpe = findBestValue('sharpe_ratio', true);
  const bestDrawdown = findBestValue('max_drawdown', false); // Lower is better
  const bestWinRate = findBestValue('win_rate', true);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
          <BarChart3 size={20} className="text-blue-400" />
          性能对比
        </h3>
        {showComparison && (
          <button
            onClick={() => setShowComparison(false)}
            className="text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X size={20} />
          </button>
        )}
      </div>

      {!showComparison ? (
        <>
          {/* Comparison Item Selector */}
          <div className="space-y-3">
            <p className="text-sm text-slate-400 mb-3">选择对比项（至少选择一个）：</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-y-auto">
              {comparisonItems.map((item) => (
                <label
                  key={item.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    item.selected
                      ? 'bg-blue-500/10 border-blue-500/30'
                      : 'bg-slate-800/50 border-slate-700 hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-2 flex-1">
                    {item.selected ? (
                      <CheckSquare size={18} className="text-blue-400" />
                    ) : (
                      <Square size={18} className="text-slate-500" />
                    )}
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-200">{item.name}</div>
                      {item.type === 'benchmark' && benchmarkStrategies[item.id] && (
                        <div className="text-xs text-slate-500 mt-0.5">
                          {benchmarkStrategies[item.id].description}
                        </div>
                      )}
                    </div>
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                  </div>
                  <input
                    type="checkbox"
                    checked={item.selected}
                    onChange={() => handleToggleItem(item.id)}
                    className="hidden"
                  />
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={handleCompare}
            disabled={loading || selectedItems.length <= 1}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>对比中...</span>
              </>
            ) : (
              <>
                <BarChart3 size={18} />
                <span>开始对比</span>
              </>
            )}
          </button>
        </>
      ) : (
        <>
          {/* Comparison Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-800/50">
                  <th className="px-4 py-3 text-sm font-semibold text-slate-300 border-b border-slate-700 sticky left-0 bg-slate-800/50 z-10">
                    指标
                  </th>
                  {selectedItems.map((item) => (
                    <th
                      key={item.id}
                      className="px-4 py-3 text-sm font-semibold text-slate-300 border-b border-slate-700 text-center min-w-[120px]"
                    >
                      <div className="flex items-center justify-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: item.color }}
                        />
                        <span>{item.name}</span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {/* Total Return */}
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-sm text-slate-400 sticky left-0 bg-slate-900 z-10">
                    <div className="flex items-center gap-2">
                      <DollarSign size={16} className="text-blue-400" />
                      总收益率
                    </div>
                  </td>
                  {selectedItems.map((item) => {
                    const result = comparisonData[item.id];
                    const value = result?.total_return ?? 0;
                    const isBest = bestTotalReturn === item.id;
                    // total_return is decimal (0.108 = 10.8%), convert to percentage for display
                    const displayValue = value * 100;
                    return (
                      <td
                        key={item.id}
                        className={`px-4 py-3 text-sm text-center ${
                          isBest
                            ? 'bg-emerald-500/20 text-emerald-400 font-bold'
                            : displayValue >= 0
                            ? 'text-emerald-400'
                            : 'text-red-400'
                        }`}
                      >
                        {value !== null && value !== undefined
                          ? `${displayValue >= 0 ? '+' : ''}${displayValue.toFixed(2)}%${isBest ? ' ✓' : ''}`
                          : '-'}
                      </td>
                    );
                  })}
                </tr>

                {/* Annualized Return */}
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-sm text-slate-400 sticky left-0 bg-slate-900 z-10">
                    <div className="flex items-center gap-2">
                      <TrendingUp size={16} className="text-emerald-400" />
                      年化收益率
                    </div>
                  </td>
                  {selectedItems.map((item) => {
                    const result = comparisonData[item.id];
                    const value = result?.annualized_return;
                    const isBest = bestAnnualized === item.id;
                    // annualized_return is decimal (0.108 = 10.8%), convert to percentage for display
                    const displayValue = (value !== null && value !== undefined ? value : 0) * 100;
                    return (
                      <td
                        key={item.id}
                        className={`px-4 py-3 text-sm text-center ${
                          isBest
                            ? 'bg-emerald-500/20 text-emerald-400 font-bold'
                            : displayValue >= 0
                            ? 'text-emerald-400'
                            : 'text-red-400'
                        }`}
                      >
                        {value !== null && value !== undefined
                          ? `${displayValue >= 0 ? '+' : ''}${displayValue.toFixed(2)}%${isBest ? ' ✓' : ''}`
                          : '-'}
                      </td>
                    );
                  })}
                </tr>

                {/* Sharpe Ratio */}
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-sm text-slate-400 sticky left-0 bg-slate-900 z-10">
                    <div className="flex items-center gap-2">
                      <Target size={16} className="text-blue-400" />
                      夏普比率
                    </div>
                  </td>
                  {selectedItems.map((item) => {
                    const result = comparisonData[item.id];
                    const value = result?.sharpe_ratio;
                    const isBest = bestSharpe === item.id;
                    return (
                      <td
                        key={item.id}
                        className={`px-4 py-3 text-sm text-center ${
                          isBest
                            ? 'bg-emerald-500/20 text-emerald-400 font-bold'
                            : 'text-slate-200'
                        }`}
                      >
                        {value !== null && value !== undefined
                          ? `${value.toFixed(2)}${isBest ? ' ✓' : ''}`
                          : '-'}
                      </td>
                    );
                  })}
                </tr>

                {/* Max Drawdown */}
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-sm text-slate-400 sticky left-0 bg-slate-900 z-10">
                    <div className="flex items-center gap-2">
                      <TrendingDown size={16} className="text-red-400" />
                      最大回撤
                    </div>
                  </td>
                  {selectedItems.map((item) => {
                    const result = comparisonData[item.id];
                    const value = result?.max_drawdown;
                    const isBest = bestDrawdown === item.id;
                    return (
                      <td
                        key={item.id}
                        className={`px-4 py-3 text-sm text-center ${
                          isBest
                            ? 'bg-emerald-500/20 text-emerald-400 font-bold'
                            : 'text-red-400'
                        }`}
                      >
                        {value !== null && value !== undefined
                          ? `-${value.toFixed(2)}%${isBest ? ' ✓' : ''}`
                          : '-'}
                      </td>
                    );
                  })}
                </tr>

                {/* Win Rate */}
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-sm text-slate-400 sticky left-0 bg-slate-900 z-10">
                    <div className="flex items-center gap-2">
                      <Target size={16} className="text-emerald-400" />
                      胜率
                    </div>
                  </td>
                  {selectedItems.map((item) => {
                    const result = comparisonData[item.id];
                    const value = result?.win_rate;
                    const isBest = value !== undefined && value !== null && bestWinRate === item.id;
                    // win_rate is decimal (0.3333 = 33.33%), convert to percentage for display
                    const displayValue = value !== undefined && value !== null ? value * 100 : null;
                    return (
                      <td
                        key={item.id}
                        className={`px-4 py-3 text-sm text-center ${
                          isBest
                            ? 'bg-emerald-500/20 text-emerald-400 font-bold'
                            : displayValue !== null
                            ? 'text-emerald-400'
                            : 'text-slate-500'
                        }`}
                      >
                        {displayValue !== null
                          ? `${displayValue.toFixed(2)}%${isBest ? ' ✓' : ''}`
                          : '-'}
                      </td>
                    );
                  })}
                </tr>

                {/* Total Trades */}
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-sm text-slate-400 sticky left-0 bg-slate-900 z-10">
                    <div className="flex items-center gap-2">
                      <Activity size={16} className="text-yellow-400" />
                      总交易次数
                    </div>
                  </td>
                  {selectedItems.map((item) => {
                    const result = comparisonData[item.id];
                    const value = result?.total_trades;
                    return (
                      <td key={item.id} className="px-4 py-3 text-sm text-center text-slate-300">
                        {value !== null && value !== undefined ? value : '-'}
                      </td>
                    );
                  })}
                </tr>
              </tbody>
            </table>
          </div>

          {/* Outperformance (if main strategy) */}
          {comparisonData['main'] && (
            <div className="mt-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <h4 className="text-sm font-semibold text-slate-300 mb-2">超额收益（相对于基准）</h4>
              <div className="space-y-1">
                {selectedItems
                  .filter(item => item.id !== 'main')
                  .map((item) => {
                    const mainReturn = comparisonData['main']?.total_return ?? 0;
                    const itemReturn = comparisonData[item.id]?.total_return ?? 0;
                    // total_return is decimal, convert difference to percentage
                    const outperformance = (mainReturn - itemReturn) * 100;
                    return (
                      <div key={item.id} className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">vs {item.name}:</span>
                        <span
                          className={`font-medium ${
                            outperformance >= 0 ? 'text-emerald-400' : 'text-red-400'
                          }`}
                        >
                          {outperformance >= 0 ? '+' : ''}
                          {outperformance.toFixed(2)}%
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default BacktestComparison;

import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  Play, Loader2, TrendingUp, TrendingDown, AlertCircle, 
  BarChart3, Activity, Target, DollarSign, Sparkles 
} from 'lucide-react';
import { Strategy, BacktestRequest, BacktestResult } from '../types';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';
import StockPoolManager from './StockPoolManager';
import TimeRangeSelector from './TimeRangeSelector';
import BacktestSymbolList from './BacktestSymbolList';
import BacktestComparison from './BacktestComparison';
import AIAnalysis from './AIAnalysis';

const BacktestLab: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<number | null>(null);
  const [showActiveOnly, setShowActiveOnly] = useState<boolean>(true);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedPoolId, setSelectedPoolId] = useState<number | null>(null);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [manualSymbols, setManualSymbols] = useState<string>('AAPL,MSFT,GOOGL');
  const [useManualSymbols, setUseManualSymbols] = useState<boolean>(true);
  const [initialCash, setInitialCash] = useState<number>(100000);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAIAnalysis, setShowAIAnalysis] = useState(false);

  useEffect(() => {
    loadStrategies();
    // Set default dates (last 1 year)
    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - 1);
    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
    
    // Listen for strategy saved events to refresh the list
    const handleStrategySaved = () => {
      loadStrategies();
    };
    window.addEventListener('strategySaved', handleStrategySaved);
    
    return () => {
      window.removeEventListener('strategySaved', handleStrategySaved);
    };
  }, []);

  const loadStrategies = async () => {
    try {
      // Load strategies based on filter
      const data = showActiveOnly 
        ? await tradingService.getActiveStrategies()
        : await tradingService.getStrategies();
      setStrategies(data);
      if (data.length > 0 && !selectedStrategy) {
        setSelectedStrategy(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load strategies:', err);
    }
  };

  useEffect(() => {
    loadStrategies();
  }, [showActiveOnly]);

  const handleRunBacktest = async () => {
    if (!selectedStrategy) {
      setError('Please select a strategy');
      return;
    }

    if (!startDate || !endDate) {
      setError('Please select start and end dates');
      return;
    }

    // Get symbols from pool or manual input
    const symbolList = useManualSymbols 
      ? manualSymbols.split(',').map(s => s.trim()).filter(s => s)
      : selectedSymbols;
    
    if (symbolList.length === 0) {
      setError('Please select a stock pool or enter at least one symbol');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: BacktestRequest = {
        strategy_id: selectedStrategy,
        start_date: startDate,
        end_date: endDate,
        initial_cash: initialCash,
        symbols: symbolList,
      };

      const backtestResult = await tradingService.runBacktest(request);
      setResult(backtestResult);
      
      // If comparison items are selected, trigger comparison
      if (request.compare_items && request.compare_items.length > 0) {
        // Comparison will be included in the result
        setResult(backtestResult);
      }
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to run backtest');
      console.error('Backtest error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Format equity curve data for chart
  const equityCurveData = result?.equity_curve?.map(item => ({
    date: new Date(item.date).toLocaleDateString(),
    value: item.value,
  })) || [];

  // Format drawdown data for chart
  const drawdownData = result?.drawdown_series?.map(item => ({
    date: new Date(item.date).toLocaleDateString(),
    drawdown: (item.drawdown * 100).toFixed(2), // Convert to percentage
  })) || [];

  // Format trades data for timeline
  const tradesData = result?.trades || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-2xl font-bold text-slate-200 mb-4">回测实验室</h2>
        <p className="text-slate-400">选择策略和时间段，运行回测并查看详细结果</p>
      </div>

      {/* Configuration Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-slate-200 mb-4">回测配置</h3>
        
        <div className="space-y-6">
          {/* Strategy Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-400">
                选择策略
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showActiveOnly}
                  onChange={(e) => setShowActiveOnly(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded focus:ring-emerald-500"
                />
                <span className="text-xs text-slate-400">仅显示活跃策略</span>
              </label>
            </div>
            <select
              value={selectedStrategy || ''}
              onChange={(e) => setSelectedStrategy(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- 选择策略 --</option>
              {strategies.map((strategy) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.name} {strategy.is_active ? '✓ 活跃' : '(未激活)'}
                </option>
              ))}
            </select>
            {selectedStrategy && (
              <div className="mt-2 flex items-center gap-2">
                {strategies.find(s => s.id === selectedStrategy)?.is_active ? (
                  <span className="text-xs text-emerald-400 flex items-center gap-1">
                    <span className="w-2 h-2 bg-emerald-400 rounded-full"></span>
                    该策略已激活
                  </span>
                ) : (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    <span className="w-2 h-2 bg-slate-600 rounded-full"></span>
                    该策略未激活
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Stock Pool Selection */}
          <div className="border border-slate-700 rounded-lg p-4 bg-slate-800/50">
            <div className="flex items-center gap-4 mb-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={!useManualSymbols}
                  onChange={() => setUseManualSymbols(false)}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="text-sm font-medium text-slate-300">使用股票池</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={useManualSymbols}
                  onChange={() => setUseManualSymbols(true)}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="text-sm font-medium text-slate-300">手动输入</span>
              </label>
            </div>

            {useManualSymbols ? (
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">
                  交易标的 (逗号分隔)
                </label>
                <input
                  type="text"
                  value={manualSymbols}
                  onChange={(e) => setManualSymbols(e.target.value)}
                  placeholder="AAPL,MSFT,GOOGL"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {manualSymbols.split(',').filter(s => s.trim()).length > 0 && (
                  <div className="mt-2 text-sm text-slate-400">
                    已选择 {manualSymbols.split(',').filter(s => s.trim()).length} 个标的
                  </div>
                )}
                <div className="mt-4 border-t border-slate-700 pt-4">
                  <BacktestSymbolList
                    selectedListId={null}
                    onSelectList={(listId, symbols) => {
                      if (listId && symbols.length > 0) {
                        setManualSymbols(symbols.join(', '));
                        setUseManualSymbols(true);
                      }
                    }}
                    currentSymbols={manualSymbols.split(',').map(s => s.trim()).filter(s => s)}
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <StockPoolManager
                    selectedPoolId={selectedPoolId}
                    onSelectPool={(poolId, symbols) => {
                      setSelectedPoolId(poolId);
                      setSelectedSymbols(symbols);
                    }}
                    mode="selector"
                  />
                  {selectedSymbols.length > 0 && (
                    <div className="mt-2 text-sm text-slate-400">
                      已选择股票池: {selectedSymbols.length} 个标的
                    </div>
                  )}
                </div>
                <div className="border-t border-slate-700 pt-4">
                  <BacktestSymbolList
                    selectedListId={null}
                    onSelectList={(listId, symbols) => {
                      if (listId && symbols.length > 0) {
                        setSelectedSymbols(symbols);
                        setUseManualSymbols(false);
                      }
                    }}
                    currentSymbols={selectedSymbols}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Time Range Selection */}
          <div className="border border-slate-700 rounded-lg p-4 bg-slate-800/50">
            <TimeRangeSelector
              startDate={startDate}
              endDate={endDate}
              onChange={(start, end) => {
                setStartDate(start);
                setEndDate(end);
              }}
            />
          </div>

          {/* Initial Cash */}
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">
              初始资金
            </label>
            <input
              type="number"
              value={initialCash}
              onChange={(e) => setInitialCash(Number(e.target.value))}
              min="1000"
              step="1000"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Run Button */}
        <div className="mt-6">
          <button
            onClick={handleRunBacktest}
            disabled={loading || !selectedStrategy}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                <span>运行中...</span>
              </>
            ) : (
              <>
                <Play size={20} />
                <span>运行回测</span>
              </>
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 flex items-center gap-2 text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Result Tabs */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-4 border-b border-slate-800">
              <button
                onClick={() => setShowAIAnalysis(false)}
                className={`px-4 py-2 font-medium transition-colors ${
                  !showAIAnalysis
                    ? 'text-emerald-400 border-b-2 border-emerald-400'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                <BarChart3 size={18} className="inline mr-2" />
                回测结果
              </button>
              <button
                onClick={() => setShowAIAnalysis(true)}
                className={`px-4 py-2 font-medium transition-colors ${
                  showAIAnalysis
                    ? 'text-purple-400 border-b-2 border-purple-400'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                <Sparkles size={18} className="inline mr-2" />
                AI分析
              </button>
            </div>
          </div>

          {/* AI Analysis Tab */}
          {showAIAnalysis && (
            <AIAnalysis
              backtestResult={result}
              strategyId={selectedStrategy!}
              strategy={strategies.find(s => s.id === selectedStrategy) || undefined}
            />
          )}

          {/* Backtest Results Tab */}
          {!showAIAnalysis && (
            <>
          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <p className="text-slate-500 text-sm font-medium">总收益率</p>
                <DollarSign size={20} className="text-blue-400" />
              </div>
              <h3 className={`text-2xl font-bold ${result.total_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {(result.total_return * 100).toFixed(2)}%
              </h3>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <p className="text-slate-500 text-sm font-medium">年化收益率</p>
                <TrendingUp size={20} className="text-emerald-400" />
              </div>
              <h3 className={`text-2xl font-bold ${result.annualized_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {(result.annualized_return * 100).toFixed(2)}%
              </h3>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <p className="text-slate-500 text-sm font-medium">最大回撤</p>
                <TrendingDown size={20} className="text-red-400" />
              </div>
              <h3 className="text-2xl font-bold text-red-400">
                {(result.max_drawdown * 100).toFixed(2)}%
              </h3>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <p className="text-slate-500 text-sm font-medium">夏普比率</p>
                <Target size={20} className="text-blue-400" />
              </div>
              <h3 className="text-2xl font-bold text-slate-200">
                {result.sharpe_ratio.toFixed(2)}
              </h3>
            </div>

            {result.sortino_ratio && (
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-slate-500 text-sm font-medium">Sortino比率</p>
                  <BarChart3 size={20} className="text-purple-400" />
                </div>
                <h3 className="text-2xl font-bold text-slate-200">
                  {result.sortino_ratio.toFixed(2)}
                </h3>
              </div>
            )}

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <p className="text-slate-500 text-sm font-medium">总交易次数</p>
                <Activity size={20} className="text-yellow-400" />
              </div>
              <h3 className="text-2xl font-bold text-slate-200">
                {result.total_trades}
              </h3>
            </div>

            {result.win_rate !== undefined && (
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-slate-500 text-sm font-medium">胜率</p>
                  <Target size={20} className="text-emerald-400" />
                </div>
                <h3 className="text-2xl font-bold text-emerald-400">
                  {(result.win_rate * 100).toFixed(2)}%
                </h3>
              </div>
            )}
          </div>

          {/* Equity Curve Chart */}
          {equityCurveData.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-slate-200 mb-6">资产曲线</h3>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={equityCurveData}>
                    <defs>
                      <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis 
                      dataKey="date" 
                      stroke="#64748b" 
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis 
                      stroke="#64748b" 
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                      formatter={(value: number) => [`$${value.toLocaleString()}`, '资产价值']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#3b82f6" 
                      fillOpacity={1} 
                      fill="url(#colorEquity)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Drawdown Chart */}
          {drawdownData.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-slate-200 mb-6">回撤曲线</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={drawdownData}>
                    <defs>
                      <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis 
                      dataKey="date" 
                      stroke="#64748b" 
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis 
                      stroke="#64748b" 
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      tickFormatter={(val) => `${val}%`}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                      formatter={(value: string) => [`${value}%`, '回撤']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="drawdown" 
                      stroke="#ef4444" 
                      fillOpacity={1} 
                      fill="url(#colorDrawdown)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Per-Stock Performance */}
          {result.per_stock_performance && result.per_stock_performance.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-slate-200">个股盈亏分析</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-medium">
                    <tr>
                      <th className="px-6 py-3">标的</th>
                      <th className="px-6 py-3">总交易</th>
                      <th className="px-6 py-3">买入次数</th>
                      <th className="px-6 py-3">卖出次数</th>
                      <th className="px-6 py-3">买入数量</th>
                      <th className="px-6 py-3">卖出数量</th>
                      <th className="px-6 py-3">持仓</th>
                      <th className="px-6 py-3">平均买入价</th>
                      <th className="px-6 py-3">平均卖出价</th>
                      <th className="px-6 py-3">总佣金</th>
                      <th className="px-6 py-3">已实现盈亏</th>
                      <th className="px-6 py-3">收益率</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {result.per_stock_performance.map((stock, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-4 font-bold text-slate-200">{stock.symbol}</td>
                        <td className="px-6 py-4 text-slate-300">{stock.total_trades}</td>
                        <td className="px-6 py-4 text-slate-300">{stock.buy_trades_count}</td>
                        <td className="px-6 py-4 text-slate-300">{stock.sell_trades_count}</td>
                        <td className="px-6 py-4 text-slate-300">{stock.total_quantity_bought}</td>
                        <td className="px-6 py-4 text-slate-300">{stock.total_quantity_sold}</td>
                        <td className="px-6 py-4 text-slate-300">{stock.final_position}</td>
                        <td className="px-6 py-4 text-slate-300">
                          ${stock.avg_buy_price?.toFixed(2) || '0.00'}
                        </td>
                        <td className="px-6 py-4 text-slate-300">
                          ${stock.avg_sell_price?.toFixed(2) || '0.00'}
                        </td>
                        <td className="px-6 py-4 text-slate-400">
                          ${stock.total_commission.toFixed(2)}
                        </td>
                        <td className={`px-6 py-4 font-medium ${
                          stock.realized_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          ${stock.realized_pnl.toFixed(2)}
                        </td>
                        <td className={`px-6 py-4 font-medium ${
                          stock.return_percent >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          {stock.return_percent.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Strategy Comparison */}
          <BacktestComparison
            mainResult={result}
            onCompare={async (selectedItems: string[]) => {
              if (!selectedStrategy) return;
              
              setLoading(true);
              setError(null);
              try {
                const symbolList = useManualSymbols 
                  ? manualSymbols.split(',').map(s => s.trim()).filter(s => s)
                  : selectedSymbols;
                
                const request: BacktestRequest = {
                  strategy_id: selectedStrategy,
                  start_date: startDate,
                  end_date: endDate,
                  initial_cash: initialCash,
                  symbols: symbolList,
                  compare_items: selectedItems
                };
                
                const backtestResult = await tradingService.runBacktest(request);
                setResult(backtestResult);
              } catch (err) {
                const apiError = err as ApiError;
                setError(apiError.detail || '对比失败');
                console.error('Comparison error:', err);
              } finally {
                setLoading(false);
              }
            }}
            loading={loading}
          />

          {/* Trades Timeline */}
          {tradesData.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-slate-200">交易记录</h3>
              </div>
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-medium sticky top-0">
                    <tr>
                      <th className="px-6 py-3">日期</th>
                      <th className="px-6 py-3">标的</th>
                      <th className="px-6 py-3">方向</th>
                      <th className="px-6 py-3">价格</th>
                      <th className="px-6 py-3">数量</th>
                      <th className="px-6 py-3">佣金</th>
                      <th className="px-6 py-3">触发原因</th>
                      <th className="px-6 py-3">盈亏</th>
                      <th className="px-6 py-3">盈亏%</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {tradesData.map((trade, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-4 text-slate-300">
                          {new Date(trade.date).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 font-bold text-slate-200">{trade.symbol}</td>
                        <td className={`px-6 py-4 font-medium ${
                          trade.side === 'BUY' ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          {trade.side}
                        </td>
                        <td className="px-6 py-4 text-slate-300">${trade.price.toFixed(2)}</td>
                        <td className="px-6 py-4 text-slate-300">{trade.quantity}</td>
                        <td className="px-6 py-4 text-slate-400">
                          ${trade.commission?.toFixed(2) || '0.00'}
                        </td>
                        <td className="px-6 py-4 text-slate-400 text-sm max-w-xs truncate" title={trade.trigger_reason}>
                          {trade.trigger_reason || '-'}
                        </td>
                        <td className={`px-6 py-4 font-medium ${
                          trade.pnl !== null && trade.pnl !== undefined
                            ? (trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400')
                            : 'text-slate-400'
                        }`}>
                          {trade.pnl !== null && trade.pnl !== undefined
                            ? `$${trade.pnl.toFixed(2)}`
                            : '-'}
                        </td>
                        <td className={`px-6 py-4 font-medium ${
                          trade.pnl_percent !== null && trade.pnl_percent !== undefined
                            ? (trade.pnl_percent >= 0 ? 'text-emerald-400' : 'text-red-400')
                            : 'text-slate-400'
                        }`}>
                          {trade.pnl_percent !== null && trade.pnl_percent !== undefined
                            ? `${trade.pnl_percent.toFixed(2)}%`
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default BacktestLab;

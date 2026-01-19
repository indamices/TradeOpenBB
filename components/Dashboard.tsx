import React, { useEffect, useState } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  TrendingUp, TrendingDown, DollarSign, Activity, AlertCircle,
  BarChart3, Eye, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { Portfolio, Position, MarketQuote } from '../types';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';
import { safeSignedPercent, safeCurrency, safeSignedCurrency, safeToFixed, formatMetric, formatDate, formatQuantity } from '../utils/format';

interface TechnicalIndicator {
  date: string;
  [key: string]: string | number;
}

const Dashboard: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [marketQuotes, setMarketQuotes] = useState<MarketQuote[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('AAPL');
  const [indicators, setIndicators] = useState<TechnicalIndicator[]>([]);
  const [marketOverview, setMarketOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'overview' | 'multi-stock' | 'indicators'>('overview');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [selectedSymbol]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const portfolioId = 1;

      // Step 1: Fetch basic data first (portfolio and positions) - show immediately
      const [portfolioData, positionsData] = await Promise.all([
        tradingService.getPortfolio(portfolioId),
        tradingService.getPositions(portfolioId),
      ]);
      setPortfolio(portfolioData);
      setPositions(positionsData);
      
      // Step 2: Set loading to false after basic data is loaded (progressive loading)
      setLoading(false);

      // Step 3: Fetch market data in parallel (non-blocking, loads in background)
      const symbols = positionsData.length > 0 
        ? positionsData.map(p => p.symbol)
        : ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'];
      
      // Parallel execution of all market data requests
      Promise.all([
        // Market quotes
        symbols.length > 0
          ? tradingService.getMultipleQuotes(symbols.slice(0, 10))
              .then(quotes => setMarketQuotes(quotes))
              .catch(err => console.warn('Failed to fetch market quotes:', err))
          : Promise.resolve(),
        
        // Market overview
        tradingService.getMarketOverview()
          .then(overview => setMarketOverview(overview))
          .catch(err => console.warn('Failed to fetch market overview:', err)),
        
        // Technical indicators (only if symbol is selected)
        selectedSymbol
          ? tradingService.getTechnicalIndicators(
              selectedSymbol,
              ['SMA', 'RSI', 'MACD'],
              20
            )
              .then(indicatorData => setIndicators(indicatorData))
              .catch(err => console.warn('Failed to fetch indicators:', err))
          : Promise.resolve(),
      ]).catch(err => {
        console.error('Error loading market data:', err);
      });
      
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load data');
      console.error('Error loading dashboard data:', err);
      setLoading(false);
    }
  };

  if (loading && !portfolio) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <div className="text-slate-400 animate-pulse">加载数据中...</div>
      </div>
    );
  }

  if (error && !portfolio) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-slate-400">
        <AlertCircle size={48} className="mb-4 text-red-400" />
        <h2 className="text-xl font-bold text-slate-300 mb-2">数据加载失败</h2>
        <p className="text-slate-500">{error}</p>
      </div>
    );
  }

  if (!portfolio) return <div className="text-slate-400">无投资组合数据</div>;

  // Prepare chart data for portfolio value over time (simulated)
  const portfolioChartData = Array.from({ length: 30 }, (_, i) => {
    const baseValue = portfolio.total_value;
    const variation = (Math.sin(i / 5) * 0.05 + Math.random() * 0.02) * baseValue;
    return {
      date: `Day ${i + 1}`,
      value: baseValue + variation,
    };
  });

  // Prepare multi-stock comparison data
  const multiStockData = marketQuotes.map(quote => ({
    symbol: quote.symbol,
    price: quote.price,
    change: quote.change,
    changePercent: quote.change_percent,
    volume: quote.volume,
  }));

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-sm font-medium">总资产</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                ${portfolio.total_value.toLocaleString()}
              </h3>
            </div>
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
              <Activity size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <span className={`flex items-center ${portfolio.daily_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {portfolio.daily_pnl >= 0 ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
              {portfolio.daily_pnl_percent >= 0 ? '+' : ''}{(portfolio.daily_pnl_percent ?? 0).toFixed(2)}%
            </span>
            <span className="text-slate-600 ml-2">今日</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-sm font-medium">可用资金</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                ${portfolio.current_cash.toLocaleString()}
              </h3>
            </div>
            <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
              <DollarSign size={20} />
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-sm font-medium">今日盈亏</p>
              <h3 className={`text-2xl font-bold mt-1 ${portfolio.daily_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {portfolio.daily_pnl >= 0 ? '+' : ''}${portfolio.daily_pnl.toLocaleString()}
              </h3>
            </div>
            <div className={`p-2 rounded-lg ${portfolio.daily_pnl >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
              {portfolio.daily_pnl >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-4">{(portfolio.daily_pnl_percent ?? 0).toFixed(2)}%</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-sm font-medium">持仓数量</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {positions.length}
              </h3>
            </div>
            <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
              <BarChart3 size={20} />
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-4">市场报价: {marketQuotes.length}</p>
        </div>
      </div>

      {/* View Toggle */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveView('overview')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeView === 'overview'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <Eye size={16} className="inline mr-2" />
            市场概览
          </button>
          <button
            onClick={() => setActiveView('multi-stock')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeView === 'multi-stock'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <BarChart3 size={16} className="inline mr-2" />
            多股票对比
          </button>
          <button
            onClick={() => setActiveView('indicators')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeView === 'indicators'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <Activity size={16} className="inline mr-2" />
            技术指标
          </button>
        </div>
      </div>

      {/* Market Overview View */}
      {activeView === 'overview' && (
        <>
          {/* Portfolio Equity Curve */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-slate-200 mb-6">资产曲线</h3>
            <div className="h-80 w-full min-h-[320px]">
              <ResponsiveContainer width="100%" height="100%" minHeight={320}>
                <AreaChart data={portfolioChartData}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="date" hide />
                  <YAxis domain={['auto', 'auto']} stroke="#64748b" tickFormatter={(val) => `$${val/1000}k`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} 
                    formatter={(value: number) => [`$${value.toLocaleString()}`, '资产价值']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#10b981" 
                    fillOpacity={1} 
                    fill="url(#colorValue)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Market Overview Stats */}
          {marketOverview && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                <p className="text-slate-500 text-sm font-medium">市场总览</p>
                <h3 className="text-xl font-bold text-white mt-2">
                  {marketOverview.total_stocks?.toLocaleString() || 'N/A'}
                </h3>
                <p className="text-slate-600 text-sm mt-2">总股票数</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                <p className="text-slate-500 text-sm font-medium">上涨</p>
                <h3 className="text-xl font-bold text-emerald-400 mt-2">
                  {marketOverview.advances?.toLocaleString() || 'N/A'}
                </h3>
                <p className="text-slate-600 text-sm mt-2">下跌: {marketOverview.declines?.toLocaleString() || 'N/A'}</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                <p className="text-slate-500 text-sm font-medium">总成交量</p>
                <h3 className="text-xl font-bold text-white mt-2">
                  ${marketOverview.total_volume_usd ? (marketOverview.total_volume_usd / 1e12).toFixed(2) + 'T' : 'N/A'}
                </h3>
              </div>
            </div>
          )}
        </>
      )}

      {/* Multi-Stock Comparison View */}
      {activeView === 'multi-stock' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-6">多股票价格对比</h3>
          {marketQuotes.length > 0 ? (
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%" minHeight={320}>
                <BarChart data={multiStockData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="symbol" stroke="#64748b" tick={{ fill: '#94a3b8' }} />
                  <YAxis stroke="#64748b" tick={{ fill: '#94a3b8' }} tickFormatter={(val) => `$${val.toFixed(0)}`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, '价格']}
                  />
                  <Bar dataKey="price" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center text-slate-500 py-12">暂无市场数据</div>
          )}
        </div>
      )}

      {/* Technical Indicators View */}
      {activeView === 'indicators' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-slate-200">技术指标分析</h3>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {marketQuotes.map(quote => (
                <option key={quote.symbol} value={quote.symbol}>{quote.symbol}</option>
              ))}
              {marketQuotes.length === 0 && <option value="AAPL">AAPL</option>}
            </select>
          </div>
          {indicators.length > 0 ? (
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%" minHeight={320}>
                <LineChart data={indicators.slice(-30)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#64748b" 
                    tick={{ fill: '#94a3b8', fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis stroke="#64748b" tick={{ fill: '#94a3b8' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                  />
                  <Legend />
                  {indicators[0] && Object.keys(indicators[0]).filter(k => k !== 'date').map((key, idx) => (
                    <Line 
                      key={key}
                      type="monotone" 
                      dataKey={key} 
                      stroke={['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][idx % 4]}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center text-slate-500 py-12">加载技术指标中...</div>
          )}
        </div>
      )}

      {/* Current Holdings */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800">
          <h3 className="text-lg font-semibold text-slate-200">当前持仓</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-medium">
              <tr>
                <th className="px-6 py-3">标的</th>
                <th className="px-6 py-3">数量</th>
                <th className="px-6 py-3">均价</th>
                <th className="px-6 py-3">现价</th>
                <th className="px-6 py-3">市值</th>
                <th className="px-6 py-3">浮动盈亏</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {positions.map((pos) => (
                <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-bold text-slate-200">{pos.symbol}</td>
                  <td className="px-6 py-4 text-slate-300">{pos.quantity}</td>
                  <td className="px-6 py-4 text-slate-400">{safeCurrency(pos.avg_price)}</td>
                  <td className="px-6 py-4 text-slate-300">{safeCurrency(pos.current_price)}</td>
                  <td className="px-6 py-4 text-slate-200">{safeCurrency(pos.market_value)}</td>
                  <td className={`px-6 py-4 font-medium ${pos.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {safeSignedCurrency(pos.unrealized_pnl)} ({safeSignedPercent(pos.unrealized_pnl_percent)})
                  </td>
                </tr>
              ))}
              {positions.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-500">暂无持仓</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Market Quotes Table */}
      {marketQuotes.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800">
            <h3 className="text-lg font-semibold text-slate-200">实时市场报价</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-medium">
                <tr>
                  <th className="px-6 py-3">标的</th>
                  <th className="px-6 py-3">价格</th>
                  <th className="px-6 py-3">涨跌</th>
                  <th className="px-6 py-3">涨跌幅</th>
                  <th className="px-6 py-3">成交量</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {marketQuotes.map((quote) => (
                  <tr key={quote.symbol} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-bold text-slate-200">{quote.symbol}</td>
                    <td className="px-6 py-4 text-slate-300">{safeCurrency(quote.price)}</td>
                    <td className={`px-6 py-4 font-medium ${quote.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {formatMetric(quote.change, '', 2)}
                    </td>
                    <td className={`px-6 py-4 font-medium ${quote.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {safeSignedPercent(quote.change_percent)}
                    </td>
                    <td className="px-6 py-4 text-slate-400">{formatQuantity(quote.volume, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

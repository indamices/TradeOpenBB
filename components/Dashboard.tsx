import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Activity, AlertCircle } from 'lucide-react';
import { Portfolio, Position } from '../types';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';

// Mock chart data (will be replaced with real data later)
const chartData = Array.from({ length: 30 }, (_, i) => ({
  name: `Day ${i + 1}`,
  value: 100000 + Math.random() * 5000 * (i * 0.1) - 2000
}));

const Dashboard: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const portfolioId = 1;  // Explicit portfolio ID
        const [portfolioData, positionsData] = await Promise.all([
          tradingService.getPortfolio(portfolioId),  // Explicitly pass ID
          tradingService.getPositions(portfolioId)  // Explicitly pass ID
        ]);
        setPortfolio(portfolioData);
        setPositions(positionsData);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to load data');
        console.error('Error loading dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="text-slate-400 animate-pulse">Loading Asset Data...</div>;
  
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-slate-400">
        <AlertCircle size={48} className="mb-4 text-red-400" />
        <h2 className="text-xl font-bold text-slate-300 mb-2">Error Loading Data</h2>
        <p className="text-slate-500">{error}</p>
      </div>
    );
  }

  if (!portfolio) return <div className="text-slate-400">No portfolio data available.</div>;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-sm font-medium">Total Equity</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                ${portfolio.total_value.toLocaleString()}
              </h3>
            </div>
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
              <Activity size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <span className="text-emerald-400 flex items-center">
              <TrendingUp size={14} className="mr-1" />
              +12.5%
            </span>
            <span className="text-slate-600 ml-2">All time</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-sm font-medium">Buying Power</p>
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
              <p className="text-slate-500 text-sm font-medium">Daily P&L</p>
              <h3 className={`text-2xl font-bold mt-1 ${portfolio.daily_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {portfolio.daily_pnl >= 0 ? '+' : ''}{portfolio.daily_pnl.toLocaleString()}
              </h3>
            </div>
            <div className={`p-2 rounded-lg ${portfolio.daily_pnl >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
              {portfolio.daily_pnl >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-4">{portfolio.daily_pnl_percent}% today</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-500 text-sm font-medium">Open Positions</p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {positions.length}
              </h3>
            </div>
          </div>
           <p className="text-slate-600 text-sm mt-4">Active strategies: 2</p>
        </div>
      </div>

      {/* Main Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-slate-200 mb-6">Equity Curve (Simulated)</h3>
        <div className="h-80 w-full min-h-[320px]">
          <ResponsiveContainer width="100%" height="100%" minHeight={320}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="name" hide />
              <YAxis domain={['auto', 'auto']} stroke="#64748b" tickFormatter={(val) => `$${val/1000}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} 
                itemStyle={{ color: '#10b981' }}
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

      {/* Top Positions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800">
          <h3 className="text-lg font-semibold text-slate-200">Current Holdings</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-medium">
              <tr>
                <th className="px-6 py-3">Symbol</th>
                <th className="px-6 py-3">Qty</th>
                <th className="px-6 py-3">Avg Price</th>
                <th className="px-6 py-3">Current</th>
                <th className="px-6 py-3">Market Value</th>
                <th className="px-6 py-3">Unrealized P&L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {positions.map((pos) => (
                <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-bold text-slate-200">{pos.symbol}</td>
                  <td className="px-6 py-4 text-slate-300">{pos.quantity}</td>
                  <td className="px-6 py-4 text-slate-400">${pos.avg_price.toFixed(2)}</td>
                  <td className="px-6 py-4 text-slate-300">${pos.current_price.toFixed(2)}</td>
                  <td className="px-6 py-4 text-slate-200">${pos.market_value.toLocaleString()}</td>
                  <td className={`px-6 py-4 font-medium ${pos.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                     {pos.unrealized_pnl >= 0 ? '+' : ''}{pos.unrealized_pnl.toFixed(2)} ({pos.unrealized_pnl_percent}%)
                  </td>
                </tr>
              ))}
              {positions.length === 0 && (
                <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">No open positions.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

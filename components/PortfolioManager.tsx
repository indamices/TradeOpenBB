import React, { useState, useEffect } from 'react';
import { 
  Wallet, Plus, Edit2, Trash2, TrendingUp, TrendingDown, 
  DollarSign, Activity, AlertCircle, Save, X, Loader2 
} from 'lucide-react';
import { Portfolio, Position, PositionCreate, PositionUpdate } from '../types';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';

const PortfolioManager: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingPosition, setEditingPosition] = useState<Position | null>(null);
  const [isAddingPosition, setIsAddingPosition] = useState(false);
  const [positionForm, setPositionForm] = useState({
    symbol: '',
    quantity: 0,
    avg_price: 0,
    current_price: 0
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [portfolioData, positionsData] = await Promise.all([
        tradingService.getPortfolio(1),
        tradingService.getPositions(1)
      ]);
      setPortfolio(portfolioData);
      setPositions(positionsData);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load portfolio data');
      console.error('Failed to load portfolio:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddPosition = async () => {
    if (!positionForm.symbol || positionForm.quantity <= 0 || positionForm.avg_price <= 0) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setError(null);
      const newPosition: PositionCreate = {
        portfolio_id: 1,
        symbol: positionForm.symbol.toUpperCase(),
        quantity: positionForm.quantity,
        avg_price: positionForm.avg_price,
        current_price: positionForm.current_price || positionForm.avg_price,
        market_value: positionForm.quantity * (positionForm.current_price || positionForm.avg_price),
        unrealized_pnl: 0,
        unrealized_pnl_percent: 0
      };
      
      await tradingService.createPosition(newPosition);
      await loadData();
      setIsAddingPosition(false);
      setPositionForm({ symbol: '', quantity: 0, avg_price: 0, current_price: 0 });
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to add position');
    }
  };

  const handleEditPosition = async () => {
    if (!editingPosition || positionForm.quantity <= 0 || positionForm.avg_price <= 0) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setError(null);
      const updateData: PositionUpdate = {
        quantity: positionForm.quantity,
        avg_price: positionForm.avg_price,
        current_price: positionForm.current_price || positionForm.avg_price
      };
      
      await tradingService.updatePosition(editingPosition.id, updateData);
      await loadData();
      setEditingPosition(null);
      setPositionForm({ symbol: '', quantity: 0, avg_price: 0, current_price: 0 });
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to update position');
    }
  };

  const handleDeletePosition = async (id: number) => {
    if (!confirm('Are you sure you want to delete this position?')) {
      return;
    }

    try {
      await tradingService.deletePosition(id);
      await loadData();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to delete position');
    }
  };

  const startEdit = (position: Position) => {
    setEditingPosition(position);
    setPositionForm({
      symbol: position.symbol,
      quantity: position.quantity,
      avg_price: position.avg_price,
      current_price: position.current_price
    });
    setIsAddingPosition(false);
  };

  const cancelEdit = () => {
    setEditingPosition(null);
    setIsAddingPosition(false);
    setPositionForm({ symbol: '', quantity: 0, avg_price: 0, current_price: 0 });
  };

  if (loading && !portfolio) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (error && !portfolio) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-slate-400">
        <AlertCircle size={48} className="mb-4 text-red-400" />
        <h2 className="text-xl font-bold text-slate-300 mb-2">加载失败</h2>
        <p className="text-slate-500">{error}</p>
      </div>
    );
  }

  if (!portfolio) {
    return <div className="text-slate-400">无投资组合数据</div>;
  }

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
              {portfolio.daily_pnl >= 0 ? <TrendingUp size={14} className="mr-1" /> : <TrendingDown size={14} className="mr-1" />}
              {portfolio.daily_pnl_percent >= 0 ? '+' : ''}{portfolio.daily_pnl_percent.toFixed(2)}%
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
              <Wallet size={20} />
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 text-red-400 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Add/Edit Position Form */}
      {(isAddingPosition || editingPosition) && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-4">
            {editingPosition ? '编辑持仓' : '添加持仓'}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                股票代码 *
              </label>
              <input
                type="text"
                value={positionForm.symbol}
                onChange={(e) => setPositionForm({ ...positionForm, symbol: e.target.value.toUpperCase() })}
                disabled={!!editingPosition}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                placeholder="AAPL"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                数量 *
              </label>
              <input
                type="number"
                value={positionForm.quantity || ''}
                onChange={(e) => setPositionForm({ ...positionForm, quantity: parseInt(e.target.value) || 0 })}
                min="1"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                平均成本价 *
              </label>
              <input
                type="number"
                value={positionForm.avg_price || ''}
                onChange={(e) => setPositionForm({ ...positionForm, avg_price: parseFloat(e.target.value) || 0 })}
                min="0"
                step="0.01"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="150.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                当前价格
              </label>
              <input
                type="number"
                value={positionForm.current_price || ''}
                onChange={(e) => setPositionForm({ ...positionForm, current_price: parseFloat(e.target.value) || 0 })}
                min="0"
                step="0.01"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="155.00"
              />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={editingPosition ? handleEditPosition : handleAddPosition}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
            >
              <Save size={16} />
              {editingPosition ? '保存' : '添加'}
            </button>
            <button
              onClick={cancelEdit}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors"
            >
              <X size={16} />
              取消
            </button>
          </div>
        </div>
      )}

      {/* Positions Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-slate-200">持仓列表</h3>
          {!isAddingPosition && !editingPosition && (
            <button
              onClick={() => setIsAddingPosition(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
            >
              <Plus size={16} />
              添加持仓
            </button>
          )}
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
                <th className="px-6 py-3">操作</th>
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
                    {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl.toFixed(2)} ({pos.unrealized_pnl_percent >= 0 ? '+' : ''}{pos.unrealized_pnl_percent.toFixed(2)}%)
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEdit(pos)}
                        className="p-2 text-slate-400 hover:text-blue-400 transition-colors"
                        title="编辑"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDeletePosition(pos.id)}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                        title="删除"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {positions.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    暂无持仓
                    {!isAddingPosition && (
                      <button
                        onClick={() => setIsAddingPosition(true)}
                        className="ml-2 text-blue-400 hover:text-blue-300"
                      >
                        点击添加
                      </button>
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PortfolioManager;

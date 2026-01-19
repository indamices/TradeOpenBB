import React, { useState, useEffect } from 'react';
import { 
  FileText, Download, Trash2, Eye, Edit2, X, 
  Check, Loader2, Search, Filter, ChevronLeft, ChevronRight 
} from 'lucide-react';
import { BacktestRecord, Strategy } from '../types';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';
import { formatMetric, formatDate } from '../utils/format';

interface BacktestRecordsProps {
  strategyId?: number;
  onRecordClick?: (record: BacktestRecord) => void;
}

const BacktestRecords: React.FC<BacktestRecordsProps> = ({
  strategyId,
  onRecordClick
}) => {
  const [records, setRecords] = useState<BacktestRecord[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<BacktestRecord | null>(null);
  const [filterStrategyId, setFilterStrategyId] = useState<number | undefined>(strategyId);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [editingRecordId, setEditingRecordId] = useState<number | null>(null);
  const [editName, setEditName] = useState<string>('');
  const [offset, setOffset] = useState<number>(0);
  const [limit] = useState<number>(20);
  const [hasMore, setHasMore] = useState<boolean>(true);

  useEffect(() => {
    loadStrategies();
    loadRecords();
  }, [filterStrategyId, offset]);

  const loadStrategies = async () => {
    try {
      const data = await tradingService.getStrategies();
      setStrategies(data);
    } catch (err) {
      console.error('Failed to load strategies:', err);
    }
  };

  const loadRecords = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await tradingService.getBacktestRecords(filterStrategyId, limit, offset);
      if (offset === 0) {
        setRecords(data);
      } else {
        setRecords(prev => [...prev, ...data]);
      }
      setHasMore(data.length === limit);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || '加载回测记录失败');
      console.error('Failed to load records:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (recordId: number) => {
    if (!confirm('确定要删除这条回测记录吗？')) {
      return;
    }

    try {
      await tradingService.deleteBacktestRecord(recordId);
      setRecords(records.filter(r => r.id !== recordId));
      if (selectedRecord?.id === recordId) {
        setSelectedRecord(null);
      }
    } catch (err) {
      const apiError = err as ApiError;
      alert(apiError.detail || '删除失败');
    }
  };

  const handleExport = async (recordId: number, format: 'csv' | 'excel') => {
    let url: string | null = null;
    try {
      const blob = format === 'csv'
        ? await tradingService.exportBacktestRecordCSV(recordId)
        : await tradingService.exportBacktestRecordExcel(recordId);

      url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backtest_record_${recordId}.${format === 'csv' ? 'csv' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      // Revoke ObjectURL after a short delay to ensure download starts
      setTimeout(() => {
        if (url) window.URL.revokeObjectURL(url);
      }, 100);
    } catch (err) {
      const apiError = err as ApiError;
      alert(apiError.detail || '导出失败');
    } finally {
      // Ensure cleanup even if error occurs
      if (url) {
        setTimeout(() => {
          window.URL.revokeObjectURL(url);
        }, 100);
      }
    }
  };

  const handleEdit = (record: BacktestRecord) => {
    setEditingRecordId(record.id);
    setEditName(record.name || '');
  };

  const handleSaveEdit = async (recordId: number) => {
    try {
      const updated = await tradingService.updateBacktestRecord(recordId, {
        name: editName
      });
      setRecords(records.map(r => r.id === recordId ? updated : r));
      setEditingRecordId(null);
      setEditName('');
    } catch (err) {
      const apiError = err as ApiError;
      alert(apiError.detail || '更新失败');
    }
  };

  const handleCancelEdit = () => {
    setEditingRecordId(null);
    setEditName('');
  };

  const filteredRecords = records.filter(record => {
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      return (
        (record.name?.toLowerCase().includes(term)) ||
        (record.strategy_name?.toLowerCase().includes(term)) ||
        (record.symbols.some(s => s.toLowerCase().includes(term)))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-2">
          <FileText className="text-blue-400" size={24} />
          <h2 className="text-2xl font-bold text-slate-200">回测记录</h2>
        </div>
        <p className="text-slate-400">查看、管理和导出历史回测结果</p>
      </div>

      {/* Filters */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Strategy Filter */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              筛选策略
            </label>
            <select
              value={filterStrategyId || ''}
              onChange={(e) => {
                setFilterStrategyId(e.target.value ? parseInt(e.target.value) : undefined);
                setOffset(0);
              }}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">所有策略</option>
              {strategies.map(strategy => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.name}
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              搜索
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="搜索记录名称、策略或股票代码..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Records List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        {loading && offset === 0 ? (
          <div className="p-12 text-center">
            <Loader2 className="animate-spin text-blue-400 mx-auto mb-4" size={32} />
            <p className="text-slate-400">加载中...</p>
          </div>
        ) : filteredRecords.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="text-slate-600 mx-auto mb-4" size={48} />
            <p className="text-slate-400">没有找到回测记录</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-800">
                  <tr>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">记录名称</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">策略</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">股票</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">日期范围</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">Sharpe</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">总收益率</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">最大回撤</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">创建时间</th>
                    <th className="text-right py-3 px-4 text-slate-300 font-semibold">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRecords.map((record) => (
                    <tr
                      key={record.id}
                      className="border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer"
                      onClick={() => {
                        setSelectedRecord(record);
                        if (onRecordClick) {
                          onRecordClick(record);
                        }
                      }}
                    >
                      <td className="py-3 px-4">
                        {editingRecordId === record.id ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={editName}
                              onChange={(e) => setEditName(e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                              className="flex-1 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-slate-200 text-sm"
                              autoFocus
                            />
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSaveEdit(record.id);
                              }}
                              className="p-1 text-emerald-400 hover:text-emerald-300"
                            >
                              <Check size={16} />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCancelEdit();
                              }}
                              className="p-1 text-red-400 hover:text-red-300"
                            >
                              <X size={16} />
                            </button>
                          </div>
                        ) : (
                          <span className="text-slate-200 font-medium">
                            {record.name || `回测记录 #${record.id}`}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {record.strategy_name || `策略 #${record.strategy_id}`}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {record.symbols.slice(0, 3).join(', ')}
                        {record.symbols.length > 3 && ` +${record.symbols.length - 3}`}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {formatDate(record.start_date)} ~ {formatDate(record.end_date)}
                      </td>
                      <td className="text-right py-3 px-4 text-slate-300">
                        {formatMetric(record.sharpe_ratio)}
                      </td>
                      <td className="text-right py-3 px-4 text-slate-300">
                        {formatMetric(record.total_return, '%')}
                      </td>
                      <td className="text-right py-3 px-4 text-red-400">
                        {formatMetric(record.max_drawdown, '%')}
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-sm">
                        {formatDate(record.created_at)}
                      </td>
                      <td className="py-3 px-4">
                        <div
                          className="flex items-center justify-end gap-2"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            onClick={() => {
                              setSelectedRecord(record);
                              if (onRecordClick) {
                                onRecordClick(record);
                              }
                            }}
                            className="p-1.5 text-blue-400 hover:text-blue-300 hover:bg-slate-700 rounded"
                            title="查看详情"
                          >
                            <Eye size={16} />
                          </button>
                          <button
                            onClick={() => handleEdit(record)}
                            className="p-1.5 text-yellow-400 hover:text-yellow-300 hover:bg-slate-700 rounded"
                            title="编辑名称"
                          >
                            <Edit2 size={16} />
                          </button>
                          <div className="relative group">
                            <button
                              className="p-1.5 text-emerald-400 hover:text-emerald-300 hover:bg-slate-700 rounded"
                              title="导出"
                            >
                              <Download size={16} />
                            </button>
                            <div className="absolute right-0 mt-1 w-32 bg-slate-800 border border-slate-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                              <button
                                onClick={() => handleExport(record.id, 'csv')}
                                className="w-full text-left px-3 py-2 text-slate-300 hover:bg-slate-700 rounded-t-lg text-sm"
                              >
                                CSV导出
                              </button>
                              <button
                                onClick={() => handleExport(record.id, 'excel')}
                                className="w-full text-left px-3 py-2 text-slate-300 hover:bg-slate-700 rounded-b-lg text-sm"
                              >
                                Excel导出
                              </button>
                            </div>
                          </div>
                          <button
                            onClick={() => handleDelete(record.id)}
                            className="p-1.5 text-red-400 hover:text-red-300 hover:bg-slate-700 rounded"
                            title="删除"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Load More */}
            {hasMore && (
              <div className="p-4 text-center border-t border-slate-800">
                <button
                  onClick={() => setOffset(prev => prev + limit)}
                  disabled={loading}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-slate-300 rounded-lg flex items-center gap-2 mx-auto"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin" size={16} />
                      <span>加载中...</span>
                    </>
                  ) : (
                    <>
                      <ChevronRight size={16} />
                      <span>加载更多</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Record Detail Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-900 border-b border-slate-800 p-6 flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-200">
                {selectedRecord.name || `回测记录 #${selectedRecord.id}`}
              </h3>
              <button
                onClick={() => setSelectedRecord(null)}
                className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-400">策略</div>
                  <div className="text-slate-200 font-medium">
                    {selectedRecord.strategy_name || `策略 #${selectedRecord.strategy_id}`}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400">股票代码</div>
                  <div className="text-slate-200 font-medium">
                    {selectedRecord.symbols.join(', ')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400">日期范围</div>
                  <div className="text-slate-200 font-medium">
                    {formatDate(selectedRecord.start_date)} ~ {formatDate(selectedRecord.end_date)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400">初始资金</div>
                  <div className="text-slate-200 font-medium">
                    ${selectedRecord.initial_cash.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-800 p-4 rounded-lg">
                  <div className="text-sm text-slate-400">Sharpe Ratio</div>
                  <div className="text-2xl font-bold text-emerald-400">
                    {formatMetric(selectedRecord.sharpe_ratio)}
                  </div>
                </div>
                <div className="bg-slate-800 p-4 rounded-lg">
                  <div className="text-sm text-slate-400">年化收益率</div>
                  <div className="text-2xl font-bold text-emerald-400">
                    {formatMetric(selectedRecord.annualized_return, '%')}
                  </div>
                </div>
                <div className="bg-slate-800 p-4 rounded-lg">
                  <div className="text-sm text-slate-400">最大回撤</div>
                  <div className="text-2xl font-bold text-red-400">
                    {formatMetric(selectedRecord.max_drawdown, '%')}
                  </div>
                </div>
                <div className="bg-slate-800 p-4 rounded-lg">
                  <div className="text-sm text-slate-400">胜率</div>
                  <div className="text-2xl font-bold text-blue-400">
                    {formatMetric(selectedRecord.win_rate, '%')}
                  </div>
                </div>
              </div>

              {/* Export Buttons */}
              <div className="flex gap-4 pt-4 border-t border-slate-800">
                <button
                  onClick={() => handleExport(selectedRecord.id, 'csv')}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-2"
                >
                  <Download size={18} />
                  <span>导出CSV</span>
                </button>
                <button
                  onClick={() => handleExport(selectedRecord.id, 'excel')}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-2"
                >
                  <Download size={18} />
                  <span>导出Excel</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
          {error}
        </div>
      )}
    </div>
  );
};

export default BacktestRecords;

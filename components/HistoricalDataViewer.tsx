import React, { useState } from 'react';
import { 
  Download, Loader2, AlertCircle, CheckCircle, 
  Calendar, TrendingUp, BarChart3 
} from 'lucide-react';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';

interface HistoricalDataPoint {
  Date: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
}

const HistoricalDataViewer: React.FC = () => {
  const [symbol, setSymbol] = useState<string>('AAPL');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<HistoricalDataPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Set default dates (last year)
  React.useEffect(() => {
    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - 1);
    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
  }, []);

  const handleFetchData = async () => {
    if (!symbol.trim()) {
      setError('请输入股票代码');
      return;
    }

    if (!startDate || !endDate) {
      setError('请选择日期范围');
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError('开始日期不能晚于结束日期');
      return;
    }

    setLoading(true);
    setError(null);
    setData([]);

    try {
      const result = await tradingService.getHistoricalData(
        symbol.trim().toUpperCase(),
        startDate,
        endDate
      );
      
      // Handle both array and object formats
      if (Array.isArray(result)) {
        setData(result);
      } else if (result && typeof result === 'object') {
        // Convert object to array if needed
        setData([result]);
      } else {
        setData([]);
      }
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || '获取历史数据失败');
      console.error('Historical data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (data.length === 0) return;

    const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'];
    const csvContent = [
      headers.join(','),
      ...data.map(row => {
        const date = row.Date || '';
        const open = row.Open || 0;
        const high = row.High || 0;
        const low = row.Low || 0;
        const close = row.Close || 0;
        const volume = row.Volume || 0;
        return `${date},${open},${high},${low},${close},${volume}`;
      })
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${symbol}_${startDate}_${endDate}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatNumber = (num: number | null | undefined): string => {
    if (num === null || num === undefined) return '-';
    return num.toFixed(2);
  };

  const formatVolume = (vol: number | null | undefined): string => {
    if (vol === null || vol === undefined) return '-';
    if (vol >= 1000000) {
      return `${(vol / 1000000).toFixed(2)}M`;
    } else if (vol >= 1000) {
      return `${(vol / 1000).toFixed(2)}K`;
    }
    return vol.toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-2">
          <BarChart3 className="text-blue-400" size={24} />
          <h2 className="text-2xl font-bold text-slate-200">历史数据获取</h2>
        </div>
        <p className="text-slate-400">获取指定股票的历史OHLCV数据</p>
      </div>

      {/* Configuration Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-slate-200 mb-4">数据查询配置</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Symbol Input */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              股票代码
            </label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="AAPL"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
              <Calendar size={16} />
              开始日期
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
              <Calendar size={16} />
              结束日期
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>
        </div>

        {/* Fetch Button */}
        <div className="mt-6">
          <button
            onClick={handleFetchData}
            disabled={loading || !symbol || !startDate || !endDate}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                <span>获取中...</span>
              </>
            ) : (
              <>
                <TrendingUp size={20} />
                <span>获取数据</span>
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

      {/* Data Display */}
      {data.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-200">
                历史数据 ({data.length} 条记录)
              </h3>
              <p className="text-sm text-slate-400 mt-1">
                {symbol} - {startDate} 至 {endDate}
              </p>
            </div>
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-4 py-2 rounded-lg transition-colors"
            >
              <Download size={18} />
              <span>导出CSV</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-medium">
                <tr>
                  <th className="px-6 py-3">日期</th>
                  <th className="px-6 py-3 text-right">开盘价</th>
                  <th className="px-6 py-3 text-right">最高价</th>
                  <th className="px-6 py-3 text-right">最低价</th>
                  <th className="px-6 py-3 text-right">收盘价</th>
                  <th className="px-6 py-3 text-right">成交量</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data.map((row, index) => {
                  const date = row.Date || '';
                  const formattedDate = date ? new Date(date).toLocaleDateString('zh-CN') : '-';
                  const close = row.Close || 0;
                  const open = row.Open || 0;
                  const change = close - open;
                  const changePercent = open !== 0 ? (change / open) * 100 : 0;
                  const isPositive = change >= 0;

                  return (
                    <tr key={`data-${formattedDate}-${index}`} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-300">{formattedDate}</td>
                      <td className="px-6 py-4 text-right text-slate-300">
                        ${formatNumber(row.Open)}
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300">
                        ${formatNumber(row.High)}
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300">
                        ${formatNumber(row.Low)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span className={`font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                            ${formatNumber(close)}
                          </span>
                          {change !== 0 && (
                            <span className={`text-xs ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                              {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300">
                        {formatVolume(row.Volume)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Summary Statistics */}
          {data.length > 0 && (
            <div className="px-6 py-4 bg-slate-800/50 border-t border-slate-800">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">最高价:</span>
                  <span className="text-emerald-400 font-semibold ml-2">
                    ${formatNumber(Math.max(...data.map(d => d.High || 0)))}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">最低价:</span>
                  <span className="text-red-400 font-semibold ml-2">
                    ${formatNumber(Math.min(...data.map(d => d.Low || 0)))}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">平均成交量:</span>
                  <span className="text-slate-300 font-semibold ml-2">
                    {formatVolume(
                      data.reduce((sum, d) => sum + (d.Volume || 0), 0) / data.length
                    )}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">总成交量:</span>
                  <span className="text-slate-300 font-semibold ml-2">
                    {formatVolume(data.reduce((sum, d) => sum + (d.Volume || 0), 0))}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && data.length === 0 && !error && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
          <BarChart3 className="text-slate-600 mx-auto mb-4" size={48} />
          <p className="text-slate-400">输入股票代码和日期范围，然后点击"获取数据"</p>
        </div>
      )}
    </div>
  );
};

export default HistoricalDataViewer;

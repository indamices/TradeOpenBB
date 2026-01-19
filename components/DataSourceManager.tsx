import React, { useState, useEffect } from 'react';
import { 
  Database, Plus, Edit2, Trash2, Check, X, Loader2, 
  AlertCircle, Settings, CheckCircle, XCircle 
} from 'lucide-react';
import { DataSourceConfig, DataSourceConfigCreate, DataSourceConfigUpdate, AvailableDataSource } from '../types';
import { dataSourceService } from '../services/dataSourceService';
import { ApiError } from '../services/apiClient';

const DataSourceManager: React.FC = () => {
  const [dataSources, setDataSources] = useState<DataSourceConfig[]>([]);
  const [availableSources, setAvailableSources] = useState<AvailableDataSource[]>([]);
  const [sourceStatuses, setSourceStatuses] = useState<{ [key: number]: { is_working: boolean; working_source_id?: number; error?: string } }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState<DataSourceConfigCreate>({
    name: '',
    source_type: 'free',
    provider: '',
    api_key: '',
    base_url: '',
    is_active: true,
    is_default: false,
    priority: 0,
    supports_markets: ['US'],
    rate_limit: 100
  });

  useEffect(() => {
    loadDataSources();
    loadAvailableSources();
    loadDataSourcesStatus();
  }, []);

  const loadDataSourcesStatus = async () => {
    try {
      const status = await dataSourceService.getDataSourcesStatus();
      const statusMap: { [key: number]: { is_working: boolean; working_source_id?: number; error?: string } } = {};

      // Add null check for status.sources
      if (status?.sources && Array.isArray(status.sources)) {
        status.sources.forEach(s => {
          if (s?.source_id !== undefined) {
            statusMap[s.source_id] = {
              is_working: s.is_working ?? false,
              error: s.error
            };
          }
        });
      }
      
      if (status?.working_source_id) {
        Object.keys(statusMap).forEach(id => {
          const sourceId = parseInt(id, 10);
          if (sourceId === status.working_source_id) {
            statusMap[sourceId].working_source_id = status.working_source_id;
          }
        });
      }
      
      setSourceStatuses(statusMap);
    } catch (err) {
      console.error('Failed to load data sources status:', err);
      // Set empty status map on error to prevent undefined errors
      setSourceStatuses({});
    }
  };

  const loadDataSources = async () => {
    try {
      setLoading(true);
      setError(null);
      const sources = await dataSourceService.getDataSources();
      setDataSources(sources);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load data sources');
      console.error('Failed to load data sources:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableSources = async () => {
    try {
      const response = await dataSourceService.getAvailableDataSources();
      setAvailableSources(response.sources);
    } catch (err) {
      console.error('Failed to load available sources:', err);
    }
  };

  const handleAdd = async () => {
    try {
      setError(null);
      await dataSourceService.createDataSource(formData);
      await loadDataSources();
      await loadDataSourcesStatus();
      setShowAddForm(false);
      setFormData({
        name: '',
        source_type: 'free',
        provider: '',
        api_key: '',
        base_url: '',
        is_active: true,
        is_default: false,
        priority: 0,
        supports_markets: ['US'],
        rate_limit: 100
      });
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to create data source');
      console.error('Failed to create data source:', err);
    }
  };

  const handleUpdate = async (id: number, data: DataSourceConfigUpdate) => {
    try {
      setError(null);
      await dataSourceService.updateDataSource(id, data);
      await loadDataSources();
      await loadDataSourcesStatus();
      setEditingId(null);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to update data source');
      console.error('Failed to update data source:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this data source?')) {
      return;
    }
    
    try {
      setError(null);
      await dataSourceService.deleteDataSource(id);
      await loadDataSources();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to delete data source');
      console.error('Failed to delete data source:', err);
    }
  };

  const handleSetDefault = async (id: number) => {
    try {
      setError(null);
      await dataSourceService.updateDataSource(id, { is_default: true });
      await loadDataSources();
      await loadDataSourcesStatus();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to set default data source');
      console.error('Failed to set default:', err);
    }
  };

  const handleToggleActive = async (id: number, currentStatus: boolean) => {
    try {
      setError(null);
      await dataSourceService.updateDataSource(id, { is_active: !currentStatus });
      await loadDataSources();
      await loadDataSourcesStatus();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to toggle active status');
      console.error('Failed to toggle active:', err);
    }
  };

  const quickAddFromAvailable = async (source: AvailableDataSource) => {
    try {
      setError(null);
      const createData: DataSourceConfigCreate = {
        name: source.name,
        source_type: source.source_type as 'free' | 'paid' | 'api' | 'direct',
        provider: source.provider,
        api_key: '',  // User needs to provide API key manually
        base_url: '',
        is_active: false,  // Inactive by default until API key is set
        is_default: false,
        priority: 0,
        supports_markets: source.supports_markets || ['US'],
        rate_limit: source.rate_limit || 100
      };
      await dataSourceService.createDataSource(createData);
      await loadDataSources();
      await loadDataSourcesStatus();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to add data source');
      console.error('Failed to add data source:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-200 mb-2 flex items-center gap-2">
              <Database size={24} className="text-blue-400" />
              数据源管理
            </h2>
            <p className="text-slate-400">配置和管理市场数据源</p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} />
            <span>添加数据源</span>
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-center gap-2 text-red-400">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Add Form */}
      {showAddForm && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-4">添加新数据源</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">名称</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="数据源名称"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">类型</label>
                <select
                  value={formData.source_type}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (['free', 'paid', 'api', 'direct'].includes(value)) {
                      setFormData({ ...formData, source_type: value as 'free' | 'paid' | 'api' | 'direct' });
                    }
                  }}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="free">免费</option>
                  <option value="paid">付费</option>
                  <option value="api">API</option>
                  <option value="direct">直连</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">提供商</label>
                <input
                  type="text"
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: yfinance, openbb"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">API Key (可选)</label>
              <input
                type="password"
                value={formData.api_key || ''}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="输入API密钥（如有）"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Base URL (可选)</label>
              <input
                type="text"
                value={formData.base_url || ''}
                onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://api.example.com"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">优先级</label>
                <input
                  type="number"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: Number(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">速率限制 (请求/分钟)</label>
                <input
                  type="number"
                  value={formData.rate_limit}
                  onChange={(e) => setFormData({ ...formData, rate_limit: Number(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_active || false}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-slate-300">激活</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_default || false}
                  onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-slate-300">设为默认</span>
              </label>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleAdd}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                <Check size={18} />
                <span>添加</span>
              </button>
              <button
                onClick={() => setShowAddForm(false)}
                className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                <X size={18} />
                <span>取消</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Available Sources */}
      {availableSources.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-4">可用数据源</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableSources.map((source) => (
              <div
                key={source.name}
                className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:bg-slate-750 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-semibold text-slate-200">{source.name}</h4>
                    <p className="text-sm text-slate-400 mt-1">{source.description}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded ${
                    source.source_type === 'free' 
                      ? 'bg-emerald-500/20 text-emerald-400' 
                      : 'bg-blue-500/20 text-blue-400'
                  }`}>
                    {source.source_type}
                  </span>
                </div>
                <div className="text-xs text-slate-500 space-y-1 mt-2">
                  <div>提供商: {source.provider}</div>
                  <div>支持市场: {source.supports_markets?.join(', ') || 'N/A'}</div>
                  <div>速率限制: {source.rate_limit} 请求/分钟</div>
                  {source.requires_api_key && (
                    <div className="text-yellow-400">
                      需要 API Key
                      {source.api_key_url && (
                        <a href={source.api_key_url} target="_blank" rel="noopener noreferrer" className="underline ml-1">
                          获取
                        </a>
                      )}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => quickAddFromAvailable(source)}
                  className="mt-3 w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors"
                >
                  快速添加
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Sources List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800">
          <h3 className="text-lg font-semibold text-slate-200">已配置的数据源</h3>
        </div>
        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="animate-spin mx-auto text-blue-400" size={32} />
            <p className="text-slate-400 mt-2">加载中...</p>
          </div>
        ) : dataSources.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            还没有配置数据源，点击"添加数据源"开始配置
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase font-medium">
                <tr>
                  <th className="px-6 py-3">名称</th>
                  <th className="px-6 py-3">类型</th>
                  <th className="px-6 py-3">提供商</th>
                  <th className="px-6 py-3">状态</th>
                  <th className="px-6 py-3">默认</th>
                  <th className="px-6 py-3">优先级</th>
                  <th className="px-6 py-3">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {dataSources.map((source) => (
                  <tr key={source.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-200">{source.name}</td>
                    <td className="px-6 py-4 text-slate-300">
                      <span className={`text-xs px-2 py-1 rounded ${
                        source.source_type === 'free' 
                          ? 'bg-emerald-500/20 text-emerald-400' 
                          : 'bg-blue-500/20 text-blue-400'
                      }`}>
                        {source.source_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-300">{source.provider}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <button
                          onClick={() => handleToggleActive(source.id, source.is_active)}
                          className={`flex items-center gap-2 px-2 py-1 rounded text-xs font-medium transition-colors ${
                            source.is_active
                              ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
                              : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                          }`}
                        >
                          {source.is_active ? (
                            <>
                              <CheckCircle size={14} />
                              激活
                            </>
                          ) : (
                            <>
                              <XCircle size={14} />
                              未激活
                            </>
                          )}
                        </button>
                        {source.is_active && sourceStatuses && typeof sourceStatuses === 'object' && sourceStatuses[source.id] ? (
                          <div className="flex flex-col gap-1">
                            <span className={`text-xs px-1 py-0.5 rounded ${
                              sourceStatuses[source.id]?.is_working
                                ? 'bg-blue-500/20 text-blue-400'
                                : 'bg-red-500/20 text-red-400'
                            }`}>
                              {sourceStatuses[source.id]?.is_working ? '✓ 可用' : '✗ 不可用'}
                            </span>
                            {!sourceStatuses[source.id]?.is_working && sourceStatuses[source.id]?.error && (
                              <span className="text-xs text-red-400 max-w-[200px] truncate" title={sourceStatuses[source.id].error}>
                                {sourceStatuses[source.id].error}
                              </span>
                            )}
                          </div>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {source.is_default ? (
                        <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400 font-medium">
                          默认
                        </span>
                      ) : (
                        <button
                          onClick={() => handleSetDefault(source.id)}
                          className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-400 hover:bg-slate-600 transition-colors"
                        >
                          设为默认
                        </button>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-300">{source.priority}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={async () => {
                            try {
                              setError(null);
                              setLoading(true);
                              try {
                                const result = await dataSourceService.testDataSourceConnection(source.id);
                                if (result.success) {
                                  alert(`✅ ${result.message || '连接测试成功！'}\n\n数据源: ${result.source_name || source.name}\n提供商: ${result.provider || 'Unknown'}\n测试股票: ${result.symbol || 'N/A'}\n数据点: ${result.data_points || 0}\n日期范围: ${result.date_range || 'N/A'}`);
                                } else {
                                  alert(`❌ ${result.message || '连接测试失败'}\n\n数据源: ${result.source_name || source.name}\n提供商: ${result.provider || 'Unknown'}\n${result.error ? `错误: ${result.error}` : ''}`);
                                }
                              } finally {
                                setLoading(false);
                              }
                            } catch (err) {
                              const apiError = err as ApiError;
                              setError(apiError.detail || '连接测试失败');
                            }
                          }}
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                          title="测试连接"
                        >
                          <Settings size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(source.id)}
                          className="text-red-400 hover:text-red-300 transition-colors"
                          title="删除"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataSourceManager;

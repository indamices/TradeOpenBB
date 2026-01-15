import React, { useState, useEffect } from 'react';
import { List, Plus, Edit, Trash2, Save, X, FileText, Loader2 } from 'lucide-react';
import { symbolListService, SymbolList } from '../services/symbolListService';

interface BacktestSymbolListProps {
  selectedListId: number | null;
  onSelectList: (listId: number | null, symbols: string[]) => void;
  currentSymbols?: string[];
}

const BacktestSymbolList: React.FC<BacktestSymbolListProps> = ({
  selectedListId,
  onSelectList,
  currentSymbols = []
}) => {
  const [lists, setLists] = useState<SymbolList[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingList, setEditingList] = useState<SymbolList | null>(null);
  const [form, setForm] = useState({ name: '', description: '', symbols: '' });

  useEffect(() => {
    loadLists();
  }, []);

  const loadLists = async () => {
    try {
      setLoading(true);
      const data = await symbolListService.getSymbolLists(true); // Only active lists
      setLists(data);
    } catch (error) {
      console.error('Failed to load symbol lists:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectList = (list: SymbolList) => {
    onSelectList(list.id, list.symbols);
  };

  const handleCreate = async () => {
    if (!form.name.trim() || !form.symbols.trim()) {
      alert('请输入清单名称和股票代码');
      return;
    }

    const symbols = form.symbols.split(',').map(s => s.trim().toUpperCase()).filter(s => s);
    if (symbols.length === 0) {
      alert('请输入至少一个股票代码');
      return;
    }

    try {
      await symbolListService.createSymbolList({
        name: form.name,
        description: form.description || undefined,
        symbols
      });
      await loadLists();
      setShowCreateDialog(false);
      setForm({ name: '', description: '', symbols: '' });
    } catch (error) {
      console.error('Failed to create symbol list:', error);
      alert('创建清单失败');
    }
  };

  const handleSaveCurrent = () => {
    if (currentSymbols.length === 0) {
      alert('当前没有选中的股票');
      return;
    }
    setForm({
      name: '',
      description: '',
      symbols: currentSymbols.join(', ')
    });
    setShowCreateDialog(true);
  };

  const handleEdit = (list: SymbolList) => {
    setEditingList(list);
    setForm({
      name: list.name,
      description: list.description || '',
      symbols: list.symbols.join(', ')
    });
    setShowCreateDialog(true);
  };

  const handleUpdate = async () => {
    if (!editingList || !form.name.trim() || !form.symbols.trim()) {
      alert('请输入清单名称和股票代码');
      return;
    }

    const symbols = form.symbols.split(',').map(s => s.trim().toUpperCase()).filter(s => s);
    if (symbols.length === 0) {
      alert('请输入至少一个股票代码');
      return;
    }

    try {
      await symbolListService.updateSymbolList(editingList.id, {
        name: form.name,
        description: form.description || undefined,
        symbols
      });
      await loadLists();
      setShowCreateDialog(false);
      setEditingList(null);
      setForm({ name: '', description: '', symbols: '' });
      
      // Update selected list if it's the one being edited
      if (selectedListId === editingList.id) {
        onSelectList(editingList.id, symbols);
      }
    } catch (error) {
      console.error('Failed to update symbol list:', error);
      alert('更新清单失败');
    }
  };

  const handleDelete = async (listId: number) => {
    if (!confirm('确定要删除这个清单吗？')) return;
    try {
      await symbolListService.deleteSymbolList(listId);
      await loadLists();
      if (selectedListId === listId) {
        onSelectList(null, []);
      }
    } catch (error) {
      console.error('Failed to delete symbol list:', error);
      alert('删除清单失败');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 text-slate-400">
        <Loader2 className="animate-spin mr-2" size={20} />
        <span>加载中...</span>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <label className="block text-sm font-medium text-slate-400">
          保存的股票清单
        </label>
        <div className="flex gap-2">
          {currentSymbols.length > 0 && (
            <button
              onClick={handleSaveCurrent}
              className="px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium flex items-center gap-1 transition"
              title="保存当前配置为清单"
            >
              <Save size={12} /> 保存当前
            </button>
          )}
          <button
            onClick={() => {
              setEditingList(null);
              setForm({ name: '', description: '', symbols: '' });
              setShowCreateDialog(true);
            }}
            className="px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium flex items-center gap-1 transition"
          >
            <Plus size={12} /> 新建清单
          </button>
        </div>
      </div>

      {lists.length === 0 ? (
        <div className="text-center py-6 text-slate-500 text-sm">
          <FileText size={32} className="mx-auto mb-2 text-slate-700" />
          <p>还没有保存的清单</p>
          <p className="text-xs mt-1">创建清单后可以快速选择</p>
        </div>
      ) : (
        <div className="space-y-2">
          {lists.map((list) => (
            <div
              key={list.id}
              className={`p-3 rounded-lg border cursor-pointer transition ${
                selectedListId === list.id
                  ? 'bg-emerald-600/20 border-emerald-600/30'
                  : 'bg-slate-800 hover:bg-slate-700 border-slate-700'
              }`}
              onClick={() => handleSelectList(list)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <List size={14} className="text-slate-400" />
                    <div className="text-sm font-medium text-slate-200 truncate">
                      {list.name}
                    </div>
                  </div>
                  {list.description && (
                    <div className="text-xs text-slate-400 mb-2">{list.description}</div>
                  )}
                  <div className="text-xs text-slate-500">
                    {list.symbols.length} 个标的: {list.symbols.slice(0, 5).join(', ')}
                    {list.symbols.length > 5 && '...'}
                  </div>
                </div>
                <div className="flex gap-1 ml-2" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => handleEdit(list)}
                    className="p-1 hover:bg-slate-600 rounded transition"
                    title="编辑"
                  >
                    <Edit size={12} className="text-slate-400" />
                  </button>
                  <button
                    onClick={() => handleDelete(list.id)}
                    className="p-1 hover:bg-red-600/20 rounded transition"
                    title="删除"
                  >
                    <Trash2 size={12} className="text-red-400" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-200">
                {editingList ? '编辑清单' : '新建清单'}
              </h3>
              <button
                onClick={() => {
                  setShowCreateDialog(false);
                  setEditingList(null);
                  setForm({ name: '', description: '', symbols: '' });
                }}
                className="p-1 hover:bg-slate-700 rounded transition"
              >
                <X size={18} className="text-slate-400" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">清单名称 *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="例如：科技股组合"
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">描述（可选）</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={2}
                  placeholder="清单的简要说明"
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500 resize-none"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">股票代码 *</label>
                <textarea
                  value={form.symbols}
                  onChange={(e) => setForm({ ...form, symbols: e.target.value })}
                  rows={4}
                  placeholder="例如：AAPL, MSFT, GOOGL, TSLA"
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-emerald-500 resize-none"
                />
                <div className="text-xs text-slate-500 mt-1">
                  多个股票代码请用逗号分隔
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={editingList ? handleUpdate : handleCreate}
                  disabled={!form.name.trim() || !form.symbols.trim()}
                  className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded text-sm font-medium transition"
                >
                  <Save size={14} className="inline mr-2" />
                  {editingList ? '更新' : '创建'}
                </button>
                <button
                  onClick={() => {
                    setShowCreateDialog(false);
                    setEditingList(null);
                    setForm({ name: '', description: '', symbols: '' });
                  }}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm font-medium transition"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BacktestSymbolList;

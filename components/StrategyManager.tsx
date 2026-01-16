import React, { useState, useEffect } from 'react';
import { Settings, Search, Filter, Edit, Trash2, Power, PowerOff, CheckSquare, Square, Plus, X, Save, Code } from 'lucide-react';
import { tradingService } from '../services/tradingService';
import { Strategy } from '../types';

const StrategyManager: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [filteredStrategies, setFilteredStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [selectedStrategies, setSelectedStrategies] = useState<Set<number>>(new Set());
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
  const [editForm, setEditForm] = useState({ name: '', description: '', logic_code: '' });

  useEffect(() => {
    loadStrategies();
    
    // Listen for strategy saved events to refresh the list
    const handleStrategySaved = () => {
      loadStrategies();
    };
    window.addEventListener('strategySaved', handleStrategySaved);
    
    return () => {
      window.removeEventListener('strategySaved', handleStrategySaved);
    };
  }, []);

  useEffect(() => {
    filterStrategies();
  }, [strategies, searchTerm, activeFilter]);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const data = await tradingService.getStrategies();
      setStrategies(data);
    } catch (error) {
      console.error('Failed to load strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterStrategies = () => {
    let filtered = [...strategies];

    // Apply active filter
    if (activeFilter === 'active') {
      filtered = filtered.filter(s => s.is_active);
    } else if (activeFilter === 'inactive') {
      filtered = filtered.filter(s => !s.is_active);
    }

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(s => 
        s.name.toLowerCase().includes(term) ||
        (s.description && s.description.toLowerCase().includes(term))
      );
    }

    setFilteredStrategies(filtered);
  };

  const handleToggleActive = async (strategyId: number, currentStatus: boolean) => {
    try {
      await tradingService.setStrategyActive(strategyId, !currentStatus);
      await loadStrategies();
      setSelectedStrategies(new Set());
    } catch (error) {
      console.error('Failed to toggle strategy status:', error);
      alert('Failed to update strategy status');
    }
  };

  const handleBatchToggle = async (isActive: boolean) => {
    if (selectedStrategies.size === 0) return;
    
    try {
      await tradingService.batchSetStrategyActive(Array.from(selectedStrategies), isActive);
      await loadStrategies();
      setSelectedStrategies(new Set());
    } catch (error) {
      console.error('Failed to batch update strategies:', error);
      alert('Failed to update strategies');
    }
  };

  const handleDelete = async (strategyId: number) => {
    if (!confirm('Are you sure you want to delete this strategy?')) return;
    
    try {
      await tradingService.deleteStrategy(strategyId);
      await loadStrategies();
    } catch (error) {
      console.error('Failed to delete strategy:', error);
      alert('Failed to delete strategy');
    }
  };

  const handleEdit = (strategy: Strategy) => {
    setEditingStrategy(strategy);
    setEditForm({
      name: strategy.name,
      description: strategy.description || '',
      logic_code: strategy.logic_code
    });
  };

  const handleSaveEdit = async () => {
    if (!editingStrategy) return;
    
    try {
      await tradingService.updateStrategy(editingStrategy.id, {
        name: editForm.name,
        description: editForm.description,
        logic_code: editForm.logic_code
      });
      await loadStrategies();
      setEditingStrategy(null);
    } catch (error) {
      console.error('Failed to update strategy:', error);
      alert('Failed to update strategy');
    }
  };

  const handleSelectStrategy = (strategyId: number) => {
    const newSelected = new Set(selectedStrategies);
    if (newSelected.has(strategyId)) {
      newSelected.delete(strategyId);
    } else {
      newSelected.add(strategyId);
    }
    setSelectedStrategies(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedStrategies.size === filteredStrategies.length) {
      setSelectedStrategies(new Set());
    } else {
      setSelectedStrategies(new Set(filteredStrategies.map(s => s.id)));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[50vh] text-slate-400">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mx-auto mb-4"></div>
          <p>Loading strategies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-800/50 flex items-center justify-between">
        <div className="flex items-center gap-2 text-emerald-400">
          <Settings size={20} />
          <h2 className="font-bold text-lg text-white">Strategy Management</h2>
        </div>
        {selectedStrategies.size > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleBatchToggle(true)}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-sm font-medium flex items-center gap-2 transition"
            >
              <Power size={14} /> Activate ({selectedStrategies.size})
            </button>
            <button
              onClick={() => handleBatchToggle(false)}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm font-medium flex items-center gap-2 transition"
            >
              <PowerOff size={14} /> Deactivate ({selectedStrategies.size})
            </button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-900 flex items-center gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" size={18} />
          <input
            type="text"
            placeholder="Search strategies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded px-10 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={18} className="text-slate-400" />
          <select
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value as 'all' | 'active' | 'inactive')}
            className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All Strategies</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
        </div>
        <button
          onClick={handleSelectAll}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded text-sm font-medium flex items-center gap-2 transition"
        >
          {selectedStrategies.size === filteredStrategies.length ? (
            <>
              <CheckSquare size={14} /> Deselect All
            </>
          ) : (
            <>
              <Square size={14} /> Select All
            </>
          )}
        </button>
      </div>

      {/* Strategy List */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredStrategies.length === 0 ? (
          <div className="text-center text-slate-500 py-12">
            <Settings size={48} className="mx-auto mb-4 text-slate-700" />
            <p className="text-lg font-medium mb-2">No strategies found</p>
            <p className="text-sm">
              {searchTerm || activeFilter !== 'all' 
                ? 'Try adjusting your filters' 
                : 'Create a strategy to get started'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredStrategies.map((strategy) => (
              <div
                key={strategy.id}
                className={`bg-slate-800 border rounded-lg p-5 transition ${
                  selectedStrategies.has(strategy.id)
                    ? 'border-emerald-500 bg-slate-800/50'
                    : 'border-slate-700 hover:border-slate-600'
                }`}
              >
                {editingStrategy?.id === strategy.id ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Name</label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Description</label>
                      <textarea
                        value={editForm.description}
                        onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                        rows={2}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500 resize-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Code</label>
                      <textarea
                        value={editForm.logic_code}
                        onChange={(e) => setEditForm({ ...editForm, logic_code: e.target.value })}
                        rows={8}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-xs font-mono focus:outline-none focus:border-emerald-500 resize-none"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveEdit}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-sm font-medium flex items-center gap-2 transition"
                      >
                        <Save size={14} /> Save
                      </button>
                      <button
                        onClick={() => setEditingStrategy(null)}
                        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm font-medium flex items-center gap-2 transition"
                      >
                        <X size={14} /> Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <input
                          type="checkbox"
                          checked={selectedStrategies.has(strategy.id)}
                          onChange={() => handleSelectStrategy(strategy.id)}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold text-white text-lg">{strategy.name}</h3>
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-medium ${
                                strategy.is_active
                                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                  : 'bg-slate-700 text-slate-400 border border-slate-600'
                              }`}
                            >
                              {strategy.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          {strategy.description && (
                            <p className="text-slate-400 text-sm mb-3">{strategy.description}</p>
                          )}
                          <div className="text-xs text-slate-500 mb-3">
                            {strategy.created_at && (
                              <span>Created: {new Date(strategy.created_at).toLocaleDateString()}</span>
                            )}
                          </div>
                          <div className="bg-slate-950 border border-slate-700 rounded p-3 mb-3">
                            <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
                              <Code size={12} />
                              <span>Strategy Code</span>
                            </div>
                            <pre className="text-xs text-slate-300 font-mono overflow-x-auto max-h-32 overflow-y-auto">
                              {strategy.logic_code.substring(0, 300)}
                              {strategy.logic_code.length > 300 && '...'}
                            </pre>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-700">
                      <button
                        onClick={() => handleToggleActive(strategy.id, strategy.is_active)}
                        className={`px-3 py-1.5 rounded text-sm font-medium flex items-center gap-2 transition ${
                          strategy.is_active
                            ? 'bg-slate-700 hover:bg-slate-600 text-white'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                        }`}
                      >
                        {strategy.is_active ? (
                          <>
                            <PowerOff size={14} /> Deactivate
                          </>
                        ) : (
                          <>
                            <Power size={14} /> Activate
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => handleEdit(strategy)}
                        className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm font-medium flex items-center gap-2 transition"
                      >
                        <Edit size={14} /> Edit
                      </button>
                      <button
                        onClick={() => handleDelete(strategy.id)}
                        className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-600/30 rounded text-sm font-medium flex items-center gap-2 transition"
                      >
                        <Trash2 size={14} /> Delete
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default StrategyManager;

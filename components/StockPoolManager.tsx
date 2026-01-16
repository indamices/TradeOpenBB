import React, { useState, useEffect } from 'react';
import { 
  Plus, Edit2, Trash2, Search, X, Save, Loader2, 
  List, Grid, Check, AlertCircle 
} from 'lucide-react';
import { StockPool, StockInfo, StockPoolCreate, StockPoolUpdate } from '../types';
import { stockPoolService } from '../services/stockPoolService';

interface StockPoolManagerProps {
  selectedPoolId: number | null;
  onSelectPool: (poolId: number | null, symbols: string[]) => void;
  mode?: 'selector' | 'manager'; // 'selector' for selecting pool, 'manager' for full management
}

const StockPoolManager: React.FC<StockPoolManagerProps> = ({
  selectedPoolId,
  onSelectPool,
  mode = 'selector',
}) => {
  const [pools, setPools] = useState<StockPool[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  
  // Pool management states
  const [editingPool, setEditingPool] = useState<StockPool | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newPoolName, setNewPoolName] = useState('');
  const [newPoolDescription, setNewPoolDescription] = useState('');
  const [newPoolSymbols, setNewPoolSymbols] = useState<string[]>([]);
  
  // Stock search states
  const [stockSearchQuery, setStockSearchQuery] = useState('');
  const [stockSearchResults, setStockSearchResults] = useState<StockInfo[]>([]);
  const [stockSearchLoading, setStockSearchLoading] = useState(false);
  const [selectedMarketType, setSelectedMarketType] = useState<string>(''); // 'US', 'HK', 'CN', or '' for all

  useEffect(() => {
    loadPools();
  }, []);

  const loadPools = async () => {
    try {
      setLoading(true);
      const data = await stockPoolService.getStockPools();
      setPools(data);
    } catch (error) {
      console.error('Failed to load stock pools:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchStocks = async (query: string) => {
    if (!query || query.length < 1) {
      setStockSearchResults([]);
      return;
    }

    try {
      setStockSearchLoading(true);
      const results = await stockPoolService.searchStocks(query, 20, selectedMarketType || undefined);
      setStockSearchResults(results);
    } catch (error) {
      console.error('Failed to search stocks:', error);
      setStockSearchResults([]);
    } finally {
      setStockSearchLoading(false);
    }
  };

  const handleAddSymbol = (symbol: string) => {
    if (!newPoolSymbols.includes(symbol)) {
      setNewPoolSymbols([...newPoolSymbols, symbol]);
    }
    setStockSearchQuery('');
    setStockSearchResults([]);
  };

  const handleRemoveSymbol = (symbol: string) => {
    setNewPoolSymbols(newPoolSymbols.filter(s => s !== symbol));
  };

  const handleCreatePool = async () => {
    if (!newPoolName.trim() || newPoolSymbols.length === 0) {
      return;
    }

    try {
      const poolData: StockPoolCreate = {
        name: newPoolName.trim(),
        description: newPoolDescription.trim() || undefined,
        symbols: newPoolSymbols,
      };
      
      const created = await stockPoolService.createStockPool(poolData);
      setPools([...pools, created]);
      
      // Reset form
      setIsCreating(false);
      setNewPoolName('');
      setNewPoolDescription('');
      setNewPoolSymbols([]);
      
      // Select the new pool
      onSelectPool(created.id, created.symbols);
    } catch (error) {
      console.error('Failed to create pool:', error);
    }
  };

  const handleUpdatePool = async () => {
    if (!editingPool) return;

    try {
      const poolData: StockPoolUpdate = {
        name: newPoolName.trim(),
        description: newPoolDescription.trim() || undefined,
        symbols: newPoolSymbols,
      };
      
      const updated = await stockPoolService.updateStockPool(editingPool.id, poolData);
      setPools(pools.map(p => p.id === updated.id ? updated : p));
      
      // Reset form
      setEditingPool(null);
      setIsCreating(false);
      setNewPoolName('');
      setNewPoolDescription('');
      setNewPoolSymbols([]);
      
      // Update selection if this was the selected pool
      if (selectedPoolId === updated.id) {
        onSelectPool(updated.id, updated.symbols);
      }
    } catch (error) {
      console.error('Failed to update pool:', error);
    }
  };

  const handleDeletePool = async (id: number) => {
    if (!confirm('Are you sure you want to delete this stock pool?')) {
      return;
    }

    try {
      await stockPoolService.deleteStockPool(id);
      setPools(pools.filter(p => p.id !== id));
      
      // Clear selection if deleted pool was selected
      if (selectedPoolId === id) {
        onSelectPool(null, []);
      }
    } catch (error) {
      console.error('Failed to delete pool:', error);
    }
  };

  const handleEditPool = (pool: StockPool) => {
    setEditingPool(pool);
    setIsCreating(false);
    setNewPoolName(pool.name);
    setNewPoolDescription(pool.description || '');
    setNewPoolSymbols([...pool.symbols]);
  };

  const handleStartCreating = () => {
    setIsCreating(true);
    setEditingPool(null);
    setNewPoolName('');
    setNewPoolDescription('');
    setNewPoolSymbols([]);
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingPool(null);
    setNewPoolName('');
    setNewPoolDescription('');
    setNewPoolSymbols([]);
  };

  const filteredPools = pools.filter(pool =>
    pool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    pool.symbols.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Stock Pools
        </h3>
        {mode === 'manager' && (
          <button
            onClick={handleStartCreating}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Pool
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search pools or symbols..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Pool creation/edit form */}
      {(isCreating || editingPool) && (
        <div className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
          <h4 className="font-semibold mb-3 text-gray-900 dark:text-gray-100">
            {editingPool ? 'Edit Pool' : 'Create New Pool'}
          </h4>
          
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Pool name"
              value={newPoolName}
              onChange={(e) => setNewPoolName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            
            <textarea
              placeholder="Description (optional)"
              value={newPoolDescription}
              onChange={(e) => setNewPoolDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            
            {/* Stock search */}
            <div className="space-y-2">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search stocks to add..."
                    value={stockSearchQuery}
                    onChange={(e) => {
                      setStockSearchQuery(e.target.value);
                      handleSearchStocks(e.target.value);
                    }}
                    className="w-full pl-9 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  />
                  {stockSearchLoading && (
                    <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
                  )}
                </div>
                <select
                  value={selectedMarketType}
                  onChange={(e) => {
                    setSelectedMarketType(e.target.value);
                    if (stockSearchQuery) {
                      handleSearchStocks(stockSearchQuery);
                    }
                  }}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">All Markets</option>
                  <option value="US">US Stocks</option>
                  <option value="HK">HK Stocks</option>
                  <option value="CN">A股 (CN)</option>
                </select>
              </div>
              
              {/* Search results */}
              {stockSearchResults.length > 0 && (
                <div className="max-h-48 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700">
                  {stockSearchResults.map((stock) => (
                    <button
                      key={stock.symbol}
                      onClick={() => handleAddSymbol(stock.symbol)}
                      disabled={newPoolSymbols.includes(stock.symbol)}
                      className="w-full px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-between"
                    >
                      <div>
                        <div className="font-medium text-gray-900 dark:text-gray-100">{stock.symbol}</div>
                        {stock.name && (
                          <div className="text-sm text-gray-600 dark:text-gray-400">{stock.name}</div>
                        )}
                      </div>
                      {newPoolSymbols.includes(stock.symbol) && (
                        <Check className="w-4 h-4 text-green-500" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            {/* Selected symbols */}
            {newPoolSymbols.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {newPoolSymbols.map((symbol) => (
                  <span
                    key={symbol}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm"
                  >
                    {symbol}
                    <button
                      onClick={() => handleRemoveSymbol(symbol)}
                      className="hover:text-blue-600 dark:hover:text-blue-300"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
            
            {newPoolSymbols.length === 0 && (
              <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400 text-sm">
                <AlertCircle className="w-4 h-4" />
                <span>Add at least one stock symbol</span>
              </div>
            )}
            
            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={editingPool ? handleUpdatePool : handleCreatePool}
                disabled={!newPoolName.trim() || newPoolSymbols.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save className="w-4 h-4" />
                {editingPool ? 'Update' : 'Create'}
              </button>
              <button
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pool list */}
      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : filteredPools.length === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          {searchQuery ? 'No pools found' : 'No stock pools yet. Create one to get started.'}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredPools.map((pool) => (
            <div
              key={pool.id}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                selectedPoolId === pool.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
              onClick={() => onSelectPool(pool.id, pool.symbols)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">{pool.name}</h4>
                    {selectedPoolId === pool.id && (
                      <Check className="w-4 h-4 text-blue-500" />
                    )}
                  </div>
                  {pool.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{pool.description}</p>
                  )}
                  <div className="flex flex-wrap gap-1">
                    {pool.symbols.slice(0, 10).map((symbol) => (
                      <span
                        key={symbol}
                        className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs"
                      >
                        {symbol}
                      </span>
                    ))}
                    {pool.symbols.length > 10 && (
                      <span className="px-2 py-1 text-gray-500 dark:text-gray-400 text-xs">
                        +{pool.symbols.length - 10} more
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    {pool.symbols.length} symbol{pool.symbols.length !== 1 ? 's' : ''}
                  </div>
                </div>
                {mode === 'manager' && (
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditPool(pool);
                      }}
                      className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeletePool(pool.id);
                      }}
                      className="p-2 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StockPoolManager;

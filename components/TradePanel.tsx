import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { MarketQuote, Order } from '../types';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';

const TradePanel: React.FC = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [quote, setQuote] = useState<MarketQuote | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [limitPrice, setLimitPrice] = useState(0);
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [loading, setLoading] = useState(false);
  const [orderHistory, setOrderHistory] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchQuote = async () => {
    setLoading(true);
    setError(null);
    try {
      const q = await tradingService.getQuote(symbol);
      setQuote(q);
      if(orderType === 'LIMIT' && limitPrice === 0) setLimitPrice(q.price);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to fetch quote');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrders = async () => {
    try {
      const orders = await tradingService.getOrders();
      setOrderHistory(orders);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
    }
  };

  useEffect(() => {
    fetchQuote();
    fetchOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    try {
      if(!quote) throw new Error("Please fetch a quote first");
      
      await tradingService.placeOrder({
        portfolio_id: 1,
        symbol: quote.symbol,
        side,
        type: orderType,
        quantity,
        limit_price: orderType === 'LIMIT' ? limitPrice : undefined
      });

      setSuccess(`Order Placed: ${side} ${quantity} ${quote.symbol}`);
      fetchOrders(); // Refresh table
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to place order");
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Order Entry */}
      <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">Place Order</h2>
        
        {/* Quote Section */}
        <div className="mb-6 bg-slate-800/50 p-4 rounded-lg">
          <div className="flex gap-2 mb-2">
            <input 
              type="text" 
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white w-full focus:outline-none focus:border-emerald-500"
              placeholder="Symbol"
            />
            <button onClick={fetchQuote} className="bg-slate-700 hover:bg-slate-600 p-2 rounded text-white transition">
              <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
            </button>
          </div>
          {quote && (
            <div className="flex justify-between items-end">
              <div>
                <div className="text-2xl font-bold text-white">${quote.price.toFixed(2)}</div>
                <div className={`text-sm ${quote.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {quote.change} ({quote.change_percent}%)
                </div>
              </div>
              <div className="text-xs text-slate-500">Vol: {(quote.volume/1000000).toFixed(2)}M</div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              type="button"
              className={`flex-1 py-2 rounded text-sm font-medium transition ${side === 'BUY' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'}`}
              onClick={() => setSide('BUY')}
            >
              Buy
            </button>
            <button
              type="button"
              className={`flex-1 py-2 rounded text-sm font-medium transition ${side === 'SELL' ? 'bg-red-600 text-white' : 'text-slate-400 hover:text-white'}`}
              onClick={() => setSide('SELL')}
            >
              Sell
            </button>
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-xs text-slate-500 mb-1">Quantity</label>
              <input 
                type="number" 
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-slate-500 mb-1">Order Type</label>
              <select
                value={orderType}
                onChange={(e) => setOrderType(e.target.value as 'MARKET' | 'LIMIT')}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
              >
                <option value="MARKET">Market</option>
                <option value="LIMIT">Limit</option>
              </select>
            </div>
          </div>

          {orderType === 'LIMIT' && (
             <div>
               <label className="block text-xs text-slate-500 mb-1">Limit Price</label>
               <input 
                 type="number" 
                 step="0.01"
                 value={limitPrice}
                 onChange={(e) => setLimitPrice(parseFloat(e.target.value))}
                 className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
               />
             </div>
          )}

          <div className="pt-2">
            <div className="flex justify-between text-sm text-slate-400 mb-4">
               <span>Est. Total</span>
               <span className="text-white font-bold">
                 ${((orderType === 'LIMIT' ? limitPrice : (quote?.price || 0)) * quantity).toLocaleString()}
               </span>
            </div>
            
            <button 
              type="submit"
              className={`w-full py-3 rounded-lg font-bold text-white transition shadow-lg
                ${side === 'BUY' ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-900/20' : 'bg-red-600 hover:bg-red-500 shadow-red-900/20'}
              `}
            >
              {side} {symbol}
            </button>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm flex items-center">
              <AlertCircle size={16} className="mr-2" />
              {error}
            </div>
          )}
           {success && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded text-emerald-400 text-sm flex items-center">
              <CheckCircle size={16} className="mr-2" />
              {success}
            </div>
          )}
        </form>
      </div>

      {/* Order Blotter */}
      <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-slate-800">
            <h3 className="text-lg font-semibold text-slate-200">Order History (Simulated)</h3>
        </div>
        <div className="overflow-auto flex-1">
            <table className="w-full text-left text-sm">
                <thead className="bg-slate-800/50 text-slate-400 uppercase font-medium">
                    <tr>
                        <th className="px-6 py-3">Time</th>
                        <th className="px-6 py-3">Symbol</th>
                        <th className="px-6 py-3">Side</th>
                        <th className="px-6 py-3">Type</th>
                        <th className="px-6 py-3">Price</th>
                        <th className="px-6 py-3">Qty</th>
                        <th className="px-6 py-3">Status</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                    {orderHistory.map(order => (
                        <tr key={order.id} className="hover:bg-slate-800/30">
                            <td className="px-6 py-3 text-slate-400">{new Date(order.created_at).toLocaleTimeString()}</td>
                            <td className="px-6 py-3 font-bold text-white">{order.symbol}</td>
                            <td className={`px-6 py-3 font-medium ${order.side === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>{order.side}</td>
                            <td className="px-6 py-3 text-slate-300">{order.type}</td>
                            <td className="px-6 py-3 text-slate-300">${(order.avg_fill_price || order.limit_price || 0).toFixed(2)}</td>
                            <td className="px-6 py-3 text-slate-300">{order.quantity}</td>
                            <td className="px-6 py-3">
                                <span className="px-2 py-1 rounded text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                    {order.status}
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
      </div>
    </div>
  );
};

export default TradePanel;

import { Portfolio, Position, Order, Strategy, MarketQuote } from '../types';

// Initial Mock Data
let PORTFOLIO: Portfolio = {
  id: 1,
  name: "Main Aggressive Fund",
  initial_cash: 100000,
  current_cash: 65420.50,
  total_value: 102350.75,
  created_at: new Date().toISOString(),
  daily_pnl: 1250.40,
  daily_pnl_percent: 1.23
};

let POSITIONS: Position[] = [
  {
    id: 1,
    portfolio_id: 1,
    symbol: "AAPL",
    quantity: 150,
    avg_price: 175.50,
    current_price: 182.30,
    market_value: 27345.00,
    unrealized_pnl: 1020.00,
    unrealized_pnl_percent: 3.87
  },
  {
    id: 2,
    portfolio_id: 1,
    symbol: "NVDA",
    quantity: 20,
    avg_price: 450.00,
    current_price: 479.25,
    market_value: 9585.00,
    unrealized_pnl: 585.00,
    unrealized_pnl_percent: 6.5
  }
];

let ORDERS: Order[] = [
  {
    id: 101,
    portfolio_id: 1,
    symbol: "TSLA",
    side: "BUY",
    type: "LIMIT",
    quantity: 10,
    limit_price: 210.00,
    status: "FILLED",
    avg_fill_price: 209.50,
    commission: 1.05,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    filled_at: new Date(Date.now() - 86300000).toISOString(),
  }
];

let STRATEGIES: Strategy[] = [
  {
    id: 1,
    name: "Golden Cross v1",
    is_active: true,
    target_portfolio_id: 1,
    logic_code: "def strategy(df):\n  return df['MA50'] > df['MA200']",
    description: "Classic Moving Average Crossover"
  }
];

// Simulation Service
export const MockService = {
  getPortfolio: async (): Promise<Portfolio> => {
    return new Promise(resolve => setTimeout(() => resolve({...PORTFOLIO}), 300));
  },

  getPositions: async (): Promise<Position[]> => {
    return new Promise(resolve => setTimeout(() => resolve([...POSITIONS]), 300));
  },

  getOrders: async (): Promise<Order[]> => {
    return new Promise(resolve => setTimeout(() => resolve([...ORDERS]), 300));
  },

  getStrategies: async (): Promise<Strategy[]> => {
    return new Promise(resolve => setTimeout(() => resolve([...STRATEGIES]), 300));
  },

  saveStrategy: async (strategy: Omit<Strategy, 'id'>): Promise<Strategy> => {
    const newStrategy = { ...strategy, id: STRATEGIES.length + 1 };
    STRATEGIES.push(newStrategy);
    return newStrategy;
  },

  placeOrder: async (orderRequest: Omit<Order, 'id' | 'status' | 'created_at' | 'commission'>): Promise<Order> => {
    // Simulate simple execution logic
    const price = orderRequest.type === 'MARKET' ? 
      (await MockService.getQuote(orderRequest.symbol)).price : 
      orderRequest.limit_price || 0;
    
    const totalCost = price * orderRequest.quantity;
    const commission = Math.max(1, totalCost * 0.0003); // Min $1 or 3bps

    // Update Cash (Simplified)
    if (orderRequest.side === 'BUY') {
        if (PORTFOLIO.current_cash < totalCost) throw new Error("Insufficient Funds");
        PORTFOLIO.current_cash -= (totalCost + commission);
        
        // Update Position
        const existingPos = POSITIONS.find(p => p.symbol === orderRequest.symbol);
        if (existingPos) {
            const newQty = existingPos.quantity + orderRequest.quantity;
            const totalVal = (existingPos.avg_price * existingPos.quantity) + totalCost;
            existingPos.quantity = newQty;
            existingPos.avg_price = totalVal / newQty;
        } else {
            POSITIONS.push({
                id: POSITIONS.length + 1,
                portfolio_id: 1,
                symbol: orderRequest.symbol,
                quantity: orderRequest.quantity,
                avg_price: price,
                current_price: price,
                market_value: totalCost,
                unrealized_pnl: 0,
                unrealized_pnl_percent: 0
            });
        }
    } else {
         // Sell logic omitted for brevity in demo, but would check qty
         PORTFOLIO.current_cash += (totalCost - commission);
         const existingPos = POSITIONS.find(p => p.symbol === orderRequest.symbol);
         if(existingPos) {
             existingPos.quantity -= orderRequest.quantity;
             if(existingPos.quantity <= 0) {
                 POSITIONS = POSITIONS.filter(p => p.symbol !== orderRequest.symbol);
             }
         }
    }

    const newOrder: Order = {
      id: ORDERS.length + 100,
      ...orderRequest,
      status: 'FILLED', // Auto-fill for demo
      avg_fill_price: price,
      commission,
      created_at: new Date().toISOString(),
      filled_at: new Date().toISOString()
    };
    
    ORDERS.unshift(newOrder); // Add to top
    return newOrder;
  },

  getQuote: async (symbol: string): Promise<MarketQuote> => {
    // Generate semi-random quote
    const basePrice = Math.random() * 200 + 50;
    return {
      symbol: symbol.toUpperCase(),
      price: parseFloat(basePrice.toFixed(2)),
      change: parseFloat((Math.random() * 10 - 5).toFixed(2)),
      change_percent: parseFloat((Math.random() * 5 - 2.5).toFixed(2)),
      volume: Math.floor(Math.random() * 1000000),
      last_updated: new Date().toISOString()
    };
  }
};

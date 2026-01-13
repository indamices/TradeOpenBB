// Data Models matching the SQL Schema provided

export interface Portfolio {
  id: number;
  name: string;
  initial_cash: number;
  current_cash: number;
  total_value: number;
  created_at: string;
  daily_pnl: number;
  daily_pnl_percent: number;
}

export interface Position {
  id: number;
  portfolio_id: number;
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

export interface Order {
  id: number;
  portfolio_id: number;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT';
  quantity: number;
  limit_price?: number;
  avg_fill_price?: number;
  status: 'PENDING' | 'FILLED' | 'CANCELLED';
  commission: number;
  created_at: string;
  filled_at?: string;
}

export interface Strategy {
  id: number;
  name: string;
  logic_code: string;
  is_active: boolean;
  target_portfolio_id: number;
  description?: string;
}

export interface MarketQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  last_updated: string;
}

// AI Service Types
export interface StrategyGenerationRequest {
  prompt: string;
  model_id?: number;
}

export interface StrategyGenerationResponse {
  code: string;
  explanation: string;
}

// Backtest Types
export interface BacktestRequest {
  strategy_id: number;
  start_date: string;
  end_date: string;
  initial_cash: number;
  symbols: string[];
}

export interface BacktestResult {
  sharpe_ratio: number;
  sortino_ratio?: number;
  annualized_return: number;
  max_drawdown: number;
  win_rate?: number;
  total_trades: number;
  total_return: number;
}

// AI Model Config Types
export type AIProvider = 'gemini' | 'openai' | 'claude' | 'custom';

export interface AIModelConfig {
  id: number;
  name: string;
  provider: AIProvider;
  model_name: string;
  base_url?: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AIModelConfigCreate {
  name: string;
  provider: AIProvider;
  api_key: string;
  model_name: string;
  base_url?: string;
}

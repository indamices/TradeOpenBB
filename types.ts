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
  // Time series data
  equity_curve?: Array<{date: string, value: number}>;
  drawdown_series?: Array<{date: string, drawdown: number}>;
  trades?: Array<{
    date: string;
    symbol: string;
    side: 'BUY' | 'SELL';
    price: number;
    quantity: number;
    commission?: number;
  }>;
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

// AI Chat Types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  code_snippets?: { [key: string]: string };
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  context?: {
    strategy_id?: number;
    backtest_result_id?: number;
  };
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  suggestions?: string[];
  code_snippets?: {[key: string]: string};
}

export interface ChatConversation {
  conversation_id: string;
  messages: ChatMessage[];
}

// Stock Pool Types
export interface StockPool {
  id: number;
  name: string;
  description?: string;
  symbols: string[];
  created_at: string;
  updated_at?: string;
}

export interface StockPoolCreate {
  name: string;
  description?: string;
  symbols: string[];
}

export interface StockPoolUpdate {
  name?: string;
  description?: string;
  symbols?: string[];
}

// Stock Info Types
export interface StockInfo {
  symbol: string;
  name?: string;
  exchange?: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  pe_ratio?: number;
  updated_at?: string;
}

// Time Range Types
export interface TimeRange {
  start: string;
  end: string;
  label?: string;
}

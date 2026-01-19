/**
 * 扩展的 TypeScript 类型定义
 * 补充 types.ts 中缺失的类型定义
 */

// ==================== API 响应类型 ====================

/**
 * 通用 API 响应包装
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

/**
 * API 错误详细类型（扩展 ApiError）
 */
export interface ExtendedApiError {
  detail: string;
  status?: number;
  code?: string;
  fields?: Record<string, string[]>;
  stack?: string;
}

// ==================== 技术指标类型 ====================

/**
 * 技术指标数据点
 */
export interface TechnicalIndicatorDataPoint {
  date: string;
  [key: string]: string | number | undefined;
}

/**
 * 技术指标类型
 */
export type TechnicalIndicatorType =
  | 'SMA'      // 简单移动平均
  | 'EMA'      // 指数移动平均
  | 'RSI'      // 相对强弱指标
  | 'MACD'     // 移动平均收敛散度
  | 'BOLL'     // 布林带
  | 'STOCH'    // 随机指标
  | 'ADX'      // 平均趋向指标
  | 'CCI'      // 顺势指标
  | 'ATR'      // 真实波幅
  | 'VWAP';    // 成交量加权平均价

/**
 * 技术指标参数
 */
export interface TechnicalIndicatorParams {
  indicator: TechnicalIndicatorType;
  period?: number;
  params?: Record<string, number | string>;
}

/**
 * 技术指标响应
 */
export interface TechnicalIndicatorResponse {
  symbol: string;
  indicator: TechnicalIndicatorType;
  data: TechnicalIndicatorDataPoint[];
  period: number;
  calculatedAt: string;
}

// ==================== 市场数据类型 ====================

/**
 * 市场概览数据
 */
export interface MarketOverview {
  total_stocks?: number;
  advances?: number;
  declines?: number;
  unchanged?: number;
  total_volume_usd?: number;
  market_cap?: number;
  market_status?: 'open' | 'closed' | 'pre_market' | 'after_hours';
  last_updated: string;
}

/**
 * 历史数据点
 */
export interface HistoricalDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjusted_close?: number;
}

/**
 * 实时报价（扩展 MarketQuote）
 */
export interface ExtendedMarketQuote extends MarketQuote {
  bid?: number;
  ask?: number;
  bid_size?: number;
  ask_size?: number;
  day_high?: number;
  day_low?: number;
  week_52_high?: number;
  week_52_low?: number;
  market_cap?: number;
  pe_ratio?: number;
  dividend_yield?: number;
}

// ==================== 回测扩展类型 ====================

/**
 * 回测配置选项
 */
export interface BacktestConfigOptions {
  slippage?: number;          // 滑点百分比
  commission?: number;        // 佣金率
  commission_per_share?: number; // 每股佣金
  initial_cash?: number;      // 初始资金
  position_size?: number;     // 仓位大小
  stop_loss?: number;         // 止损百分比
  take_profit?: number;       // 止盈百分比
  max_positions?: number;     // 最大持仓数
}

/**
 * 回测统计指标（扩展 BacktestResult）
 */
export interface BacktestStatistics {
  // 收益指标
  total_return: number;
  annualized_return: number;
  daily_return_mean: number;
  daily_return_std: number;

  // 风险指标
  max_drawdown: number;
  max_drawdown_duration: number;  // 天数
  sharpe_ratio: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  omega_ratio?: number;

  // 交易指标
  total_trades: number;
  win_rate?: number;
  profit_factor?: number;
  avg_win?: number;
  avg_loss?: number;
  best_trade?: number;
  worst_trade?: number;

  // 其他指标
  beta?: number;
  alpha?: number;
  r_squared?: number;
}

/**
 * 交易详情（扩展 BacktestResult.trades）
 */
export interface TradeDetail {
  date: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  commission?: number;
  slippage?: number;
  trigger_reason?: string;
  pnl?: number;
  pnl_percent?: number;
  bars_held?: number;  // 持有天数
  entry_date?: string;
  exit_date?: string;
}

// ==================== AI 分析类型 ====================

/**
 * AI 分析请求（扩展 AIStrategyAnalysisRequest）
 */
export interface ExtendedAIAnalysisRequest {
  backtest_result: BacktestResult;
  strategy_id: number;
  analysis_type?: 'performance' | 'risk' | 'optimization' | 'comprehensive';
  focus_areas?: string[];
}

/**
 * AI 分析响应（扩展 AIStrategyAnalysisResponse）
 */
export interface ExtendedAIAnalysisResponse {
  analysis_summary: string;
  strengths: string[];
  weaknesses: string[];
  optimization_suggestions: string[];
  risk_assessment?: {
    level: 'low' | 'medium' | 'high' | 'very_high';
    factors: string[];
  };
  performance_rating?: {
    score: number;  // 0-100
    category: 'excellent' | 'good' | 'average' | 'poor';
    comparison?: string;  // 与基准比较
  };
  recommended_changes?: Array<{
    parameter: string;
    current_value: any;
    suggested_value: any;
    reason: string;
  }>;
  raw_ai_response?: string;
}

// ==================== 策略类型 ====================

/**
 * 策略参数类型
 */
export interface StrategyParameter {
  name: string;
  type: 'number' | 'string' | 'boolean' | 'array';
  value: any;
  default_value?: any;
  min_value?: number;
  max_value?: number;
  step?: number;
  options?: any[];
  description?: string;
}

/**
 * 策略元数据
 */
export interface StrategyMetadata {
  id: number;
  name: string;
  description?: string;
  category?: string;  // 如 'trend_following', 'mean_reversion'
  risk_level?: 'low' | 'medium' | 'high';
  time_frame?: string;  // 如 '1h', '1d'
  parameters: StrategyParameter[];
  created_at: string;
  updated_at?: string;
  backtest_count?: number;
  avg_return?: number;
  avg_sharpe?: number;
}

// ==================== 错误处理类型 ====================

/**
 * 错误级别
 */
export type ErrorLevel = 'info' | 'warning' | 'error' | 'critical';

/**
 * 应用错误
 */
export interface AppError {
  id: string;
  level: ErrorLevel;
  code: string;
  message: string;
  details?: string;
  timestamp: string;
  context?: Record<string, any>;
  user_action?: string;  // 建议用户采取的操作
}

/**
 * 错误边界状态
 */
export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

// ==================== UI 状态类型 ====================

/**
 * 加载状态
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * 异步操作状态
 */
export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

/**
 * 分页状态
 */
export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
  hasMore: boolean;
}

// ==================== 表单类型 ====================

/**
 * 表单验证规则
 */
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: RegExp;
  custom?: (value: any) => boolean | string;
}

/**
 * 表单字段状态
 */
export interface FormField<T = any> {
  value: T;
  error: string | null;
  touched: boolean;
  dirty: boolean;
}

/**
 * 表单状态
 */
export interface FormState<T extends Record<string, any>> {
  fields: { [K in keyof T]: FormField<T[K]> };
  valid: boolean;
  submitting: boolean;
}

// ==================== 通知类型 ====================

/**
 * 通知类型
 */
export type NotificationType = 'success' | 'info' | 'warning' | 'error';

/**
 * 通知消息
 */
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number;  // 自动关闭时间（毫秒）
  timestamp: Date;
  actions?: Array<{
    label: string;
    onClick: () => void;
  }>;
}

// ==================== 图表类型 ====================

/**
 * 图表数据系列
 */
export interface ChartSeries {
  name: string;
  data: Array<{ x: string | number; y: number }>;
  color?: string;
  type?: 'line' | 'area' | 'bar' | 'scatter';
}

/**
 * 图表配置
 */
export interface ChartConfig {
  title?: string;
  xAxis?: string;
  yAxis?: string;
  series: ChartSeries[];
  legend?: boolean;
  grid?: boolean;
  tooltip?: boolean;
}

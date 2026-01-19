/**
 * API 响应类型定义
 * 用于 services 层的类型安全
 */

import { ApiError } from './apiClient';

// ==================== 技术指标类型 ====================

/**
 * 技术指标数据点
 */
export interface TechnicalIndicatorDataPoint {
  date: string;
  [key: string]: string | number | undefined;
}

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
 * 扩展的市场报价
 */
export interface ExtendedMarketQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  last_updated: string;
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

// ==================== 服务层增强 ====================

/**
 * 带重试配置的请求选项
 */
export interface RequestOptions {
  maxRetries?: number;
  retryDelay?: number;
  timeout?: number;
  signal?: AbortSignal;
}

/**
 * 服务响应包装
 */
export interface ServiceResponse<T> {
  data: T;
  status: number;
  message?: string;
  timestamp: string;
}

/**
 * 分页请求参数
 */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
  offset?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
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

// ==================== 错误处理增强 ====================

/**
 * 扩展的 API 错误
 */
export interface ExtendedApiError extends ApiError {
  code?: string;
  fields?: Record<string, string[]>;
  stack?: string;
  timestamp?: string;
  requestId?: string;
}

/**
 * 错误响应
 */
export interface ErrorResponse {
  detail: string;
  code?: string;
  fields?: Record<string, string[]>;
  status: number;
}

// ==================== 请求/响应包装 ====================

/**
 * 成功响应
 */
export interface SuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
}

/**
 * 错误响应
 */
export interface ErrorResponseWrapper {
  success: false;
  error: {
    message: string;
    code?: string;
    details?: any;
  };
}

/**
 * 统一 API 响应类型
 */
export type ApiResponse<T> = SuccessResponse<T> | ErrorResponseWrapper;

// ==================== 批量操作类型 ====================

/**
 * 批量操作请求
 */
export interface BatchOperationRequest<T> {
  items: T[];
  operation: 'create' | 'update' | 'delete';
}

/**
 * 批量操作响应
 */
export interface BatchOperationResponse {
  succeeded: number;
  failed: number;
  errors: Array<{
    index: number;
    error: string;
  }>;
}

// ==================== 搜索和过滤类型 ====================

/**
 * 搜索参数
 */
export interface SearchParams {
  query: string;
  filters?: Record<string, any>;
  page?: number;
  pageSize?: number;
}

/**
 * 搜索结果
 */
export interface SearchResult<T> {
  items: T[];
  total: number;
  query: string;
  suggestions?: string[];
}

// ==================== 导出类型 ====================

/**
 * 导出格式
 */
export type ExportFormat = 'csv' | 'excel' | 'json' | 'pdf';

/**
 * 导出请求
 */
export interface ExportRequest {
  format: ExportFormat;
  filters?: Record<string, any>;
  columns?: string[];
  startDate?: string;
  endDate?: string;
}

/**
 * 导出响应
 */
export interface ExportResponse {
  url: string;
  filename: string;
  format: ExportFormat;
  size: number;
  expiresAt: string;
}

// ==================== 实时数据类型 ====================

/**
 * WebSocket 消息类型
 */
export type WebSocketMessageType =
  | 'quote'
  | 'trade'
  | 'order_update'
  | 'position_update'
  | 'error'
  | 'heartbeat';

/**
 * WebSocket 消息
 */
export interface WebSocketMessage<T = any> {
  type: WebSocketMessageType;
  data: T;
  timestamp: string;
  sequence?: number;
}

/**
 * 实时报价更新
 */
export interface QuoteUpdate {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

/**
 * 实时交易更新
 */
export interface TradeUpdate {
  symbol: string;
  price: number;
  size: number;
  timestamp: string;
}

// ==================== 缓存类型 ====================

/**
 * 缓存策略
 */
export type CacheStrategy = 'no-cache' | 'memory' | 'localStorage' | 'sessionStorage';

/**
 * 缓存配置
 */
export interface CacheConfig {
  strategy: CacheStrategy;
  ttl?: number; // 过期时间（毫秒）
  maxSize?: number; // 最大缓存条目数
}

/**
 * 缓存条目
 */
export interface CacheEntry<T> {
  key: string;
  value: T;
  timestamp: number;
  ttl?: number;
}

// ==================== 认证类型 ====================

/**
 * 认证令牌响应
 */
export interface AuthTokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

/**
 * 用户信息
 */
export interface UserInfo {
  id: number;
  username: string;
  email: string;
  roles: string[];
  permissions: string[];
}

// ==================== 统计类型 ====================

/**
 * 时间范围
 */
export type TimeRange = '1d' | '1w' | '1m' | '3m' | '6m' | '1y' | 'ytd' | 'max';

/**
 * 统计指标
 */
export interface MetricData {
  timestamp: string;
  value: number;
  label?: string;
}

/**
 * 统计汇总
 */
export interface StatisticsSummary {
  total: number;
  average: number;
  min: number;
  max: number;
  count: number;
}

// ==================== 通知类型 ====================

/**
 * 通知级别
 */
export type NotificationLevel = 'info' | 'success' | 'warning' | 'error';

/**
 * 系统通知
 */
export interface SystemNotification {
  id: string;
  level: NotificationLevel;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
}

// ==================== 类型守卫 ====================

/**
 * 检查是否为成功响应
 */
export function isSuccessResponse<T>(response: ApiResponse<T>): response is SuccessResponse<T> {
  return (response as SuccessResponse<T>).success === true;
}

/**
 * 检查是否为错误响应
 */
export function isErrorResponse<T>(response: ApiResponse<T>): response is ErrorResponseWrapper {
  return (response as ErrorResponseWrapper).success === false;
}

/**
 * 提取错误消息
 */
export function getErrorMessage(error: unknown): string {
  if (typeof error === 'string') {
    return error;
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (error && typeof error === 'object' && 'detail' in error) {
    return String(error.detail);
  }

  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message);
  }

  return 'An unknown error occurred';
}

/**
 * 检查是否为网络错误
 */
export function isNetworkError(error: ApiError): boolean {
  return error.status === 0 || error.detail.includes('Network error');
}

/**
 * 检查是否为超时错误
 */
export function isTimeoutError(error: ApiError): boolean {
  return error.status === 408 || error.detail.includes('timeout');
}

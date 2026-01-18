import { apiClient, ApiError } from './apiClient';
import { Portfolio, Position, Order, Strategy, MarketQuote, StrategyGenerationRequest, StrategyGenerationResponse, BacktestRequest, BacktestResult, SetStrategyActiveRequest, BatchSetActiveRequest, StrategyUpdate, BacktestRecord, BacktestRecordCreate, BacktestRecordUpdate, ParameterOptimizationRequest, ParameterOptimizationResult, AIStrategyAnalysisRequest, AIStrategyAnalysisResponse } from '../types';

export class TradingService {
  // Portfolio methods
  async getPortfolio(portfolioId: number = 1): Promise<Portfolio> {
    const params = new URLSearchParams();
    params.append('portfolio_id', portfolioId.toString());
    return apiClient.get<Portfolio>(`/api/portfolio?${params.toString()}`);
  }

  async createPortfolio(name: string, initialCash: number): Promise<Portfolio> {
    return apiClient.post<Portfolio>('/api/portfolio', {
      name,
      initial_cash: initialCash,
    });
  }

  async updatePortfolio(portfolioId: number, updates: Partial<Portfolio>): Promise<Portfolio> {
    return apiClient.put<Portfolio>(`/api/portfolio/${portfolioId}`, updates);
  }

  // Position methods
  async getPositions(portfolioId: number = 1): Promise<Position[]> {
    const params = new URLSearchParams();
    params.append('portfolio_id', portfolioId.toString());
    return apiClient.get<Position[]>(`/api/positions?${params.toString()}`);
  }

  async createPosition(position: Omit<Position, 'id' | 'created_at'>): Promise<Position> {
    return apiClient.post<Position>('/api/positions', position);
  }

  // Order methods
  async getOrders(portfolioId: number = 1): Promise<Order[]> {
    const params = new URLSearchParams();
    params.append('portfolio_id', portfolioId.toString());
    return apiClient.get<Order[]>(`/api/orders?${params.toString()}`);
  }

  async placeOrder(order: Omit<Order, 'id' | 'status' | 'created_at' | 'commission' | 'avg_fill_price' | 'filled_at'>): Promise<Order> {
    return apiClient.post<Order>('/api/orders', order);
  }

  // Strategy methods
  async getStrategies(portfolioId?: number, isActive?: boolean): Promise<Strategy[]> {
    const params = new URLSearchParams();
    if (portfolioId) {
      params.append('portfolio_id', portfolioId.toString());
    }
    if (isActive !== undefined) {
      params.append('is_active', isActive.toString());
    }
    const queryString = params.toString();
    const endpoint = queryString ? `/api/strategies?${queryString}` : '/api/strategies';
    return apiClient.get<Strategy[]>(endpoint);
  }

  async getActiveStrategies(portfolioId?: number): Promise<Strategy[]> {
    const params = new URLSearchParams();
    if (portfolioId) {
      params.append('portfolio_id', portfolioId.toString());
    }
    const queryString = params.toString();
    const endpoint = queryString ? `/api/strategies/active?${queryString}` : '/api/strategies/active';
    return apiClient.get<Strategy[]>(endpoint);
  }

  async saveStrategy(strategy: Omit<Strategy, 'id' | 'created_at' | 'updated_at'>): Promise<Strategy> {
    return apiClient.post<Strategy>('/api/strategies', strategy);
  }

  async updateStrategy(strategyId: number, updates: StrategyUpdate): Promise<Strategy> {
    return apiClient.put<Strategy>(`/api/strategies/${strategyId}`, updates);
  }

  async deleteStrategy(strategyId: number): Promise<void> {
    return apiClient.delete(`/api/strategies/${strategyId}`);
  }

  async setStrategyActive(strategyId: number, isActive: boolean): Promise<Strategy> {
    return apiClient.put<Strategy>(`/api/strategies/${strategyId}/set-active`, { is_active: isActive });
  }

  async toggleStrategyActive(strategyId: number): Promise<Strategy> {
    return apiClient.put<Strategy>(`/api/strategies/${strategyId}/toggle-active`, {});
  }

  async batchSetStrategyActive(strategyIds: number[], isActive: boolean): Promise<void> {
    return apiClient.put('/api/strategies/batch-set-active', {
      strategy_ids: strategyIds,
      is_active: isActive
    });
  }

  async generateStrategy(request: StrategyGenerationRequest): Promise<StrategyGenerationResponse> {
    return apiClient.post<StrategyGenerationResponse>('/api/strategies/generate', request);
  }

  // Market methods
  async getQuote(symbol: string): Promise<MarketQuote> {
    return apiClient.get<MarketQuote>(`/api/market/quote/${symbol}`);
  }

  async getMultipleQuotes(symbols: string[]): Promise<MarketQuote[]> {
    const params = new URLSearchParams();
    symbols.forEach(symbol => params.append('symbols', symbol));
    return apiClient.get<MarketQuote[]>(`/api/market/quotes?${params.toString()}`);
  }

  async getTechnicalIndicators(symbol: string, indicators: string[], period: number = 20): Promise<any[]> {
    const params = new URLSearchParams();
    indicators.forEach(ind => params.append('indicators', ind));
    params.append('period', period.toString());
    return apiClient.get<any[]>(`/api/market/indicators/${symbol}?${params.toString()}`);
  }

  async getMarketOverview(): Promise<any> {
    return apiClient.get<any>('/api/market/overview');
  }

  // Backtest methods
  async runBacktest(request: BacktestRequest, saveRecord: boolean = false): Promise<BacktestResult> {
    const params = new URLSearchParams();
    if (saveRecord) {
      params.append('save_record', 'true');
    }
    const url = `/api/backtest${params.toString() ? `?${params.toString()}` : ''}`;
    return apiClient.post<BacktestResult>(url, request);
  }

  // Backtest Record methods
  async getBacktestRecords(strategyId?: number, limit: number = 50, offset: number = 0): Promise<BacktestRecord[]> {
    const params = new URLSearchParams();
    if (strategyId) {
      params.append('strategy_id', strategyId.toString());
    }
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    return apiClient.get<BacktestRecord[]>(`/api/backtest/records?${params.toString()}`);
  }

  async getBacktestRecord(recordId: number): Promise<BacktestRecord> {
    return apiClient.get<BacktestRecord>(`/api/backtest/records/${recordId}`);
  }

  async updateBacktestRecord(recordId: number, update: BacktestRecordUpdate): Promise<BacktestRecord> {
    return apiClient.put<BacktestRecord>(`/api/backtest/records/${recordId}`, update);
  }

  async deleteBacktestRecord(recordId: number): Promise<void> {
    return apiClient.delete<void>(`/api/backtest/records/${recordId}`);
  }

  async exportBacktestRecordCSV(recordId: number): Promise<Blob> {
    const response = await fetch(`${apiClient['baseURL']}/api/backtest/records/${recordId}/export/csv`, {
      method: 'GET',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw { detail: errorData.detail || response.statusText, status: response.status } as ApiError;
    }
    return response.blob();
  }

  async exportBacktestRecordExcel(recordId: number): Promise<Blob> {
    const response = await fetch(`${apiClient['baseURL']}/api/backtest/records/${recordId}/export/excel`, {
      method: 'GET',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw { detail: errorData.detail || response.statusText, status: response.status } as ApiError;
    }
    return response.blob();
  }

  // Parameter Optimization methods
  async optimizeStrategyParameters(request: ParameterOptimizationRequest): Promise<ParameterOptimizationResult> {
    return apiClient.post<ParameterOptimizationResult>('/api/backtest/optimize', request);
  }

  // AI Strategy Analysis methods
  async analyzeBacktestResult(request: AIStrategyAnalysisRequest): Promise<AIStrategyAnalysisResponse> {
    const params = new URLSearchParams();
    params.append('strategy_id', request.strategy_id.toString());
    return apiClient.post<AIStrategyAnalysisResponse>(`/api/backtest/analyze?${params.toString()}`, {
      backtest_result: request.backtest_result
    });
  }
}

export const tradingService = new TradingService();

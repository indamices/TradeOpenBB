import { apiClient, ApiError } from './apiClient';
import { Portfolio, Position, Order, Strategy, MarketQuote, StrategyGenerationRequest, StrategyGenerationResponse, BacktestRequest, BacktestResult } from '../types';

export class TradingService {
  // Portfolio methods
  async getPortfolio(portfolioId: number = 1): Promise<Portfolio> {
    return apiClient.get<Portfolio>(`/api/portfolio?portfolio_id=${portfolioId}`);
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
    return apiClient.get<Position[]>(`/api/positions?portfolio_id=${portfolioId}`);
  }

  async createPosition(position: Omit<Position, 'id' | 'created_at'>): Promise<Position> {
    return apiClient.post<Position>('/api/positions', position);
  }

  // Order methods
  async getOrders(portfolioId: number = 1): Promise<Order[]> {
    return apiClient.get<Order[]>(`/api/orders?portfolio_id=${portfolioId}`);
  }

  async placeOrder(order: Omit<Order, 'id' | 'status' | 'created_at' | 'commission' | 'avg_fill_price' | 'filled_at'>): Promise<Order> {
    return apiClient.post<Order>('/api/orders', order);
  }

  // Strategy methods
  async getStrategies(portfolioId?: number): Promise<Strategy[]> {
    const endpoint = portfolioId 
      ? `/api/strategies?portfolio_id=${portfolioId}`
      : '/api/strategies';
    return apiClient.get<Strategy[]>(endpoint);
  }

  async saveStrategy(strategy: Omit<Strategy, 'id' | 'created_at'>): Promise<Strategy> {
    return apiClient.post<Strategy>('/api/strategies', strategy);
  }

  async generateStrategy(request: StrategyGenerationRequest): Promise<StrategyGenerationResponse> {
    return apiClient.post<StrategyGenerationResponse>('/api/strategies/generate', request);
  }

  // Market methods
  async getQuote(symbol: string): Promise<MarketQuote> {
    return apiClient.get<MarketQuote>(`/api/market/quote/${symbol}`);
  }

  // Backtest methods
  async runBacktest(request: BacktestRequest): Promise<BacktestResult> {
    return apiClient.post<BacktestResult>('/api/backtest', request);
  }
}

export const tradingService = new TradingService();

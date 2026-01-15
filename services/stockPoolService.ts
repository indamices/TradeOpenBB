import { apiClient } from './apiClient';
import { StockPool, StockPoolCreate, StockPoolUpdate, StockInfo } from '../types';

class StockPoolService {
  async getStockPools(): Promise<StockPool[]> {
    return apiClient.get<StockPool[]>('/api/stock-pools');
  }

  async getStockPool(id: number): Promise<StockPool> {
    return apiClient.get<StockPool>(`/api/stock-pools/${id}`);
  }

  async createStockPool(pool: StockPoolCreate): Promise<StockPool> {
    return apiClient.post<StockPool>('/api/stock-pools', pool);
  }

  async updateStockPool(id: number, pool: StockPoolUpdate): Promise<StockPool> {
    return apiClient.put<StockPool>(`/api/stock-pools/${id}`, pool);
  }

  async deleteStockPool(id: number): Promise<void> {
    return apiClient.delete<void>(`/api/stock-pools/${id}`);
  }

  async searchStocks(query: string, limit: number = 50): Promise<StockInfo[]> {
    const params = new URLSearchParams({ q: query, limit: limit.toString() });
    return apiClient.get<StockInfo[]>(`/api/market/stocks/search?${params}`);
  }

  async getStockInfo(symbol: string): Promise<StockInfo> {
    return apiClient.get<StockInfo>(`/api/market/stocks/${symbol}/info`);
  }
}

export const stockPoolService = new StockPoolService();

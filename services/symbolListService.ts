import { apiClient } from './apiClient';

export interface SymbolList {
  id: number;
  name: string;
  description?: string;
  symbols: string[];
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface SymbolListCreate {
  name: string;
  description?: string;
  symbols: string[];
}

export interface SymbolListUpdate {
  name?: string;
  description?: string;
  symbols?: string[];
  is_active?: boolean;
}

export class SymbolListService {
  async getSymbolLists(isActive?: boolean): Promise<SymbolList[]> {
    const params = new URLSearchParams();
    if (isActive !== undefined) {
      params.append('is_active', isActive.toString());
    }
    const queryString = params.toString();
    const endpoint = queryString ? `/api/backtest/symbol-lists?${queryString}` : '/api/backtest/symbol-lists';
    return apiClient.get<SymbolList[]>(endpoint);
  }

  async getSymbolList(listId: number): Promise<SymbolList> {
    return apiClient.get<SymbolList>(`/api/backtest/symbol-lists/${listId}`);
  }

  async createSymbolList(list: SymbolListCreate): Promise<SymbolList> {
    return apiClient.post<SymbolList>('/api/backtest/symbol-lists', list);
  }

  async updateSymbolList(listId: number, updates: SymbolListUpdate): Promise<SymbolList> {
    return apiClient.put<SymbolList>(`/api/backtest/symbol-lists/${listId}`, updates);
  }

  async deleteSymbolList(listId: number): Promise<void> {
    return apiClient.delete(`/api/backtest/symbol-lists/${listId}`);
  }
}

export const symbolListService = new SymbolListService();

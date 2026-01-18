import { apiClient } from './apiClient';
import { DataSourceConfig, DataSourceConfigCreate, DataSourceConfigUpdate, AvailableDataSource } from '../types';

export const dataSourceService = {
  async getDataSources(): Promise<DataSourceConfig[]> {
    return apiClient.get<DataSourceConfig[]>('/api/data-sources');
  },

  async getDataSource(id: number): Promise<DataSourceConfig> {
    return apiClient.get<DataSourceConfig>(`/api/data-sources/${id}`);
  },

  async createDataSource(source: DataSourceConfigCreate): Promise<DataSourceConfig> {
    return apiClient.post<DataSourceConfig>('/api/data-sources', source);
  },

  async updateDataSource(id: number, source: DataSourceConfigUpdate): Promise<DataSourceConfig> {
    return apiClient.put<DataSourceConfig>(`/api/data-sources/${id}`, source);
  },

  async deleteDataSource(id: number): Promise<void> {
    return apiClient.delete(`/api/data-sources/${id}`);
  },

  async getAvailableDataSources(): Promise<{ sources: AvailableDataSource[] }> {
    return apiClient.get<{ sources: AvailableDataSource[] }>('/api/data-sources/available');
  },

  async getDataSourcesStatus(): Promise<{ sources: Array<{ source_id: number; name: string; provider: string; is_working: boolean; priority: number; is_default: boolean; data_points: number; error?: string }>; working_source_id?: number; message: string }> {
    return apiClient.get('/api/data-sources/status');
  },

  async testDataSourceConnection(id: number): Promise<{ success: boolean; message: string; data_points?: number; symbol?: string; date_range?: string; error?: string; provider?: string; source_name?: string; is_active?: boolean }> {
    return apiClient.post(`/api/data-sources/${id}/test`);
  }
};

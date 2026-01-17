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
  }
};

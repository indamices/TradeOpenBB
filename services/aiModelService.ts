import { apiClient } from './apiClient';
import { AIModelConfig, AIModelConfigCreate } from '../types';

export class AIModelService {
  async getAIModels(): Promise<AIModelConfig[]> {
    return apiClient.get<AIModelConfig[]>('/api/ai-models');
  }

  async createAIModel(model: AIModelConfigCreate): Promise<AIModelConfig> {
    return apiClient.post<AIModelConfig>('/api/ai-models', model);
  }

  async updateAIModel(modelId: number, updates: Partial<AIModelConfigCreate>): Promise<AIModelConfig> {
    return apiClient.put<AIModelConfig>(`/api/ai-models/${modelId}`, updates);
  }

  async deleteAIModel(modelId: number): Promise<void> {
    return apiClient.delete<void>(`/api/ai-models/${modelId}`);
  }

  async testAIModel(modelId: number): Promise<{ success: boolean; message: string }> {
    return apiClient.post<{ success: boolean; message: string }>(`/api/ai-models/${modelId}/test`);
  }

  async setDefaultModel(modelId: number): Promise<AIModelConfig> {
    return apiClient.put<AIModelConfig>(`/api/ai-models/${modelId}/set-default`);
  }
}

export const aiModelService = new AIModelService();

import { apiClient } from './apiClient';

export interface Conversation {
  id: number;
  conversation_id: string;
  title?: string;
  created_at: string;
  updated_at?: string;
  message_count: number;
}

export interface ConversationDetail {
  conversation_id: string;
  title?: string;
  created_at: string;
  updated_at?: string;
  messages: Array<{
    id: number;
    conversation_id: string;
    role: 'user' | 'assistant';
    content: string;
    code_snippets?: { [key: string]: string };
    created_at?: string;  // Backend may return this
    timestamp?: string;   // Backend actually returns this field
  }>;
}

export interface ChatStrategy {
  id: number;
  conversation_id: string;
  message_id?: number;
  name: string;
  logic_code: string;
  description?: string;
  is_saved: boolean;
  saved_strategy_id?: number;
  created_at: string;
}

export interface SaveStrategyRequest {
  name: string;
  description?: string;
  target_portfolio_id?: number;
}

export class ChatService {
  // Conversation methods
  async getConversations(): Promise<Conversation[]> {
    return apiClient.get<Conversation[]>('/api/ai/conversations');
  }

  async getConversation(conversationId: string): Promise<ConversationDetail> {
    return apiClient.get<ConversationDetail>(`/api/ai/conversations/${conversationId}`);
  }

  async deleteConversation(conversationId: string): Promise<void> {
    return apiClient.delete(`/api/ai/conversations/${conversationId}`);
  }

  // Chat Strategy methods
  async extractStrategies(conversationId: string, messageId: number): Promise<ChatStrategy[]> {
    return apiClient.post<ChatStrategy[]>(`/api/ai/conversations/${conversationId}/extract-strategies?message_id=${messageId}`);
  }

  async getChatStrategies(conversationId: string): Promise<ChatStrategy[]> {
    return apiClient.get<ChatStrategy[]>(`/api/ai/conversations/${conversationId}/strategies`);
  }

  async saveChatStrategy(chatStrategyId: number, request: SaveStrategyRequest): Promise<any> {
    return apiClient.post(`/api/ai/chat-strategies/${chatStrategyId}/save`, request);
  }

  async deleteChatStrategy(chatStrategyId: number): Promise<void> {
    return apiClient.delete(`/api/ai/chat-strategies/${chatStrategyId}`);
  }
}

export const chatService = new ChatService();

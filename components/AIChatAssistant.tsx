import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Code, Lightbulb, MessageSquare, User, History, Trash2, Plus, Sparkles, Save, X, Power, PowerOff, FileText, Scissors } from 'lucide-react';
import { ChatMessage, ChatRequest, ChatResponse, Conversation, ChatStrategy, AIModelConfig } from '../types';
import { apiClient } from '../services/apiClient';
import { chatService } from '../services/chatService';
import { tradingService } from '../services/tradingService';
import { aiModelService } from '../services/aiModelService';
import { ApiError } from '../services/apiClient';

const AIChatAssistant: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [chatStrategies, setChatStrategies] = useState<ChatStrategy[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [savingStrategy, setSavingStrategy] = useState<ChatStrategy | null>(null);
  const [saveForm, setSaveForm] = useState({ name: '', description: '' });
  const [extractingStrategy, setExtractingStrategy] = useState<number | null>(null);
  const [aiModels, setAiModels] = useState<AIModelConfig[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<number | undefined>();
  const [activeModel, setActiveModel] = useState<AIModelConfig | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
    loadChatStrategies();
    loadAIModels();
  }, [conversationId]);

  const loadAIModels = async () => {
    try {
      const models = await aiModelService.getAIModels();
      setAiModels(models);
      // Find active model
      const active = models.find(m => m.is_active);
      if (active) {
        setActiveModel(active);
        setSelectedModelId(active.id);
      } else if (models.length > 0) {
        // Fallback to first model if no active
        setSelectedModelId(models[0].id);
      }
    } catch (error) {
      console.error('Failed to load AI models:', error);
    }
  };

  const handleModelChange = async (modelId: number) => {
    try {
      await aiModelService.setActiveModel(modelId);
      setSelectedModelId(modelId);
      const model = aiModels.find(m => m.id === modelId);
      if (model) {
        setActiveModel(model);
      }
      // Reload models to update active status
      await loadAIModels();
    } catch (error) {
      console.error('Failed to set active model:', error);
    }
  };

  useEffect(() => {
    if (conversationId) {
      loadConversation();
    }
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = async () => {
    try {
      const data = await chatService.getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async () => {
    if (!conversationId) return;
    try {
      const detail = await chatService.getConversation(conversationId);
      const chatMessages: ChatMessage[] = detail.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || msg.created_at || new Date().toISOString(), // Backend returns 'timestamp', fallback to 'created_at'
        code_snippets: msg.code_snippets
      }));
      setMessages(chatMessages);
      loadChatStrategies();
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const loadChatStrategies = async () => {
    if (!conversationId) return;
    try {
      const data = await chatService.getChatStrategies(conversationId);
      setChatStrategies(data);
    } catch (error) {
      console.error('Failed to load chat strategies:', error);
    }
  };

  const handleNewConversation = () => {
    setConversationId(null);
    setMessages([]);
    setChatStrategies([]);
    const welcomeMessage: ChatMessage = {
      role: 'assistant',
      content: '你好！我是AI策略助手。我可以帮助你：\n\n• 分析和优化交易策略\n• 解释策略代码逻辑\n• 提供市场分析和建议\n• 协助回测和参数调优\n\n请告诉我你需要什么帮助？',
      timestamp: new Date().toISOString(),
    };
    setMessages([welcomeMessage]);
  };

  const handleSelectConversation = (convId: string) => {
    setConversationId(convId);
  };

  const handleDeleteConversation = async (convId: string) => {
    if (!confirm('确定要删除这个会话吗？')) return;
    try {
      await chatService.deleteConversation(convId);
      if (conversationId === convId) {
        handleNewConversation();
      }
      await loadConversations();
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('删除会话失败');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const request: ChatRequest = {
        message: currentInput,
        conversation_id: conversationId || undefined,
      };

      const response = await apiClient.post<ChatResponse>('/api/ai/chat', request);
      
      setConversationId(response.conversation_id);

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        code_snippets: response.code_snippets ? {
          python: response.code_snippets.python || '',
        } : undefined,
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      }

      // Reload conversations to update list
      await loadConversations();
    } catch (err) {
      const apiError = err as ApiError;
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `抱歉，发生了错误：${apiError.detail || '无法连接到AI服务'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleExtractStrategy = async (messageIdx: number) => {
    if (!conversationId) {
      alert('请先选择一个会话');
      return;
    }
    
    const message = messages[messageIdx];
    if (message.role !== 'assistant') {
      alert('只能从 AI 助手的消息中提取策略');
      return;
    }
    
    if (!message.code_snippets || !message.code_snippets.python) {
      alert('该消息中没有找到策略代码');
      return;
    }

    // Find message ID from conversation detail
    try {
      setExtractingStrategy(messageIdx);
      
      // Reload conversation to ensure timestamps match between local state and database
      // This ensures that messages array has the same timestamps as the database
      const targetMessageContent = messages[messageIdx]?.content;
      const targetMessageCodeSnippets = messages[messageIdx]?.code_snippets;
      
      await loadConversation();
      
      // After reload, find the message by content (more reliable than index after reload)
      const reloadedMessageIdx = messages.findIndex(m => 
        m.role === 'assistant' && 
        m.content === targetMessageContent &&
        (m.code_snippets?.python === targetMessageCodeSnippets?.python || 
         (!m.code_snippets && !targetMessageCodeSnippets))
      );
      
      // Update messageIdx to the reloaded message index if found
      const actualMessageIdx = reloadedMessageIdx !== -1 ? reloadedMessageIdx : messageIdx;
      
      const detail = await chatService.getConversation(conversationId);
      
      // Improved matching: Try multiple strategies
      const targetMessage = messages[actualMessageIdx];
      
      // Strategy 1: Match by position in assistant messages array (most reliable if order is consistent)
      const localAssistantMessages = messages.filter(m => m.role === 'assistant');
      const targetLocalAssistantIdx = localAssistantMessages.findIndex(m => 
        m === targetMessage || (m.timestamp === targetMessage.timestamp && m.role === targetMessage.role)
      );
      
      let assistantMsg: typeof detail.messages[0] | undefined;
      
      if (targetLocalAssistantIdx >= 0) {
        const detailAssistantMessages = detail.messages.filter(m => m.role === 'assistant');
        if (targetLocalAssistantIdx < detailAssistantMessages.length) {
          assistantMsg = detailAssistantMessages[targetLocalAssistantIdx];
        }
      }
      
      // Strategy 2: Match by timestamp with tolerance and content similarity (fallback)
      if (!assistantMsg) {
        assistantMsg = detail.messages.find((msg) => {
          if (msg.role !== 'assistant') return false;
          
          // Backend returns 'timestamp' field, not 'created_at'
          const msgTimestamp = msg.timestamp || msg.created_at;
          
          // Check timestamp with 10 second tolerance
          const timeDiff = Math.abs(new Date(msgTimestamp).getTime() - new Date(targetMessage.timestamp).getTime());
          const timeMatch = timeDiff < 10000; // Allow 10 second difference
          
          // Check content similarity (first 100 chars) as additional verification
          const contentSimilar = msg.content.substring(0, 100) === targetMessage.content.substring(0, 100) ||
            (msg.content.length > 0 && targetMessage.content.length > 0 && 
             msg.content.substring(0, 50) === targetMessage.content.substring(0, 50));
          
          return timeMatch && contentSimilar;
        });
      }
      
      // Strategy 3: Match by exact timestamp (original logic, but as last resort)
      if (!assistantMsg) {
        assistantMsg = detail.messages.find((msg) => {
          if (msg.role !== 'assistant') return false;
          
          const msgTimestamp = msg.timestamp || msg.created_at;
          
          const chatMsgIdx = messages.findIndex(m => {
            const exactMatch = m.timestamp === msgTimestamp;
            const timeMatch = Math.abs(new Date(m.timestamp).getTime() - new Date(msgTimestamp).getTime()) < 1000;
            return (exactMatch || timeMatch) && m.role === msg.role;
          });
          
          return chatMsgIdx === actualMessageIdx;
        });
      }
      
      if (!assistantMsg || !assistantMsg.id) {
        alert('无法找到消息 ID，请刷新页面后重试');
        return;
      }

      const strategies = await chatService.extractStrategies(conversationId, assistantMsg.id);
      await loadChatStrategies();
      
      if (strategies && strategies.length > 0) {
        alert(`成功提取 ${strategies.length} 个策略！`);
      } else {
        alert('未找到可提取的策略代码。请确保代码包含 strategy_logic 函数。');
      }
    } catch (error: any) {
      console.error('Failed to extract strategy:', error);
      const errorMsg = error.detail || error.message || '提取策略失败';
      alert(`提取策略失败: ${errorMsg}`);
    } finally {
      setExtractingStrategy(null);
    }
  };

  const handleSaveStrategy = async (chatStrategy: ChatStrategy) => {
    setSavingStrategy(chatStrategy);
    setSaveForm({
      name: chatStrategy.name,
      description: chatStrategy.description || ''
    });
  };

  const handleConfirmSave = async () => {
    if (!savingStrategy || !saveForm.name.trim()) return;
    try {
      const savedStrategy = await chatService.saveChatStrategy(savingStrategy.id, {
        name: saveForm.name,
        description: saveForm.description,
        target_portfolio_id: 1
      });
      await loadChatStrategies();
      setSavingStrategy(null);
      setSaveForm({ name: '', description: '' });
      
      // Notify user that strategy was saved successfully
      alert(`策略已成功保存到策略管理页面！策略ID: ${savedStrategy.id}`);
      
      // Trigger a custom event to notify other components to refresh
      window.dispatchEvent(new CustomEvent('strategySaved', { detail: { strategyId: savedStrategy.id } }));
    } catch (error) {
      console.error('Failed to save strategy:', error);
      alert('保存策略失败');
    }
  };

  const handleToggleStrategyActive = async (strategyId: number, currentStatus: boolean) => {
    try {
      await tradingService.setStrategyActive(strategyId, !currentStatus);
      // Reload strategies to update status
      const detail = await chatService.getConversation(conversationId!);
      await loadChatStrategies();
    } catch (error) {
      console.error('Failed to toggle strategy status:', error);
      alert('更新策略状态失败');
    }
  };

  const handleSuggestion = (suggestion: string) => {
    setInput(suggestion);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const currentConversation = conversations.find(c => c.conversation_id === conversationId);

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-64 border-r border-slate-800 bg-slate-900 flex flex-col">
          {/* Conversations */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <History size={16} />
                会话历史
              </h3>
              <button
                onClick={handleNewConversation}
                className="p-1.5 bg-emerald-600 hover:bg-emerald-500 rounded text-white transition"
                title="新建会话"
              >
                <Plus size={14} />
              </button>
            </div>
            <div className="space-y-2">
              {conversations.map((conv) => (
                <div
                  key={conv.conversation_id}
                  className={`p-3 rounded-lg cursor-pointer transition ${
                    conversationId === conv.conversation_id
                      ? 'bg-emerald-600/20 border border-emerald-600/30'
                      : 'bg-slate-800 hover:bg-slate-700 border border-slate-700'
                  }`}
                  onClick={() => handleSelectConversation(conv.conversation_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-200 truncate">
                        {conv.title || '新会话'}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {conv.message_count} 条消息
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteConversation(conv.conversation_id);
                      }}
                      className="p-1 hover:bg-slate-600 rounded transition"
                    >
                      <Trash2 size={12} className="text-slate-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Extracted Strategies */}
          {conversationId && chatStrategies.length > 0 && (
            <div className="border-t border-slate-800 p-4 max-h-64 overflow-y-auto">
              <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                <Sparkles size={16} />
                提取的策略
              </h3>
              <div className="space-y-2">
                {chatStrategies.map((strategy) => (
                  <div
                    key={strategy.id}
                    className="p-3 bg-slate-800 rounded-lg border border-slate-700"
                  >
                    <div className="text-xs font-medium text-slate-200 mb-1">
                      {strategy.name}
                    </div>
                    {strategy.is_saved && strategy.saved_strategy_id ? (
                      <div className="text-xs text-emerald-400 flex items-center gap-1">
                        <Save size={12} /> 已保存
                      </div>
                    ) : (
                      <button
                        onClick={() => handleSaveStrategy(strategy)}
                        className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 mt-1"
                      >
                        <Save size={12} /> 保存到策略池
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-2 hover:bg-slate-800 rounded transition"
            >
              <History size={18} className="text-slate-400" />
            </button>
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <MessageSquare className="text-blue-400" size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-200">AI策略助手</h2>
              <p className="text-sm text-slate-400">
                {currentConversation?.title || '新会话'}
              </p>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-slate-500 py-12">
              <MessageSquare size={48} className="mx-auto mb-4 text-slate-700" />
              <p className="text-lg font-medium mb-2">开始新的对话</p>
              <p className="text-sm">选择一个会话或开始新的对话</p>
            </div>
          ) : (
            messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex gap-4 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center">
                    <MessageSquare className="text-blue-400" size={16} />
                  </div>
                )}
                
                <div
                  className={`max-w-[75%] rounded-lg p-4 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-800 text-slate-200 border border-slate-700'
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">{message.content}</div>
                  
                  {/* Code Snippets */}
                  {message.code_snippets && Object.keys(message.code_snippets).length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-700">
                      {Object.entries(message.code_snippets).map(([lang, code]) => (
                        <div key={lang} className="mt-2">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Code size={14} className="text-slate-400" />
                              <span className="text-xs text-slate-400 uppercase">{lang}</span>
                            </div>
                            {message.role === 'assistant' && code.includes('def strategy_logic') && (
                              <button
                                onClick={() => handleExtractStrategy(idx)}
                                disabled={extractingStrategy === idx}
                                className="text-xs px-2 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded flex items-center gap-1 transition disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {extractingStrategy === idx ? (
                                  <>
                                    <Loader2 size={12} className="animate-spin" /> 提取中...
                                  </>
                                ) : (
                                  <>
                                    <Scissors size={12} /> 提取策略
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                          <pre className="bg-slate-900 rounded p-3 text-xs overflow-x-auto text-slate-300 border border-slate-700">
                            <code>{code}</code>
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  <div className="text-xs text-slate-500 mt-2">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>

                {message.role === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                    <User className="text-slate-400" size={16} />
                  </div>
                )}
              </div>
            ))
          )}

          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center">
                <MessageSquare className="text-blue-400" size={16} />
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400">
                  <Loader2 className="animate-spin" size={16} />
                  <span>AI正在思考...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/50">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb size={14} className="text-yellow-400" />
              <span className="text-xs text-slate-400 font-medium">建议</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestion(suggestion)}
                  className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900">
          {/* Model Selector */}
          {aiModels.length > 0 && (
            <div className="mb-3 flex items-center gap-2">
              <span className="text-xs text-slate-400">当前模型:</span>
              <select
                value={selectedModelId || ''}
                onChange={(e) => handleModelChange(Number(e.target.value))}
                className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {aiModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} {model.is_active ? '(激活)' : ''}
                  </option>
                ))}
              </select>
              {activeModel && (
                <span className="text-xs text-slate-500">
                  ({activeModel.provider} - {activeModel.model_name})
                </span>
              )}
            </div>
          )}
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入你的问题或需求..."
              rows={2}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>发送中</span>
                </>
              ) : (
                <>
                  <Send size={18} />
                  <span>发送</span>
                </>
              )}
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            按 Enter 发送，Shift+Enter 换行
          </p>
        </div>
      </div>

      {/* Save Strategy Dialog */}
      {savingStrategy && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-200">保存策略到策略池</h3>
              <button
                onClick={() => setSavingStrategy(null)}
                className="p-1 hover:bg-slate-700 rounded transition"
              >
                <X size={18} className="text-slate-400" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">策略名称</label>
                <input
                  type="text"
                  value={saveForm.name}
                  onChange={(e) => setSaveForm({ ...saveForm, name: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">描述（可选）</label>
                <textarea
                  value={saveForm.description}
                  onChange={(e) => setSaveForm({ ...saveForm, description: e.target.value })}
                  rows={3}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500 resize-none"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={handleConfirmSave}
                  disabled={!saveForm.name.trim()}
                  className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded text-sm font-medium transition"
                >
                  <Save size={14} className="inline mr-2" />
                  保存
                </button>
                <button
                  onClick={() => setSavingStrategy(null)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm font-medium transition"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIChatAssistant;

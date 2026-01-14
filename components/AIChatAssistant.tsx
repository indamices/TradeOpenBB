import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Code, Lightbulb, MessageSquare, User } from 'lucide-react';
import { ChatMessage, ChatRequest, ChatResponse, Strategy } from '../types';
import { apiClient } from '../services/apiClient';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';

const AIChatAssistant: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadStrategies();
    // Initialize with welcome message
    const welcomeMessage: ChatMessage = {
      role: 'assistant',
      content: '你好！我是AI策略助手。我可以帮助你：\n\n• 分析和优化交易策略\n• 解释策略代码逻辑\n• 提供市场分析和建议\n• 协助回测和参数调优\n\n请告诉我你需要什么帮助？',
      timestamp: new Date().toISOString(),
    };
    setMessages([welcomeMessage]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadStrategies = async () => {
    try {
      const data = await tradingService.getStrategies();
      setStrategies(data);
    } catch (err) {
      console.error('Failed to load strategies:', err);
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
    setInput('');
    setLoading(true);

    try {
      const request: ChatRequest = {
        message: input,
        conversation_id: conversationId || undefined,
        context: strategies.length > 0 ? {
          strategy_id: strategies[0].id,
        } : undefined,
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

  const handleSuggestion = (suggestion: string) => {
    setInput(suggestion);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-900">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <MessageSquare className="text-blue-400" size={20} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-200">AI策略助手</h2>
            <p className="text-sm text-slate-400">智能对话式策略开发与优化</p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message, idx) => (
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
                      <div className="flex items-center gap-2 mb-2">
                        <Code size={14} className="text-slate-400" />
                        <span className="text-xs text-slate-400 uppercase">{lang}</span>
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
        ))}

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
  );
};

export default AIChatAssistant;

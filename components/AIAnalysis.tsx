import React, { useState } from 'react';
import { 
  Sparkles, Loader2, AlertCircle, CheckCircle, 
  TrendingUp, TrendingDown, Lightbulb, Code2 
} from 'lucide-react';
import { BacktestResult, Strategy, AIStrategyAnalysisResponse } from '../types';
import { tradingService } from '../services/tradingService';
import { ApiError } from '../services/apiClient';
import { formatMetric } from '../utils/format';

interface AIAnalysisProps {
  backtestResult: BacktestResult;
  strategyId: number;
  strategy?: Strategy;
  onApplySuggestion?: (suggestion: string) => void;
}

const AIAnalysis: React.FC<AIAnalysisProps> = ({
  backtestResult,
  strategyId,
  strategy,
  onApplySuggestion
}) => {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AIStrategyAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const response = await tradingService.analyzeBacktestResult({
        backtest_result: backtestResult,
        strategy_id: strategyId
      });
      setAnalysis(response);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'AI分析失败');
      console.error('AI Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="text-purple-400" size={24} />
            <div>
              <h2 className="text-2xl font-bold text-slate-200">AI策略分析</h2>
              <p className="text-slate-400 text-sm mt-1">
                {strategy ? `分析策略: ${strategy.name}` : 'AI智能分析回测结果'}
              </p>
            </div>
          </div>
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg flex items-center gap-2 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>分析中...</span>
              </>
            ) : (
              <>
                <Sparkles size={18} />
                <span>开始分析</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Backtest Metrics Summary */}
      {!analysis && !loading && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-4">回测指标摘要</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-800 p-4 rounded-lg">
              <div className="text-sm text-slate-400">Sharpe Ratio</div>
              <div className="text-2xl font-bold text-emerald-400">
                {formatMetric(backtestResult.sharpe_ratio)}
              </div>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <div className="text-sm text-slate-400">年化收益率</div>
              <div className="text-2xl font-bold text-emerald-400">
                {formatMetric(backtestResult.annualized_return, '%')}
              </div>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <div className="text-sm text-slate-400">最大回撤</div>
              <div className="text-2xl font-bold text-red-400">
                {formatMetric(backtestResult.max_drawdown, '%')}
              </div>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <div className="text-sm text-slate-400">胜率</div>
              <div className="text-2xl font-bold text-blue-400">
                {formatMetric(backtestResult.win_rate, '%')}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
          <Loader2 className="animate-spin text-purple-400 mx-auto mb-4" size={48} />
          <p className="text-slate-400">AI正在分析策略表现，请稍候...</p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-6">
          {/* Analysis Summary */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="text-emerald-400" size={24} />
              <h3 className="text-xl font-bold text-slate-200">分析摘要</h3>
            </div>
            <div className="prose prose-invert max-w-none">
              <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                {analysis.analysis_summary}
              </p>
            </div>
          </div>

          {/* Strengths */}
          {analysis.strengths && analysis.strengths.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="text-emerald-400" size={24} />
                <h3 className="text-xl font-bold text-slate-200">策略优势</h3>
              </div>
              <ul className="space-y-3">
                {analysis.strengths.map((strength, idx) => (
                  <li key={`strength-${idx}`} className="flex items-start gap-3">
                    <CheckCircle className="text-emerald-400 mt-0.5 flex-shrink-0" size={18} />
                    <span className="text-slate-300">{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Weaknesses */}
          {analysis.weaknesses && analysis.weaknesses.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingDown className="text-red-400" size={24} />
                <h3 className="text-xl font-bold text-slate-200">策略劣势</h3>
              </div>
              <ul className="space-y-3">
                {analysis.weaknesses.map((weakness, idx) => (
                  <li key={`weakness-${idx}`} className="flex items-start gap-3">
                    <AlertCircle className="text-red-400 mt-0.5 flex-shrink-0" size={18} />
                    <span className="text-slate-300">{weakness}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Optimization Suggestions */}
          {analysis.optimization_suggestions && analysis.optimization_suggestions.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="text-yellow-400" size={24} />
                <h3 className="text-xl font-bold text-slate-200">优化建议</h3>
              </div>
              <ul className="space-y-4">
                {analysis.optimization_suggestions.map((suggestion, idx) => (
                  <li key={`suggestion-${idx}`} className="bg-slate-800 p-4 rounded-lg">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1">
                        <Lightbulb className="text-yellow-400 mt-0.5 flex-shrink-0" size={18} />
                        <span className="text-slate-300">{suggestion}</span>
                      </div>
                      {onApplySuggestion && (
                        <button
                          onClick={() => onApplySuggestion(suggestion)}
                          className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-sm rounded flex items-center gap-1 flex-shrink-0"
                        >
                          <Code2 size={14} />
                          应用
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Raw AI Response (Collapsible) */}
          {analysis.raw_ai_response && (
            <details className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <summary className="cursor-pointer text-slate-400 hover:text-slate-300 font-medium">
                查看原始AI响应
              </summary>
              <div className="mt-4 p-4 bg-slate-800 rounded-lg">
                <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono">
                  {analysis.raw_ai_response}
                </pre>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
};

export default AIAnalysis;

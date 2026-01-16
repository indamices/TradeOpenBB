import React, { useState, useEffect } from 'react';
import { Sparkles, Play, Save, Code, Terminal } from 'lucide-react';
import { generateStrategyCode } from '../services/aiStrategyService';
import { tradingService } from '../services/tradingService';
import { aiModelService } from '../services/aiModelService';
import { AIModelConfig, Strategy, BacktestRequest } from '../types';

const StrategyLab: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('');
  const [explanation, setExplanation] = useState('');
  const [consoleOutput, setConsoleOutput] = useState<string[]>([]);
  const [aiModels, setAiModels] = useState<AIModelConfig[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<number | undefined>();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | null>(null);
  const [backtestLoading, setBacktestLoading] = useState(false);

  const loadStrategies = async () => {
    try {
      const strategyList = await tradingService.getStrategies();
      setStrategies(strategyList);
    } catch (error) {
      console.error('Failed to load strategies:', error);
      setConsoleOutput(prev => [...prev, `> Error loading strategies.`]);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [models, strategyList] = await Promise.all([
          aiModelService.getAIModels(),
          tradingService.getStrategies()
        ]);
        setAiModels(models);
        setStrategies(strategyList);
        
        // Set active model (prefer active over default)
        const activeModel = models.find(m => m.is_active);
        if (activeModel) {
          setSelectedModelId(activeModel.id);
        } else {
          // Fallback to default model
          const defaultModel = models.find(m => m.is_default);
          if (defaultModel) {
            setSelectedModelId(defaultModel.id);
          } else if (models.length > 0) {
            setSelectedModelId(models[0].id);
          }
        }
      } catch (error) {
        console.error('Failed to load data:', error);
        setConsoleOutput(prev => [...prev, `> Error loading AI models or strategies.`]);
      }
    };
    loadData();
    
    // Listen for strategy saved events to refresh the list
    const handleStrategySaved = () => {
      loadStrategies();
    };
    window.addEventListener('strategySaved', handleStrategySaved);
    
    return () => {
      window.removeEventListener('strategySaved', handleStrategySaved);
    };
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setIsGenerating(true);
    setConsoleOutput(prev => [...prev, `> Generating strategy from prompt: "${prompt}"...`]);
    
    try {
      const response = await generateStrategyCode(prompt, selectedModelId);
      setGeneratedCode(response.code);
      setExplanation(response.explanation);
      setConsoleOutput(prev => [...prev, `> Generation successful.`, `> ${response.explanation}`]);
    } catch (error: any) {
      setConsoleOutput(prev => [...prev, `> Error: ${error.detail || 'Failed to generate strategy.'}`]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleBacktest = async () => {
    if (!generatedCode || !selectedStrategyId) {
      setConsoleOutput(prev => [...prev, `> Error: Please save the strategy first before backtesting.`]);
      return;
    }
    
    setBacktestLoading(true);
    setConsoleOutput(prev => [...prev, `> Running backtest...`, `> Fetching historical data...`]);
    
    try {
      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      const request: BacktestRequest = {
        strategy_id: selectedStrategyId,
        start_date: startDate,
        end_date: endDate,
        initial_cash: 100000,
        symbols: ['AAPL', 'MSFT', 'TSLA']
      };
      
      const result = await tradingService.runBacktest(request);
      setConsoleOutput(prev => [
        ...prev,
        `> Backtest Complete.`,
        `> Sharpe Ratio: ${result.sharpe_ratio.toFixed(2)}`,
        `> Annualized Return: ${result.annualized_return.toFixed(2)}%`,
        `> Max Drawdown: -${result.max_drawdown.toFixed(2)}%`,
        `> Total Trades: ${result.total_trades}`,
        `> Total Return: ${result.total_return.toFixed(2)}%`
      ]);
    } catch (error: any) {
      setConsoleOutput(prev => [...prev, `> Backtest Error: ${error.detail || 'Failed to run backtest.'}`]);
    } finally {
      setBacktestLoading(false);
    }
  };

  const handleSave = async () => {
    if (!generatedCode) return;
    try {
      const strategy = await tradingService.saveStrategy({
        name: `AI Strategy ${new Date().toLocaleTimeString()}`,
        logic_code: generatedCode,
        is_active: false,
        target_portfolio_id: 1,
        description: explanation
      });
      setSelectedStrategyId(strategy.id);
      setStrategies(prev => [...prev, strategy]);
      setConsoleOutput(prev => [...prev, `> Strategy saved to database (ID: ${strategy.id}).`]);
    } catch (error: any) {
      setConsoleOutput(prev => [...prev, `> Error saving strategy: ${error.detail || 'Failed to save.'}`]);
    }
  };

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col lg:flex-row gap-6">
      {/* Left Panel: Controls */}
      <div className="w-full lg:w-1/3 flex flex-col gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex-1 flex flex-col">
          <div className="flex items-center gap-2 mb-4 text-emerald-400">
            <Sparkles size={20} />
            <h2 className="font-bold text-lg text-white">AI Copilot</h2>
          </div>
          <p className="text-slate-400 text-sm mb-4">
            Describe your strategy in plain English. The AI will generate the Pandas/Python code for the OpenBB engine.
          </p>
          
          {/* AI Model Selection */}
          {aiModels.length > 0 && (
            <div className="mb-4">
              <label className="block text-xs text-slate-500 mb-1">AI Model</label>
              <select
                value={selectedModelId || ''}
                onChange={async (e) => {
                  const modelId = e.target.value ? parseInt(e.target.value) : undefined;
                  setSelectedModelId(modelId);
                  // Set as active model
                  if (modelId) {
                    try {
                      await aiModelService.setActiveModel(modelId);
                      // Reload models to update active status
                      const models = await aiModelService.getAIModels();
                      setAiModels(models);
                    } catch (error) {
                      console.error('Failed to set active model:', error);
                    }
                  }
                }}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm"
              >
                {aiModels.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} {model.is_active ? '(激活)' : ''} ({model.provider})
                  </option>
                ))}
              </select>
            </div>
          )}
          
          <textarea 
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full flex-1 bg-slate-950 border border-slate-700 rounded-lg p-4 text-slate-200 resize-none focus:outline-none focus:border-emerald-500"
            placeholder="E.g., Write a mean reversion strategy using Bollinger Bands. Buy when price touches lower band, sell when it touches upper band."
          />
          <button 
            onClick={handleGenerate}
            disabled={isGenerating || !prompt}
            className={`mt-4 w-full py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition
              ${isGenerating ? 'bg-slate-700 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20'}
            `}
          >
            {isGenerating ? 'Thinking...' : 'Generate Code'}
            {!isGenerating && <Sparkles size={16} />}
          </button>
        </div>

         <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col h-1/3">
             <div className="flex items-center gap-2 mb-2 text-slate-300">
                <Terminal size={18} />
                <h3 className="font-bold">System Output</h3>
             </div>
             <div className="flex-1 bg-black rounded p-3 font-mono text-xs text-green-500 overflow-y-auto">
                 {consoleOutput.map((line, i) => (
                     <div key={i} className="mb-1">{line}</div>
                 ))}
                 {consoleOutput.length === 0 && <span className="text-slate-600">Ready...</span>}
             </div>
         </div>
      </div>

      {/* Right Panel: Code Editor & Actions */}
      <div className="w-full lg:w-2/3 flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-800/50">
          <div className="flex items-center gap-2 text-slate-200">
            <Code size={18} />
            <span className="font-medium">strategy.py</span>
          </div>
          <div className="flex gap-2">
            <button 
                onClick={handleBacktest}
                disabled={!generatedCode || !selectedStrategyId || backtestLoading}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm font-medium flex items-center gap-2 transition disabled:opacity-50"
            >
              <Play size={14} /> {backtestLoading ? 'Running...' : 'Backtest'}
            </button>
            <button 
                onClick={handleSave}
                disabled={!generatedCode}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-sm font-medium flex items-center gap-2 transition disabled:opacity-50"
            >
              <Save size={14} /> Save
            </button>
          </div>
        </div>
        
        <div className="flex-1 bg-[#0d1117] p-0 overflow-hidden relative">
            <textarea
                value={generatedCode}
                onChange={(e) => setGeneratedCode(e.target.value)}
                className="w-full h-full bg-transparent text-slate-300 font-mono text-sm p-6 focus:outline-none resize-none"
                spellCheck={false}
                placeholder="# Generated Python code will appear here..."
            />
        </div>
      </div>
    </div>
  );
};

export default StrategyLab;

import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import StrategyLab from './components/StrategyLab';
import AIModelSettings from './components/AIModelSettings';
import { Wallet } from 'lucide-react';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'backtest':
        // TODO: Replace with BacktestLab component
        return <div className="text-slate-400">回测实验室（开发中）</div>;
      case 'ai-chat':
        // TODO: Replace with AIChatAssistant component
        return <div className="text-slate-400">AI策略助手（开发中）</div>;
      case 'portfolio':
        return (
            <div className="flex flex-col items-center justify-center h-[50vh] text-slate-500">
                <Wallet size={48} className="mb-4 text-slate-700" />
                <h2 className="text-xl font-bold text-slate-400">Portfolio Management</h2>
                <p>Advanced allocation settings would go here.</p>
            </div>
        );
      case 'ai-settings':
        return <AIModelSettings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
      {renderContent()}
    </Layout>
  );
};

export default App;

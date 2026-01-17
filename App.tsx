import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import BacktestLab from './components/BacktestLab';
import AIChatAssistant from './components/AIChatAssistant';
import StrategyLab from './components/StrategyLab';
import StrategyManager from './components/StrategyManager';
import AIModelSettings from './components/AIModelSettings';
import PortfolioManager from './components/PortfolioManager';
import DataSourceManager from './components/DataSourceManager';
import StockPoolManager from './components/StockPoolManager';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'backtest':
        return <BacktestLab />;
      case 'ai-chat':
        return <AIChatAssistant />;
      case 'strategy':
        return <StrategyLab />;
      case 'strategy-manager':
        return <StrategyManager />;
      case 'portfolio':
        return <PortfolioManager />;
      case 'ai-settings':
        return <AIModelSettings />;
      case 'data-sources':
        return <DataSourceManager />;
      case 'stock-pools':
        return <StockPoolManager selectedPoolId={null} onSelectPool={() => {}} mode="manager" />;
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

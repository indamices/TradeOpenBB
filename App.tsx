import React, { useState, lazy, Suspense } from 'react';
import { Loader2 } from 'lucide-react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';  // 保留默认路由立即加载

// 懒加载非关键路由（按需加载，减少初始 bundle 大小）
// 优化：主 bundle 大小将从 670KB 减少到约 350KB（48% 减少）
const BacktestLab = lazy(() => import('./components/BacktestLab').then(m => ({ default: m.BacktestLab })));
const BacktestRecords = lazy(() => import('./components/BacktestRecords').then(m => ({ default: m.BacktestRecords })));
const ParameterOptimization = lazy(() => import('./components/ParameterOptimization').then(m => ({ default: m.ParameterOptimization })));
const AIChatAssistant = lazy(() => import('./components/AIChatAssistant').then(m => ({ default: m.AIChatAssistant })));
const StrategyLab = lazy(() => import('./components/StrategyLab').then(m => ({ default: m.StrategyLab })));
const StrategyManager = lazy(() => import('./components/StrategyManager').then(m => ({ default: m.StrategyManager })));
const AIModelSettings = lazy(() => import('./components/AIModelSettings').then(m => ({ default: m.AIModelSettings })));
const PortfolioManager = lazy(() => import('./components/PortfolioManager').then(m => ({ default: m.PortfolioManager })));
const DataSourceManager = lazy(() => import('./components/DataSourceManager').then(m => ({ default: m.DataSourceManager })));
const StockPoolManager = lazy(() => import('./components/StockPoolManager').then(m => ({ default: m.StockPoolManager })));
const HistoricalDataViewer = lazy(() => import('./components/HistoricalDataViewer').then(m => ({ default: m.HistoricalDataViewer })));

/**
 * 加载回退组件
 * 在懒加载组件加载时显示
 */
const LoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center h-screen bg-slate-900">
    <div className="text-center">
      <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
      <p className="text-slate-400">加载中...</p>
    </div>
  </div>
);

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'backtest':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <BacktestLab />
          </Suspense>
        );
      case 'backtest-records':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <BacktestRecords />
          </Suspense>
        );
      case 'parameter-optimization':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <ParameterOptimization />
          </Suspense>
        );
      case 'ai-chat':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <AIChatAssistant />
          </Suspense>
        );
      case 'strategy':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <StrategyLab />
          </Suspense>
        );
      case 'strategy-manager':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <StrategyManager />
          </Suspense>
        );
      case 'portfolio':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <PortfolioManager />
          </Suspense>
        );
      case 'ai-settings':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <AIModelSettings />
          </Suspense>
        );
      case 'data-sources':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <DataSourceManager />
          </Suspense>
        );
      case 'historical-data':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <HistoricalDataViewer />
          </Suspense>
        );
      case 'stock-pools':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <StockPoolManager selectedPoolId={null} onSelectPool={() => {}} mode="manager" />
          </Suspense>
        );
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

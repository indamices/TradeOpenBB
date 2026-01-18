import React from 'react';
import { LayoutDashboard, Settings, Menu, X, Wallet, TestTube, MessageSquare, FolderKanban, Database, Layers, FileText, BarChart3, SlidersHorizontal, Brain, History } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, activeTab, setActiveTab }) => {
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);

  const menuItems = [
    { id: 'dashboard', label: '数据可视化', icon: <LayoutDashboard size={20} /> },
    { id: 'backtest', label: '回测实验室', icon: <TestTube size={20} /> },
    { id: 'backtest-records', label: '回测记录', icon: <History size={20} /> },
    { id: 'parameter-optimization', label: '参数优化', icon: <SlidersHorizontal size={20} /> },
    { id: 'ai-chat', label: 'AI策略助手', icon: <MessageSquare size={20} /> },
    { id: 'historical-data', label: '历史数据', icon: <BarChart3 size={20} /> },
    { id: 'strategy-manager', label: '策略管理', icon: <FolderKanban size={20} /> },
    { id: 'portfolio', label: '投资组合', icon: <Wallet size={20} /> },
    { id: 'stock-pools', label: '股票池', icon: <Layers size={20} /> },
    { id: 'ai-settings', label: 'AI设置', icon: <Settings size={20} /> },
    { id: 'data-sources', label: '数据源', icon: <Database size={20} /> },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Mobile Header */}
      <div className="md:hidden fixed w-full bg-slate-900 z-50 px-4 py-3 flex items-center justify-between border-b border-slate-800">
        <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">SmartQuant</h1>
        <button onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
          {isSidebarOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 border-r border-slate-800 transform transition-transform duration-200 ease-in-out
        md:relative md:translate-x-0
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent hidden md:block">
            SmartQuant
          </h1>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">Personal Alpha</p>
        </div>

        <nav className="mt-6 px-3 space-y-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setIsSidebarOpen(false);
              }}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors duration-150
                ${activeTab === item.id 
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                }
              `}
            >
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full p-4 border-t border-slate-800">
          <div className="flex items-center space-x-2 text-slate-500 hover:text-slate-300 cursor-pointer">
            <Settings size={18} />
            <span className="text-sm">System Settings</span>
          </div>
          <div className="mt-4 text-[10px] text-slate-600">
            v1.0.0 | Connection: <span className="text-emerald-500">Active</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pt-16 md:pt-0 bg-slate-950">
        <div className="max-w-7xl mx-auto p-4 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;

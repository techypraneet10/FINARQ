import React from 'react';
import {
  LayoutDashboard,
  FileText,
  Building2,
  TrendingUp,
  GitCompare,
  BookOpen,
  FolderKanban,
  Activity,
  Database,
  CheckCircle2,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Logo } from '../brand/Logo';

export type NavigationTab =
  | 'dashboard'
  | 'ask'
  | 'documents'
  | 'companies'
  | 'analysis'
  | 'comparisons'
  | 'research'
  | 'collections'
  | 'jobs'
  | 'datasources'
  | 'evaluation'
  | 'admin'
  | 'settings'
  | 'landing';

export interface SidebarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  collapsed = false,
  onToggleCollapse,
}) => {
  const { hasPermission, role } = useAuth();

  const workspaceNavItems = [
    { id: 'dashboard' as NavigationTab, label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'ask' as NavigationTab, label: 'Ask FINARQ', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'documents' as NavigationTab, label: 'Documents', icon: <FileText className="w-4 h-4" /> },
    { id: 'companies' as NavigationTab, label: 'Companies', icon: <Building2 className="w-4 h-4" /> },
    { id: 'analysis' as NavigationTab, label: 'Financial Analysis', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'comparisons' as NavigationTab, label: 'Comparisons', icon: <GitCompare className="w-4 h-4" /> },
    { id: 'research' as NavigationTab, label: 'Research Library', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'collections' as NavigationTab, label: 'Collections', icon: <FolderKanban className="w-4 h-4" /> },
  ];

  const operationsNavItems = [
    { id: 'jobs' as NavigationTab, label: 'Ingestion Pipeline', icon: <Activity className="w-4 h-4" /> },
    { id: 'datasources' as NavigationTab, label: 'Data Sources', icon: <Database className="w-4 h-4" /> },
    { id: 'evaluation' as NavigationTab, label: 'RAG Evaluation', icon: <CheckCircle2 className="w-4 h-4" /> },
  ];

  const adminNavItems = [
    {
      id: 'admin' as NavigationTab,
      label: 'Audit & Governance',
      icon: <Shield className="w-4 h-4" />,
      visible: hasPermission('users:manage') || hasPermission('audit:read') || role === 'owner' || role === 'admin',
    },
    { id: 'settings' as NavigationTab, label: 'Settings', icon: <Settings className="w-4 h-4" /> },
  ];

  const renderNavGroup = (
    title: string,
    items: { id: NavigationTab; label: string; icon: React.ReactNode; visible?: boolean }[]
  ) => (
    <div className="flex flex-col gap-0.5">
      {!collapsed && (
        <span className="px-3 text-[10px] font-bold uppercase tracking-wider text-carbon-400 mb-1">
          {title}
        </span>
      )}
      {items
        .filter((i) => i.visible !== false)
        .map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all group relative ${
                isActive
                  ? 'bg-carbon-800 text-white font-semibold shadow-sm border border-carbon-600/80'
                  : 'text-carbon-300 hover:text-white hover:bg-carbon-850'
              }`}
              title={collapsed ? item.label : undefined}
            >
              {isActive && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r bg-lime-400 shadow-[0_0_8px_#d2f800]" />
              )}
              <span
                className={`shrink-0 transition-colors ${
                  isActive ? 'text-lime-400' : 'text-carbon-400 group-hover:text-carbon-200'
                }`}
              >
                {item.icon}
              </span>
              {!collapsed && <span className="truncate">{item.label}</span>}
            </button>
          );
        })}
    </div>
  );

  return (
    <aside
      className={`h-screen sticky top-0 flex flex-col bg-carbon-950 border-r border-carbon-700/60 transition-all duration-300 z-30 select-none ${
        collapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Brand Header */}
      <div className="h-14 flex items-center justify-between px-3.5 border-b border-carbon-700/60 shrink-0">
        <button
          onClick={() => onSelectTab('dashboard')}
          className="focus:outline-none flex items-center"
        >
          <Logo size={collapsed ? 'sm' : 'md'} showTagline={!collapsed} />
        </button>
        {onToggleCollapse && !collapsed && (
          <button
            onClick={onToggleCollapse}
            className="p-1 rounded text-carbon-400 hover:text-white hover:bg-carbon-800 transition-colors"
            title="Collapse Sidebar"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-2 py-3.5 flex flex-col gap-5">
        {renderNavGroup('Workspace', workspaceNavItems)}
        {renderNavGroup('Operations', operationsNavItems)}
        {renderNavGroup('Admin & Governance', adminNavItems)}
      </div>

      {/* Bottom Section */}
      <div className="p-2 border-t border-carbon-700/60 flex flex-col gap-1 shrink-0 bg-carbon-900/40">
        {/* Platform Showcase Link / Toggle */}
        <button
          onClick={() => onSelectTab('landing')}
          className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all text-carbon-400 hover:text-lime-300 hover:bg-carbon-800/50 ${
            activeTab === 'landing' ? 'text-lime-400 bg-carbon-800' : ''
          }`}
          title={collapsed ? 'Platform Overview' : undefined}
        >
          <ExternalLink className="w-3.5 h-3.5 shrink-0" />
          {!collapsed && <span className="truncate">Platform Overview</span>}
        </button>

        {/* Verified Pipeline Trust Badge */}
        {!collapsed && (
          <div className="mt-1 p-2 rounded-md bg-carbon-850 border border-carbon-700/60 text-[10px] text-carbon-300 flex items-center justify-between">
            <span className="flex items-center gap-1.5 font-semibold text-carbon-200">
              <span className="w-1.5 h-1.5 rounded-full bg-lime-400 shadow-[0_0_6px_#d2f800]" />
              Verified RAG Platform
            </span>
            <span className="font-mono text-carbon-400 text-[9px]">v1.0.0</span>
          </div>
        )}
      </div>
    </aside>
  );
};

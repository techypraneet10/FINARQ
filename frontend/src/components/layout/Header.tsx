import React, { useState, useEffect } from 'react';
import {
  Building2,
  ChevronDown,
  LogOut,
  Activity,
  User,
  Search,
  Bell,
  UploadCloud,
  CheckCircle,
  FileCheck2,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { Badge } from '../../design-system/Badge';
import { Button } from '../../design-system/Button';
import { NavigationTab } from './Sidebar';

export interface HeaderProps {
  activeTab?: NavigationTab;
  onOpenUpload?: () => void;
  onGlobalSearch?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab = 'dashboard', onOpenUpload, onGlobalSearch }) => {
  const { user, activeTenantId, role, logout } = useAuth();
  const [isReady, setIsReady] = useState<boolean | null>(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState<boolean>(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState<boolean>(false);

  useEffect(() => {
    const checkReadiness = async () => {
      try {
        const resp = await api.getReadiness();
        setIsReady(resp.status === 'ready');
      } catch {
        setIsReady(false);
      }
    };
    checkReadiness();
    const interval = setInterval(checkReadiness, 30000);
    return () => clearInterval(interval);
  }, []);

  const tabTitles: Record<NavigationTab, { group: string; title: string }> = {
    dashboard: { group: 'Workspace', title: 'Intelligence Overview' },
    ask: { group: 'Workspace', title: 'Ask FINARQ' },
    documents: { group: 'Workspace', title: 'Financial Document Repository' },
    companies: { group: 'Workspace', title: 'Company Profiles & Filings' },
    analysis: { group: 'Workspace', title: 'Financial Statement Analysis' },
    comparisons: { group: 'Workspace', title: 'Corporate Comparisons' },
    research: { group: 'Workspace', title: 'Research Library' },
    collections: { group: 'Workspace', title: 'Collections & Queries' },
    jobs: { group: 'Operations', title: 'Ingestion Pipeline' },
    datasources: { group: 'Operations', title: 'Enterprise Data Sources' },
    evaluation: { group: 'Operations', title: 'RAG Quality & Evaluation' },
    admin: { group: 'Admin & Governance', title: 'Audit Logs & Governance' },
    settings: { group: 'Admin & Governance', title: 'Platform Settings' },
    landing: { group: 'Platform', title: 'Platform Overview' },
  };

  const currentTabInfo = tabTitles[activeTab] || { group: 'Workspace', title: 'Overview' };

  const recentNotifications = [
    {
      id: 'notif-1',
      title: 'Filing Ingestion Complete',
      desc: 'Apple Inc. Form 10-K (FY2025) parsed & 184 chunks indexed.',
      time: '12m ago',
      icon: <FileCheck2 className="w-3.5 h-3.5 text-lime-400" />,
    },
    {
      id: 'notif-2',
      title: 'RAG Evaluation Benchmark',
      desc: 'Golden Dataset evaluation passed with 97.1% citation accuracy.',
      time: '1h ago',
      icon: <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />,
    },
    {
      id: 'notif-3',
      title: 'Vector Store Optimized',
      desc: 'Qdrant collection payload indices compacted successfully.',
      time: '4h ago',
      icon: <Activity className="w-3.5 h-3.5 text-cyan-400" />,
    },
  ];

  return (
    <header className="h-14 px-4 border-b border-carbon-700/60 bg-carbon-950/90 backdrop-blur-md flex items-center justify-between sticky top-0 z-20 select-none">
      {/* Left: Breadcrumbs & Organization */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="flex items-center gap-1.5 text-xs text-carbon-400 font-medium truncate">
          <span className="text-carbon-400 font-mono text-[11px] uppercase tracking-wider">{currentTabInfo.group}</span>
          <span className="text-carbon-600">/</span>
          <span className="text-carbon-100 font-semibold">{currentTabInfo.title}</span>
        </div>

        <div className="hidden lg:flex items-center gap-2 px-2 py-0.5 rounded-md bg-carbon-900 border border-carbon-700/70 text-[11px] text-carbon-300">
          <Building2 className="w-3 h-3 text-lime-400 shrink-0" />
          <span className="text-carbon-400">Org:</span>
          <span className="font-semibold text-carbon-200 font-mono truncate max-w-[130px]">
            {activeTenantId ? `tenant-${activeTenantId.substring(0, 8)}` : 'Alpha Capital'}
          </span>
        </div>
      </div>

      {/* Center: Global Command Search Trigger */}
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <button
          onClick={onGlobalSearch}
          className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg bg-carbon-900/90 hover:bg-carbon-850 border border-carbon-700/70 hover:border-carbon-500 text-xs text-carbon-400 hover:text-carbon-200 transition-all shadow-inner group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <Search className="w-3.5 h-3.5 text-carbon-400 group-hover:text-lime-400 transition-colors shrink-0" />
            <span className="truncate text-[11px]">Search documents, companies, filings...</span>
          </div>
          <kbd className="px-1.5 py-0.5 rounded bg-carbon-800 text-[10px] font-mono text-carbon-400 border border-carbon-700 shrink-0">
            Ctrl+K
          </kbd>
        </button>
      </div>

      {/* Right: Actions, System Health, Notifications, Profile */}
      <div className="flex items-center gap-2.5">
        {onOpenUpload && (
          <Button
            variant="primary"
            size="xs"
            onClick={onOpenUpload}
            icon={<UploadCloud className="w-3.5 h-3.5" />}
          >
            Upload Document
          </Button>
        )}

        {/* Subtle System Status Pill */}
        <div
          className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono border ${
            isReady === true
              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30'
              : isReady === false
              ? 'bg-rose-950/40 text-rose-300 border-rose-500/30'
              : 'bg-carbon-900 text-carbon-400 border-carbon-700/70'
          }`}
          title="Downstream Services: Qdrant, PostgreSQL, AST Engine, S3 Blob"
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isReady === true ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
            }`}
          />
          <span className="font-semibold tracking-wide">
            {isReady === true ? 'All systems operational' : isReady === false ? 'System degraded' : 'Checking status'}
          </span>
        </div>

        {/* Notifications Bell */}
        <div className="relative">
          <button
            onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
            className="p-1.5 rounded-lg text-carbon-400 hover:text-white hover:bg-carbon-800 border border-transparent hover:border-carbon-600 transition-colors relative"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-lime-400 shadow-[0_0_6px_#d2f800]" />
          </button>

          {isNotificationsOpen && (
            <>
              <div
                className="fixed inset-0 z-30"
                onClick={() => setIsNotificationsOpen(false)}
                aria-hidden="true"
              />
              <div className="absolute right-0 mt-2 w-80 bg-carbon-900 border border-carbon-700 rounded-xl shadow-2xl z-40 py-2 text-xs animate-fade-in divide-y divide-carbon-800">
                <div className="px-3.5 py-1.5 flex items-center justify-between">
                  <span className="font-bold text-carbon-100 uppercase tracking-wider text-[11px]">Notifications</span>
                  <span className="text-[10px] font-mono text-lime-400 font-semibold">3 New</span>
                </div>
                <div className="p-1.5 flex flex-col gap-1 max-h-72 overflow-y-auto">
                  {recentNotifications.map((n) => (
                    <div
                      key={n.id}
                      className="p-2.5 rounded-lg hover:bg-carbon-800 transition-colors flex items-start gap-2.5 cursor-pointer"
                    >
                      <div className="p-1.5 rounded-md bg-carbon-850 border border-carbon-700 shrink-0 mt-0.5">
                        {n.icon}
                      </div>
                      <div className="flex flex-col min-w-0 gap-0.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-semibold text-carbon-100 truncate text-[11px]">{n.title}</span>
                          <span className="text-[9px] font-mono text-carbon-400 shrink-0">{n.time}</span>
                        </div>
                        <p className="text-[10px] text-carbon-300 leading-tight">{n.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className="flex items-center gap-2 px-2 py-1 rounded-lg bg-carbon-900 hover:bg-carbon-800 border border-carbon-700/70 text-xs text-carbon-200 transition-colors"
          >
            <div className="w-5 h-5 rounded-full bg-carbon-800 border border-lime-400/40 text-lime-400 flex items-center justify-center font-bold text-[10px]">
              {user?.email?.charAt(0).toUpperCase() || <User className="w-3 h-3" />}
            </div>
            <span className="font-medium max-w-[90px] truncate hidden sm:inline">{user?.email?.split('@')[0] || 'Analyst'}</span>
            <ChevronDown className="w-3 h-3 text-carbon-400" />
          </button>

          {isUserMenuOpen && (
            <>
              <div
                className="fixed inset-0 z-30"
                onClick={() => setIsUserMenuOpen(false)}
                aria-hidden="true"
              />
              <div className="absolute right-0 mt-2 w-60 bg-carbon-900 border border-carbon-700 rounded-xl shadow-2xl z-40 py-1 text-xs animate-fade-in divide-y divide-carbon-800">
                <div className="px-3.5 py-2.5 flex flex-col gap-0.5">
                  <span className="font-semibold text-carbon-100 truncate">{user?.email || 'analyst@finarq.io'}</span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-carbon-400 font-mono text-[10px] truncate">
                      Tenant: {activeTenantId ? `tenant-${activeTenantId.substring(0, 8)}` : 'Alpha Capital'}
                    </span>
                    {role && (
                      <Badge variant="lime" size="xs">
                        {role}
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="p-1">
                  <button
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-rose-400 hover:bg-rose-950/40 rounded-lg transition-colors text-xs font-medium"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Secure Sign Out</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

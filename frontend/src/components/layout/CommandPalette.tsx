import React, { useState, useEffect } from 'react';
import {
  Search,
  FileText,
  Building2,
  TrendingUp,
  Sparkles,
  GitCompare,
  FolderKanban,
  CheckCircle2,
  Shield,
  Activity,
  ArrowRight,
  Command,
} from 'lucide-react';
import { NavigationTab } from './Sidebar';

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (tab: NavigationTab, param?: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  const [search, setSearch] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const quickItems = [
    { type: 'Page', title: 'Overview Dashboard', tab: 'dashboard' as NavigationTab, icon: <Activity className="w-4 h-4 text-lime-400" /> },
    { type: 'Page', title: 'Ask AI Research Workspace', tab: 'ask' as NavigationTab, icon: <Sparkles className="w-4 h-4 text-lime-400" /> },
    { type: 'Page', title: 'Document Repository', tab: 'documents' as NavigationTab, icon: <FileText className="w-4 h-4 text-cyan-400" /> },
    { type: 'Page', title: 'Company Intelligence', tab: 'companies' as NavigationTab, icon: <Building2 className="w-4 h-4 text-cyan-400" /> },
    { type: 'Page', title: 'Financial Analysis', tab: 'analysis' as NavigationTab, icon: <TrendingUp className="w-4 h-4 text-lime-400" /> },
    { type: 'Page', title: 'Corporate Comparisons', tab: 'comparisons' as NavigationTab, icon: <GitCompare className="w-4 h-4 text-cyan-300" /> },
    { type: 'Company', title: 'Apple Inc. (AAPL) — Form 10-K', tab: 'companies' as NavigationTab, param: 'AAPL', icon: <Building2 className="w-4 h-4 text-lime-400" /> },
    { type: 'Company', title: 'Microsoft Corp (MSFT) — Form 10-K', tab: 'companies' as NavigationTab, param: 'MSFT', icon: <Building2 className="w-4 h-4 text-lime-400" /> },
    { type: 'Company', title: 'NVIDIA Corp (NVDA) — Form 10-K', tab: 'companies' as NavigationTab, param: 'NVDA', icon: <Building2 className="w-4 h-4 text-lime-400" /> },
    { type: 'AI Query', title: "What was Apple's revenue growth from 2023 to 2025?", tab: 'ask' as NavigationTab, param: "What was Apple's revenue growth from 2023 to 2025?", icon: <Sparkles className="w-4 h-4 text-lime-400" /> },
    { type: 'AI Query', title: 'Compare Microsoft Cloud vs AWS revenue run-rate', tab: 'ask' as NavigationTab, param: 'Compare Microsoft Cloud vs AWS revenue run-rate', icon: <Sparkles className="w-4 h-4 text-lime-400" /> },
    { type: 'System', title: 'RAG Evaluation Quality Suite', tab: 'evaluation' as NavigationTab, icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" /> },
    { type: 'System', title: 'Ingestion Pipeline & Async Jobs', tab: 'jobs' as NavigationTab, icon: <Activity className="w-4 h-4 text-cyan-400" /> },
  ];

  const filtered = quickItems.filter(
    (i) =>
      !search ||
      i.title.toLowerCase().includes(search.toLowerCase()) ||
      i.type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-start justify-center pt-20 px-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-carbon-900 border border-carbon-600 rounded-2xl shadow-2xl overflow-hidden flex flex-col gap-0 text-carbon-100"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-carbon-700 bg-carbon-950">
          <Search className="w-4 h-4 text-lime-400 shrink-0" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents, companies, filings, or financial queries..."
            autoFocus
            className="flex-1 bg-transparent text-white placeholder-carbon-400 text-sm focus:outline-none"
          />
          <kbd className="px-2 py-0.5 rounded bg-carbon-800 text-[10px] font-mono text-carbon-400 border border-carbon-700">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 flex flex-col gap-1">
          {filtered.length > 0 ? (
            filtered.map((item, idx) => (
              <button
                key={idx}
                onClick={() => {
                  onNavigate(item.tab, item.param);
                  onClose();
                }}
                className="w-full p-2.5 rounded-lg hover:bg-carbon-800 text-left transition-colors flex items-center justify-between group"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="p-1.5 rounded-md bg-carbon-950 border border-carbon-700 text-carbon-300 group-hover:border-lime-400/50 transition-colors">
                    {item.icon}
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-semibold text-white group-hover:text-lime-300 transition-colors truncate">
                      {item.title}
                    </span>
                    <span className="text-[10px] text-carbon-400 font-mono">
                      {item.type}
                    </span>
                  </div>
                </div>

                <ArrowRight className="w-3.5 h-3.5 text-carbon-500 group-hover:text-lime-400 group-hover:translate-x-0.5 transition-transform" />
              </button>
            ))
          ) : (
            <div className="py-8 text-center text-xs text-carbon-400">
              No matching documents or commands found.
            </div>
          )}
        </div>

        {/* Command Palette Footer */}
        <div className="px-4 py-2 bg-carbon-950 border-t border-carbon-700/60 flex items-center justify-between text-[11px] font-mono text-carbon-400">
          <span>Navigate with <kbd className="px-1 rounded bg-carbon-800 text-carbon-300">↑</kbd> <kbd className="px-1 rounded bg-carbon-800 text-carbon-300">↓</kbd></span>
          <span>Press <kbd className="px-1.5 py-0.5 rounded bg-carbon-800 text-carbon-300 font-bold">↵</kbd> to select</span>
        </div>
      </div>
    </div>
  );
};

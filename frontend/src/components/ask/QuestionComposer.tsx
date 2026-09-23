import React, { useState } from 'react';
import { ResponseStyle } from '../../api/types';
import {
  Sparkles,
  Send,
  ChevronDown,
  ChevronUp,
  SlidersHorizontal,
} from 'lucide-react';
import { Button } from '../../design-system/Button';

export interface QuestionComposerProps {
  onSubmit: (query: string, options: { style: ResponseStyle; filters?: any }) => void;
  loading: boolean;
  initialQuery?: string;
  selectedCompanies?: string[];
  onToggleCompany?: (company: string) => void;
}

export const QuestionComposer: React.FC<QuestionComposerProps> = ({
  onSubmit,
  loading,
  initialQuery = '',
  selectedCompanies = [],
  onToggleCompany,
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [responseStyle, setResponseStyle] = useState<ResponseStyle>('standard');
  const [retrievalMode, setRetrievalMode] = useState<'hybrid' | 'dense' | 'exact'>('hybrid');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('all');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  const suggestedQueries = [
    "What was Apple's revenue growth from 2023 to 2025?",
    'Compare Microsoft Cloud vs AWS revenue run-rate for FY2024.',
    'Calculate NVIDIA Datacenter segment gross profit margin.',
    'What was JPMorgan Chase Common Equity Tier 1 (CET1) capital ratio?',
  ];

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    onSubmit(query.trim(), {
      style: responseStyle,
      filters: {
        companies: selectedCompanies.length > 0 ? selectedCompanies : undefined,
        period: selectedPeriod !== 'all' ? selectedPeriod : undefined,
        retrieval_mode: retrievalMode,
      },
    });
  };

  return (
    <div className="flex flex-col gap-3 p-5 rounded-2xl bg-carbon-900 border border-carbon-700/60 shadow-lg text-carbon-100">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {/* Main Input Composer */}
        <div className="relative flex items-start gap-3 bg-carbon-950 p-3.5 rounded-xl border border-carbon-700/60 focus-within:border-lime-400/60 focus-within:ring-1 focus-within:ring-lime-400/20 transition-all">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="Ask a financial question across verified filings (e.g. revenue growth, segment margin, period comparisons)..."
            rows={2}
            className="flex-1 bg-transparent text-white placeholder-carbon-400 text-sm leading-relaxed resize-none focus:outline-none"
            disabled={loading}
          />
          <Button
            type="submit"
            variant="lime"
            size="sm"
            loading={loading}
            disabled={!query.trim() || loading}
            icon={<Send className="w-3.5 h-3.5" />}
            className="self-end shrink-0 font-semibold"
          >
            Ask FINARQ
          </Button>
        </div>

        {/* Collapsible Advanced Options Header */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-1.5 text-xs text-carbon-400 hover:text-carbon-200 transition-colors font-medium select-none"
          >
            <SlidersHorizontal className="w-3 h-3 text-lime-400/80" />
            <span>Advanced Research Options</span>
            {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          <span className="text-[11px] text-carbon-400 font-mono hidden sm:inline">
            Press <kbd className="px-1 py-0.5 rounded bg-carbon-800 border border-carbon-700 text-carbon-300 font-sans text-[10px]">Enter ↵</kbd> to search
          </span>
        </div>

        {/* Collapsible Advanced Options Body */}
        {showAdvanced && (
          <div className="p-3.5 rounded-xl bg-carbon-950/80 border border-carbon-700/60 flex flex-wrap items-center gap-3 animate-fade-in text-xs">
            {/* Response Style */}
            <div className="flex items-center gap-2 bg-carbon-900 border border-carbon-700/60 rounded-lg px-2.5 py-1.5">
              <span className="text-carbon-400 text-[11px] font-medium">Format:</span>
              <select
                value={responseStyle}
                onChange={(e) => setResponseStyle(e.target.value as ResponseStyle)}
                className="bg-transparent text-white text-xs focus:outline-none cursor-pointer"
              >
                <option value="standard" className="bg-carbon-900 text-white">Standard (Answer + Math + Citations)</option>
                <option value="concise" className="bg-carbon-900 text-white">Concise (Direct Summary)</option>
                <option value="detailed" className="bg-carbon-900 text-white">Detailed (Full Grounding)</option>
                <option value="analytical" className="bg-carbon-900 text-white">Analytical (Multi-Period Synthesis)</option>
              </select>
            </div>

            {/* Retrieval Strategy */}
            <div className="flex items-center gap-2 bg-carbon-900 border border-carbon-700/60 rounded-lg px-2.5 py-1.5">
              <span className="text-carbon-400 text-[11px] font-medium">Search:</span>
              <select
                value={retrievalMode}
                onChange={(e) => setRetrievalMode(e.target.value as any)}
                className="bg-transparent text-lime-400 text-xs font-medium focus:outline-none cursor-pointer"
              >
                <option value="hybrid" className="bg-carbon-900 text-white">Hybrid Search</option>
                <option value="dense" className="bg-carbon-900 text-white">Semantic Search (Vector)</option>
                <option value="exact" className="bg-carbon-900 text-white">Exact Keyword (BM25)</option>
              </select>
            </div>

            {/* Target Filing Period */}
            <div className="flex items-center gap-2 bg-carbon-900 border border-carbon-700/60 rounded-lg px-2.5 py-1.5">
              <span className="text-carbon-400 text-[11px] font-medium">Period:</span>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="bg-transparent text-white text-xs focus:outline-none cursor-pointer"
              >
                <option value="all" className="bg-carbon-900 text-white">All Filing Periods</option>
                <option value="FY2025" className="bg-carbon-900 text-white">FY2025</option>
                <option value="FY2024" className="bg-carbon-900 text-white">FY2024</option>
                <option value="FY2023" className="bg-carbon-900 text-white">FY2023</option>
              </select>
            </div>
          </div>
        )}
      </form>

      {/* Suggested Inquiries */}
      <div className="flex items-center gap-1.5 flex-wrap pt-1.5 border-t border-carbon-700/40">
        <span className="text-[11px] text-carbon-400 font-medium flex items-center gap-1 shrink-0">
          <Sparkles className="w-3 h-3 text-lime-400" /> Suggested:
        </span>
        {suggestedQueries.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setQuery(q)}
            className="text-[11px] px-2.5 py-1 rounded-lg bg-carbon-800/80 hover:bg-carbon-750 border border-carbon-700/50 hover:border-lime-400/40 text-carbon-300 hover:text-white transition-all truncate max-w-xs"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
};


import React, { useState } from 'react';
import {
  FolderKanban,
  FileText,
  Sparkles,
  ArrowRight,
  Plus,
  Building2,
  Calendar,
  Layers,
  ChevronRight,
  Search,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Input } from '../../design-system/Input';

export interface CollectionsViewProps {
  onNavigateToAsk?: (query?: string) => void;
  onNavigateToDocument?: (docId: string) => void;
}

export const CollectionsView: React.FC<CollectionsViewProps> = ({
  onNavigateToAsk,
  onNavigateToDocument,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const collections = [
    {
      id: 'col-mag7',
      title: 'S&P 500 Mag 7 FY2025 Annual Filings',
      description: 'Comprehensive 10-K disclosures for Apple, Microsoft, NVIDIA, Amazon, Alphabet, Meta, and Tesla.',
      docCount: 14,
      entityCount: 7,
      updatedAt: '2 hours ago',
      tags: ['Mag 7', '10-K', 'FY2025', 'Tech'],
      sampleQuery: 'Compare capital expenditure on AI infrastructure across Mag 7 companies in FY2025.',
    },
    {
      id: 'col-semi',
      title: 'Semiconductor Supply Chain & Fab Capacity',
      description: 'Annual reports and quarterly filings for NVIDIA, TSMC, ASML, AMD, and Intel.',
      docCount: 12,
      entityCount: 5,
      updatedAt: 'Yesterday',
      tags: ['Semiconductors', 'Hardware', 'CapEx'],
      sampleQuery: 'What are the reported lead times and gross margin trends across semiconductor equipment makers?',
    },
    {
      id: 'col-banking',
      title: 'Tier 1 Global Banking Capital Adequacy (Basel III)',
      description: 'Audited filings covering JPMorgan Chase, Bank of America, Goldman Sachs, and Morgan Stanley.',
      docCount: 16,
      entityCount: 4,
      updatedAt: '3 days ago',
      tags: ['Banking', 'CET1', 'Liquidity', 'Risk'],
      sampleQuery: 'Compare Common Equity Tier 1 (CET1) capital ratios across major US money-center banks.',
    },
    {
      id: 'col-cloud',
      title: 'Enterprise Cloud Infrastructure & Hyperscaler Runtimes',
      description: 'Quarterly segmented revenue disclosures for AWS, Microsoft Intelligent Cloud, and Google Cloud.',
      docCount: 18,
      entityCount: 3,
      updatedAt: 'Sep 14, 2026',
      tags: ['Cloud', 'AWS', 'Azure', 'GCP'],
      sampleQuery: 'Calculate annualized revenue run-rates and operating margins for AWS vs Azure vs GCP.',
    },
  ];

  const filtered = collections.filter(
    (c) =>
      !searchQuery ||
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Document Collections</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-carbon-800 text-lime-400 border border-carbon-600">
              {collections.length} Curated Workspaces
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            Grouped corporate filing cohorts for cross-company comparative retrieval and multi-document synthesis.
          </p>
        </div>

        <Button
          variant="lime"
          size="sm"
          onClick={() => alert('New Collection modal initialized.')}
          icon={<Plus className="w-3.5 h-3.5" />}
        >
          Create Collection
        </Button>
      </div>

      {/* Search Bar */}
      <div className="p-3 rounded-xl bg-carbon-900 border border-carbon-600/90 shadow-sm">
        <Input
          placeholder="Search collections or thematic tags (e.g. Mag 7, Cloud, Banking)..."
          icon={<Search className="w-4 h-4 text-carbon-400" />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Grid of Collection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((col) => (
          <div
            key={col.id}
            className="p-5 rounded-xl bg-carbon-900 border border-carbon-600/80 hover:border-carbon-400/90 transition-all flex flex-col justify-between gap-4 group shadow-sm"
          >
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-carbon-800 border border-carbon-600 text-lime-400 group-hover:border-lime-400/60 transition-colors">
                    <FolderKanban className="w-4 h-4" />
                  </div>
                  <span className="font-bold text-sm text-white group-hover:text-lime-300 transition-colors">
                    {col.title}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-carbon-400">{col.updatedAt}</span>
              </div>

              <p className="text-xs text-carbon-300 leading-relaxed font-sans">
                {col.description}
              </p>

              <div className="flex items-center gap-1.5 flex-wrap pt-1">
                {col.tags.map((t, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded text-[10px] font-mono bg-carbon-800 text-carbon-300 border border-carbon-700"
                  >
                    #{t}
                  </span>
                ))}
              </div>
            </div>

            {/* Bottom Actions & Query Shortcut */}
            <div className="pt-3 border-t border-carbon-700/50 flex flex-col gap-2.5">
              <div className="flex items-center justify-between text-[11px] font-mono text-carbon-400">
                <span className="flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-lime-400" /> {col.docCount} Filings
                </span>
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-cyan-400" /> {col.entityCount} Tracked Entities
                </span>
              </div>

              <button
                onClick={() => onNavigateToAsk?.(col.sampleQuery)}
                className="w-full p-2 rounded-lg bg-carbon-800/90 hover:bg-carbon-700 border border-carbon-600/70 hover:border-lime-400/60 text-left text-xs text-white transition-all flex items-center justify-between group/btn"
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  <Sparkles className="w-3.5 h-3.5 text-lime-400 shrink-0" />
                  <span className="truncate font-medium">Ask: "{col.sampleQuery}"</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-lime-400 shrink-0 group-hover/btn:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

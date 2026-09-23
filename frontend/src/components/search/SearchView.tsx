import React, { useState } from 'react';
import {
  RetrievalSearchResponse,
  RetrievalFilterRequest,
} from '../../api/types';
import { api } from '../../api/client';
import {
  Search,
  SlidersHorizontal,
  Sparkles,
  Layers,
  Clock,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Input } from '../../design-system/Input';
import { Badge } from '../../design-system/Badge';
import { RankedEvidenceCard } from './RankedEvidenceCard';
import { SearchFilters } from './SearchFilters';
import { useWorkspace } from '../../context/WorkspaceContext';

export interface SearchViewProps {
  onNavigateToDocument?: (documentId: string, pageNumber?: number) => void;
  onAskQuestion?: (queryText: string) => void;
}

export const SearchView: React.FC<SearchViewProps> = ({
  onNavigateToDocument,
  onAskQuestion,
}) => {
  const { notify } = useWorkspace();
  const [query, setQuery] = useState<string>('');
  const [filters, setFilters] = useState<RetrievalFilterRequest>({});
  const [showFilters, setShowFilters] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [searchResult, setSearchResult] = useState<RetrievalSearchResponse | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || query.trim().length < 2) {
      notify('info', 'Please enter a search query (minimum 2 characters).');
      return;
    }

    setLoading(true);
    try {
      const resp = await api.searchEvidence({
        query: query.trim(),
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        top_k: 15,
        use_reranker: true,
      });
      setSearchResult(resp);
    } catch (err: any) {
      notify('error', err.message || 'Search execution failed.');
    } finally {
      setLoading(false);
    }
  };

  const sampleSearches = [
    'Apple total net sales breakdown by product',
    'Operating income and gross margin trends',
    'Research and development expense 2024',
    'Cash flow from operating activities',
  ];

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Search Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-100">Financial Document Search</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Execute hybrid retrieval across dense semantic embeddings (Qdrant) and lexical keyword matching (BM25) with Reciprocal Rank Fusion.
        </p>
      </div>

      {/* Query Bar Form */}
      <form onSubmit={handleSearch} className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <Input
              placeholder="Search financial metrics, balance sheet items, or filing disclosures..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              icon={<Search className="w-4 h-4" />}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            icon={<SlidersHorizontal className="w-4 h-4" />}
          >
            Filters
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={loading}
            icon={<ArrowRight className="w-4 h-4" />}
          >
            Search Evidence
          </Button>
        </div>

        {/* Collapsible Filter Panel */}
        {showFilters && (
          <SearchFilters
            filters={filters}
            onChange={setFilters}
            onClear={() => setFilters({})}
          />
        )}

        {/* Sample Quick Searches */}
        {!searchResult && (
          <div className="flex items-center gap-2 flex-wrap pt-1">
            <span className="text-xs text-slate-500 font-medium">Try searching:</span>
            {sampleSearches.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(sample);
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 transition-colors"
              >
                {sample}
              </button>
            ))}
          </div>
        )}
      </form>

      {/* Financial Signals & Retrieval Strategy Bar */}
      {searchResult && (
        <div className="flex flex-col gap-4 p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                Extracted Financial Signals:
              </span>
              {searchResult.signals.tickers.map((t) => (
                <Badge key={t} variant="emerald" size="xs">
                  Ticker: {t}
                </Badge>
              ))}
              {searchResult.signals.metrics.map((m) => (
                <Badge key={m} variant="cyan" size="xs">
                  Metric: {m}
                </Badge>
              ))}
              {searchResult.signals.fiscal_years.map((y) => (
                <Badge key={y} variant="amber" size="xs">
                  FY {y}
                </Badge>
              ))}
              {searchResult.signals.is_comparison && (
                <Badge variant="purple" size="xs" icon={<TrendingUp className="w-3 h-3" />}>
                  Comparative Intent
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
              <span>{searchResult.evidence_count} evidence chunks</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-500" />
                {Object.values(searchResult.timing_ms).reduce((a, b) => a + b, 0).toFixed(1)}ms
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Evidence Results Grid */}
      {searchResult && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Ranked Evidence Set (RRF Fusion + Reranking)
            </h3>
            {onAskQuestion && (
              <Button
                variant="emerald"
                size="sm"
                onClick={() => onAskQuestion(query)}
                icon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                Synthesize Verified Answer from Query
              </Button>
            )}
          </div>

          <div className="flex flex-col gap-4">
            {searchResult.evidence.map((item) => (
              <RankedEvidenceCard
                key={item.chunk_id}
                evidence={item}
                onNavigateToDocument={onNavigateToDocument}
                onAskFollowUp={onAskQuestion}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

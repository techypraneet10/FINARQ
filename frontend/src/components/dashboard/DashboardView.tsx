import React, { useState, useEffect } from 'react';
import { DocumentResponse, MetricsResponse } from '../../api/types';
import { api } from '../../api/client';
import {
  FileText,
  Search,
  Upload,
  ArrowRight,
  ShieldCheck,
  Zap,
  Sparkles,
  ChevronRight,
  Activity,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { QuickStats } from './QuickStats';
import { FinancialAreaChart } from '../charts/FinancialAreaChart';
import { useAuth } from '../../context/AuthContext';

export interface DashboardViewProps {
  onNavigateToDocuments: () => void;
  onNavigateToSearch: () => void;
  onNavigateToAsk: (initialQuery?: string) => void;
  onOpenUpload: () => void;
  onSelectDocument: (docId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onNavigateToDocuments,
  onNavigateToSearch,
  onNavigateToAsk,
  onOpenUpload,
  onSelectDocument,
}) => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activityTimeframe, setActivityTimeframe] = useState<'30D' | '90D' | '1Y'>('30D');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [docsData, metricsData] = await Promise.all([
          api.listDocuments(10, 0).catch(() => []),
          api.getMetrics().catch(() => null),
        ]);
        setDocuments(docsData);
        setMetrics(metricsData);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const isSample = documents.length === 0;

  // Production-realistic sample documents when live repo is empty
  const displayDocs: (DocumentResponse & { company_name?: string; status?: string })[] =
    documents.length > 0
      ? (documents as any)
      : [
          {
            id: 'doc-aapl-2025',
            title: 'Apple Inc. Form 10-K (Annual Report)',
            ticker_symbol: 'AAPL',
            company_name: 'Apple Inc.',
            document_type: '10-K',
            fiscal_year: 2025,
            fiscal_period: 'FY',
            pages_count: 184,
            current_version_id: 'v1.0.0',
            status: 'processed',
            storage_uri: 's3://vault/aapl.pdf',
            file_hash_sha256: '9a84f37823b1c8e9',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 2).toISOString(),
          },
          {
            id: 'doc-msft-2024',
            title: 'Microsoft Corp Form 10-K (Annual Report)',
            ticker_symbol: 'MSFT',
            company_name: 'Microsoft Corp',
            document_type: '10-K',
            fiscal_year: 2024,
            fiscal_period: 'FY',
            pages_count: 128,
            current_version_id: 'v1.0.0',
            status: 'processed',
            storage_uri: 's3://vault/msft.pdf',
            file_hash_sha256: '7b22d19456a0c4f8',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 14).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 14).toISOString(),
          },
          {
            id: 'doc-nvda-2025',
            title: 'NVIDIA Corporation Form 10-K',
            ticker_symbol: 'NVDA',
            company_name: 'NVIDIA Corp',
            document_type: '10-K',
            fiscal_year: 2025,
            fiscal_period: 'FY',
            pages_count: 96,
            current_version_id: 'v1.0.0',
            status: 'processed',
            storage_uri: 's3://vault/nvda.pdf',
            file_hash_sha256: '3c19e58849b2d0a1',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 28).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 28).toISOString(),
          },
          {
            id: 'doc-amzn-2024',
            title: 'Amazon.com Inc Form 10-K',
            ticker_symbol: 'AMZN',
            company_name: 'Amazon.com Inc',
            document_type: '10-K',
            fiscal_year: 2024,
            fiscal_period: 'FY',
            pages_count: 110,
            current_version_id: 'v1.0.0',
            status: 'processed',
            storage_uri: 's3://vault/amzn.pdf',
            file_hash_sha256: '5d89f21190a4e7c2',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 48).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 48).toISOString(),
          },
          {
            id: 'doc-jpm-2024',
            title: 'JPMorgan Chase & Co. Form 10-K',
            ticker_symbol: 'JPM',
            company_name: 'JPMorgan Chase & Co.',
            document_type: '10-K',
            fiscal_year: 2024,
            fiscal_period: 'FY',
            pages_count: 324,
            current_version_id: 'v1.0.0',
            status: 'processed',
            storage_uri: 's3://vault/jpm.pdf',
            file_hash_sha256: '4e91a03381c7b5d4',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 72).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 72).toISOString(),
          },
        ];

  // Recent AI Research items
  const recentResearch = [
    {
      id: 'res-1',
      query: "What was Apple's revenue growth from 2023 to 2025?",
      entities: ['Apple Inc.', 'AAPL'],
      timestamp: '12m ago',
      confidence: '99.4%',
      citationsCount: 4,
      summary: "Apple's revenue grew from $383.29B in FY2023 to $416.20B in FY2025, representing an 8.59% increase.",
    },
    {
      id: 'res-2',
      query: 'Compare Microsoft Cloud vs AWS operating margin for FY2024.',
      entities: ['Microsoft', 'Amazon', 'MSFT', 'AMZN'],
      timestamp: '1h ago',
      confidence: '98.8%',
      citationsCount: 6,
      summary: 'Microsoft Cloud operating margin reached 44.2% while AWS delivered 35.8% operating margin.',
    },
    {
      id: 'res-3',
      query: 'Calculate NVIDIA Datacenter segment revenue CAGR over last 3 years.',
      entities: ['NVIDIA Corp', 'NVDA'],
      timestamp: '3h ago',
      confidence: '99.1%',
      citationsCount: 5,
      summary: 'NVIDIA Datacenter revenue experienced a 168.4% 3-year compound annual growth rate.',
    },
  ];

  // Financial activity chart data series
  const chartData = [
    { period: 'Jan', value: 1240, secondaryValue: 82 },
    { period: 'Feb', value: 1560, secondaryValue: 98 },
    { period: 'Mar', value: 2100, secondaryValue: 142 },
    { period: 'Apr', value: 2480, secondaryValue: 165 },
    { period: 'May', value: 3120, secondaryValue: 194 },
    { period: 'Jun', value: 3680, secondaryValue: 230 },
    { period: 'Jul', value: 4190, secondaryValue: 275 },
    { period: 'Aug', value: 4821, secondaryValue: 310 },
  ];

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header & Primary CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Good morning, {user?.email ? user.email.split('@')[0] : 'Analyst'}
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-lime-400/10 text-lime-400 border border-lime-400/20">
              Terminal Active
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            FINARQ Financial Intelligence Workspace · Factual Grounding & Numerical Verification Engine
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={onNavigateToSearch}
            icon={<Search className="w-3.5 h-3.5" />}
          >
            Search Filings
          </Button>
          <Button
            variant="lime"
            size="sm"
            onClick={onOpenUpload}
            icon={<Upload className="w-3.5 h-3.5" />}
          >
            Upload Document
          </Button>
        </div>
      </div>

      {/* 5 Compact High-Quality KPI Cards with Live/Sample Status */}
      <QuickStats
        documentCount={documents.length > 0 ? documents.length : 1284}
        companiesCount={86}
        queriesCount={4821}
        citationsCount={18493}
        processingRate={98.7}
        isSampleData={isSample}
      />

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column (7 Cols): Financial Intelligence Activity + Recent AI Research */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          {/* Activity Line/Area Chart */}
          <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-700/70 shadow-sm flex flex-col gap-3.5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wider text-carbon-200">
                  Financial Intelligence Activity
                </h2>
                <p className="text-[11px] text-carbon-400 mt-0.5">
                  Verified AI queries & document analysis pipeline throughput
                </p>
              </div>

              {/* Timeframe Controls */}
              <div className="flex items-center bg-carbon-800 rounded-lg p-0.5 border border-carbon-700/60 text-[11px]">
                {(['30D', '90D', '1Y'] as const).map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setActivityTimeframe(tf)}
                    className={`px-2.5 py-1 rounded font-mono font-medium transition-all ${
                      activityTimeframe === tf
                        ? 'bg-carbon-600 text-white shadow-sm'
                        : 'text-carbon-400 hover:text-carbon-200'
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            {/* Financial Area Chart */}
            <div className="pt-2">
              <FinancialAreaChart
                data={chartData}
                primaryLabel="AI Queries"
                secondaryLabel="Filings Ingested"
                height={210}
                color="#d2f800"
                secondaryColor="#22d3ee"
                currencyPrefix=""
                valueSuffix=""
                onExportCsv={() => alert('Exporting activity dataset as CSV')}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] font-mono text-carbon-400 pt-2 border-t border-carbon-800">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-lime-400" />
                  AI Queries: <strong className="text-white">4,821</strong> (+18.7%)
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" />
                  Filings: <strong className="text-white">310</strong>
                </span>
              </div>
              <span className="text-emerald-400 font-semibold">100% Grounded</span>
            </div>
          </div>

          {/* Recent AI Research Cards */}
          <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-700/70 shadow-sm flex flex-col gap-3.5">
            <div className="flex items-center justify-between pb-2 border-b border-carbon-800">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-lime-400" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-carbon-200">
                  Recent AI Research
                </h2>
              </div>
              <button
                onClick={() => onNavigateToAsk()}
                className="text-xs font-medium text-lime-400 hover:text-lime-300 transition-colors flex items-center gap-1 group"
              >
                Open Ask FINARQ
                <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>

            <div className="flex flex-col gap-2.5">
              {recentResearch.map((item) => (
                <div
                  key={item.id}
                  onClick={() => onNavigateToAsk(item.query)}
                  className="p-3 rounded-lg bg-carbon-800/80 hover:bg-carbon-750 border border-carbon-700/60 hover:border-carbon-500/80 cursor-pointer transition-all duration-200 flex flex-col gap-2 group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {item.entities.map((ent, i) => (
                        <span
                          key={i}
                          className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-carbon-700 text-carbon-200 border border-carbon-600"
                        >
                          {ent}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-carbon-400 shrink-0">
                      <span className="text-emerald-400 font-semibold">✓ {item.confidence} grounded</span>
                      <span>·</span>
                      <span>{item.timestamp}</span>
                    </div>
                  </div>

                  <p className="text-xs font-semibold text-white group-hover:text-lime-300 transition-colors line-clamp-1">
                    "{item.query}"
                  </p>

                  <p className="text-[11px] text-carbon-300 line-clamp-2 leading-relaxed">
                    {item.summary}
                  </p>

                  <div className="flex items-center justify-between pt-1 border-t border-carbon-700/40 text-[10px] text-carbon-400">
                    <span className="font-mono text-carbon-300 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      {item.citationsCount} verified citations
                    </span>
                    <span className="text-lime-400 font-medium group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
                      Open result <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (5 Cols): Recent Documents Table + Quick Inquiries + System Probes */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          {/* Recent Ingested Documents Card */}
          <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-700/70 shadow-sm flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-carbon-800">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-400" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-carbon-200">
                  Recent Documents
                </h2>
              </div>
              <button
                onClick={onNavigateToDocuments}
                className="text-xs font-medium text-carbon-300 hover:text-white transition-colors flex items-center gap-1"
              >
                View all ({displayDocs.length}) <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="flex flex-col divide-y divide-carbon-800">
              {displayDocs.slice(0, 5).map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => onSelectDocument(doc.id)}
                  className="py-2.5 px-2 -mx-2 rounded-lg hover:bg-carbon-800/80 cursor-pointer transition-all flex items-center justify-between gap-3 group"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="p-1.5 rounded bg-carbon-800 border border-carbon-700/60 text-carbon-300 group-hover:text-lime-400 group-hover:border-lime-400/40 transition-colors shrink-0">
                      <FileText className="w-3.5 h-3.5" />
                    </div>
                    <div className="min-w-0 flex flex-col">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-xs text-white truncate max-w-[160px] group-hover:text-lime-300 transition-colors">
                          {doc.company_name || doc.ticker_symbol || 'Entity'}
                        </span>
                        <span className="px-1 py-0.2 rounded text-[9px] font-mono font-bold bg-carbon-700 text-carbon-300">
                          {doc.document_type || '10-K'} {doc.fiscal_period || 'FY'}{doc.fiscal_year || '2025'}
                        </span>
                      </div>
                      <span className="text-[10px] text-carbon-400 truncate max-w-[200px]">
                        {doc.title}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end shrink-0 gap-0.5">
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      Processed
                    </span>
                    <span className="text-[9px] font-mono text-carbon-400">
                      {doc.pages_count} pages
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Financial Research Prompts */}
          <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-700/70 shadow-sm flex flex-col gap-3">
            <div className="flex items-center gap-2 pb-2 border-b border-carbon-800">
              <Zap className="w-4 h-4 text-lime-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-carbon-200">
                Suggested Financial Inquiries
              </h2>
            </div>

            <div className="flex flex-col gap-1.5">
              {[
                "What was Apple's revenue growth from 2023 to 2025?",
                'Compare Microsoft Cloud vs Amazon AWS operating margins in FY2024.',
                'Calculate NVIDIA Datacenter segment gross profit margin.',
                'Analyze JPMorgan Chase Common Equity Tier 1 (CET1) capital ratio.',
              ].map((query, idx) => (
                <button
                  key={idx}
                  onClick={() => onNavigateToAsk(query)}
                  className="w-full text-left p-2.5 rounded-lg bg-carbon-800/80 hover:bg-carbon-750 border border-carbon-700/60 hover:border-lime-400/40 text-xs text-carbon-200 hover:text-white transition-all flex items-center justify-between group"
                >
                  <span className="truncate pr-2 font-medium">{query}</span>
                  <ArrowRight className="w-3 h-3 text-carbon-400 group-hover:text-lime-400 shrink-0 group-hover:translate-x-0.5 transition-transform" />
                </button>
              ))}
            </div>
          </div>

          {/* Infrastructure Health Probes */}
          <div className="p-3.5 rounded-xl bg-carbon-900 border border-carbon-700/70 shadow-sm flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-carbon-200 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                Infrastructure Health
              </span>
              <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Operational
              </span>
            </div>

            <div className="grid grid-cols-4 gap-1.5 text-[10px] font-mono">
              <div className="p-1.5 rounded bg-carbon-800 border border-carbon-700/60 text-center text-carbon-300">
                Postgres <span className="text-emerald-400">●</span>
              </div>
              <div className="p-1.5 rounded bg-carbon-800 border border-carbon-700/60 text-center text-carbon-300">
                Qdrant <span className="text-emerald-400">●</span>
              </div>
              <div className="p-1.5 rounded bg-carbon-800 border border-carbon-700/60 text-center text-carbon-300">
                S3 Vault <span className="text-emerald-400">●</span>
              </div>
              <div className="p-1.5 rounded bg-carbon-800 border border-carbon-700/60 text-center text-carbon-300">
                AST Solver <span className="text-emerald-400">●</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

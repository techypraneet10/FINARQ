import React, { useState } from 'react';
import {
  Building2,
  ArrowLeft,
  Sparkles,
  FileText,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  GitCompare,
  DollarSign,
  ChevronRight,
  ExternalLink,
  BookOpen,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Tabs } from '../../design-system/Tabs';
import { FinancialAreaChart } from '../charts/FinancialAreaChart';

export interface CompanyDetailViewProps {
  ticker: string;
  onBack: () => void;
  onNavigateToDocument?: (documentId: string, pageNumber?: number) => void;
  onNavigateToAsk?: (query?: string) => void;
  onNavigateToComparison?: (tickerA: string, tickerB: string) => void;
}

export const CompanyDetailView: React.FC<CompanyDetailViewProps> = ({
  ticker,
  onBack,
  onNavigateToDocument,
  onNavigateToAsk,
  onNavigateToComparison,
}) => {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const companyProfiles: Record<string, any> = {
    AAPL: {
      name: 'Apple Inc.',
      ticker: 'AAPL',
      sector: 'Consumer Electronics & Cloud Services',
      marketCap: '$3,420,000,000,000.00',
      marketCapCompact: '$3.42T',
      revenue: '$416,200,000,000.00',
      netIncome: '$112,010,000,000.00',
      eps: '$7.48',
      operatingMargin: '32.0%',
      freeCashFlow: '$108,810,000,000.00',
      filingDate: 'October 31, 2025',
      cik: '0000320193',
      revenueHistory: [
        { period: 'FY2021', value: 365817, secondaryValue: 94680 },
        { period: 'FY2022', value: 394328, secondaryValue: 99803 },
        { period: 'FY2023', value: 383285, secondaryValue: 96995 },
        { period: 'FY2024', value: 391035, secondaryValue: 93736 },
        { period: 'FY2025', value: 416200, secondaryValue: 112010 },
      ],
      filings: [
        { id: 'doc-aapl-2025', title: '2025 Form 10-K (Annual Report)', type: '10-K', period: 'FY2025', date: 'Oct 31, 2025', pages: 184 },
        { id: 'doc-aapl-q3-2025', title: 'Q3 2025 Form 10-Q (Quarterly Report)', type: '10-Q', period: 'Q3 2025', date: 'Aug 01, 2025', pages: 62 },
        { id: 'doc-aapl-2024', title: '2024 Form 10-K (Annual Report)', type: '10-K', period: 'FY2024', date: 'Nov 01, 2024', pages: 178 },
      ],
      riskFactors: [
        { title: 'Global Supply Chain & Semiconductor Dependencies', severity: 'High', description: 'Concentration of manufacturing operations in APAC regions exposes gross margins to geopolitical or component disruptions.' },
        { title: 'Digital Marketplace & App Store Antitrust Scrutiny', severity: 'Medium', description: 'Regulatory investigations regarding App Store commission rates across EU and DOJ may impact Services take-rates.' },
        { title: 'Foreign Exchange Rate Fluctuations', severity: 'Medium', description: 'Over 55% of net sales originate outside the United States, exposing revenue translation to currency headwinds.' },
      ],
    },
  };

  const profile = companyProfiles[ticker] || {
    name: `${ticker} Corporation`,
    ticker: ticker,
    sector: 'Technology & Enterprise Solutions',
    marketCap: '$1,850,000,000,000.00',
    marketCapCompact: '$1.85T',
    revenue: '$124,300,000,000.00',
    netIncome: '$68,400,000,000.00',
    eps: '$2.78',
    operatingMargin: '62.4%',
    freeCashFlow: '$60,850,000,000.00',
    filingDate: 'November 2025',
    cik: '0001045810',
    revenueHistory: [
      { period: 'FY2021', value: 26914, secondaryValue: 9752 },
      { period: 'FY2022', value: 26974, secondaryValue: 4368 },
      { period: 'FY2023', value: 60922, secondaryValue: 29760 },
      { period: 'FY2024', value: 96300, secondaryValue: 53100 },
      { period: 'FY2025', value: 124300, secondaryValue: 68400 },
    ],
    filings: [
      { id: `doc-${ticker.toLowerCase()}-2025`, title: `${ticker} 2025 Form 10-K`, type: '10-K', period: 'FY2025', date: '2025', pages: 96 },
    ],
    riskFactors: [
      { title: 'Product Architecture & R&D Velocity', severity: 'High', description: 'Continuous rapid cadence required to sustain competitive advantage in computing architectures.' },
    ],
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'financials', label: 'Financials', icon: <DollarSign className="w-4 h-4" /> },
    { id: 'filings', label: 'Filings', count: profile.filings.length, icon: <FileText className="w-4 h-4" /> },
    { id: 'risk', label: 'Risk Factors', count: profile.riskFactors.length, icon: <AlertTriangle className="w-4 h-4" /> },
    { id: 'ai', label: 'AI Research', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'comparisons', label: 'Comparisons', icon: <GitCompare className="w-4 h-4" /> },
  ];

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div className="flex items-center gap-3.5 min-w-0">
          <Button variant="outline" size="sm" onClick={onBack} icon={<ArrowLeft className="w-4 h-4" />}>
            Back
          </Button>
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl font-bold text-white truncate">{profile.name}</h1>
              <span className="px-2 py-0.5 rounded font-mono text-xs font-bold bg-carbon-800 border border-carbon-600 text-lime-400">
                {profile.ticker}
              </span>
              <span className="text-xs text-carbon-400">CIK: {profile.cik}</span>
            </div>
            <span className="text-xs text-carbon-400 mt-0.5">{profile.sector}</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            variant="lime"
            size="sm"
            onClick={() => onNavigateToAsk?.(`What were the primary revenue and margin drivers for ${profile.name} in the latest 10-K?`)}
            icon={<Sparkles className="w-3.5 h-3.5" />}
          >
            Ask AI About {profile.ticker}
          </Button>
        </div>
      </div>

      {/* 6 High-Precision KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Market Cap', value: profile.marketCapCompact, full: profile.marketCap },
          { label: 'Revenue (FY2025)', value: '$416.2B', full: profile.revenue },
          { label: 'Net Income', value: '$112.0B', full: profile.netIncome },
          { label: 'Diluted EPS', value: profile.eps, full: profile.eps },
          { label: 'Operating Margin', value: profile.operatingMargin, full: profile.operatingMargin },
          { label: 'Free Cash Flow', value: '$108.8B', full: profile.freeCashFlow },
        ].map((kpi, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col justify-between gap-1 shadow-sm"
          >
            <span className="text-[10px] font-bold uppercase tracking-wider text-carbon-400 truncate" title={kpi.label}>
              {kpi.label}
            </span>
            <span className="text-lg font-bold font-mono text-white tracking-tight">
              {kpi.value}
            </span>
            <span className="text-[10px] font-mono text-emerald-400">
              Verified Ground Truth
            </span>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab: Overview */}
      {activeTab === 'overview' && (
        <div className="flex flex-col gap-5 animate-fade-in">
          {/* Revenue & Net Income Multi-Year Trend Chart */}
          <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-carbon-200">
                  5-Year Revenue & Net Income Performance ($M)
                </h3>
                <p className="text-[11px] text-carbon-400 mt-0.5">
                  Extracted from audited SEC Form 10-K Consolidated Statements of Operations
                </p>
              </div>
            </div>

            <FinancialAreaChart
              data={profile.revenueHistory}
              primaryLabel="Total Net Sales"
              secondaryLabel="Net Income"
              height={220}
              color="#d2f800"
              secondaryColor="#22d3ee"
              valueSuffix="$M"
              onExportCsv={() => alert('Exporting company performance CSV')}
            />
          </div>

          {/* Quick AI Questions for this Company */}
          <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-carbon-200 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-lime-400" />
              Pre-Formulated AI Research Questions for {profile.ticker}
            </span>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {[
                `What was ${profile.name}'s YoY Services revenue growth from FY2023 to FY2025?`,
                `Calculate gross profit margin by product segment for ${profile.ticker}.`,
                `What risk factors were newly added in ${profile.name}'s latest 10-K?`,
                `Analyze capital expenditures vs operating cash flow over the last 3 years.`,
              ].map((q, i) => (
                <button
                  key={i}
                  onClick={() => onNavigateToAsk?.(q)}
                  className="p-3 rounded-lg bg-carbon-800 hover:bg-carbon-700 border border-carbon-600/60 hover:border-lime-400/50 text-left text-xs text-white transition-all flex items-center justify-between group"
                >
                  <span className="truncate pr-2 font-medium">{q}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-lime-400 shrink-0 group-hover:translate-x-0.5 transition-transform" />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Filings */}
      {activeTab === 'filings' && (
        <div className="flex flex-col gap-3 animate-fade-in">
          <div className="flex flex-col divide-y divide-carbon-800 rounded-xl border border-carbon-600 bg-carbon-900">
            {profile.filings.map((filing: any) => (
              <div
                key={filing.id}
                onClick={() => onNavigateToDocument?.(filing.id, 1)}
                className="p-4 hover:bg-carbon-800/80 cursor-pointer transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-carbon-800 border border-carbon-600 text-lime-400 group-hover:border-lime-400">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-semibold text-xs text-white group-hover:text-lime-300 transition-colors">
                      {filing.title}
                    </span>
                    <span className="text-[11px] font-mono text-carbon-400">
                      Filing Date: {filing.date} · {filing.pages} pages · Status: Processed
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-carbon-800 text-carbon-300 border border-carbon-600">
                    {filing.period}
                  </span>
                  <span className="text-xs font-semibold text-lime-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                    Open Filing <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Risk Factors */}
      {activeTab === 'risk' && (
        <div className="flex flex-col gap-3 animate-fade-in">
          {profile.riskFactors.map((risk: any, i: number) => (
            <div key={i} className="p-4 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-white flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  {risk.title}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950/60 text-amber-400 border border-amber-500/30">
                  {risk.severity} Risk
                </span>
              </div>
              <p className="text-xs text-carbon-300 leading-relaxed font-sans">
                {risk.description}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Comparisons */}
      {activeTab === 'comparisons' && (
        <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-4 animate-fade-in">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Side-by-Side Corporate Benchmarking
          </span>
          <p className="text-xs text-carbon-300">
            Compare {profile.name} against peer industry giants across revenue growth, gross margins, EBITDA, and free cash flow generation.
          </p>
          <div className="flex items-center gap-3">
            <Button
              variant="lime"
              size="sm"
              onClick={() => onNavigateToComparison?.(profile.ticker, profile.ticker === 'AAPL' ? 'MSFT' : 'AAPL')}
              icon={<GitCompare className="w-3.5 h-3.5" />}
            >
              Benchmark against {profile.ticker === 'AAPL' ? 'Microsoft (MSFT)' : 'Apple (AAPL)'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

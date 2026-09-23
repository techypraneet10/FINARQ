import React, { useState } from 'react';
import {
  Building2,
  Search,
  ArrowRight,
  TrendingUp,
  Sparkles,
  FileText,
  DollarSign,
  ShieldCheck,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Input } from '../../design-system/Input';
import { Sparkline } from '../charts/Sparkline';

export interface CompanySummary {
  ticker: string;
  name: string;
  sector: string;
  marketCap: string;
  revenue: string;
  netIncome: string;
  eps: string;
  operatingMargin: string;
  freeCashFlow: string;
  filingsCount: number;
  revenueSparkline: number[];
  isPos: boolean;
  status: string;
}

export interface CompaniesViewProps {
  onSelectCompany: (ticker: string) => void;
  onNavigateToAsk?: (query?: string) => void;
  onNavigateToComparison?: (tickerA: string, tickerB: string) => void;
}

export const CompaniesView: React.FC<CompaniesViewProps> = ({
  onSelectCompany,
  onNavigateToAsk,
  onNavigateToComparison,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedSector, setSelectedSector] = useState<string>('all');

  const companies: CompanySummary[] = [
    {
      ticker: 'AAPL',
      name: 'Apple Inc.',
      sector: 'Consumer Electronics & Services',
      marketCap: '$3.42T',
      revenue: '$416,200,000,000.00',
      netIncome: '$112,010,000,000.00',
      eps: '$7.48',
      operatingMargin: '32.0%',
      freeCashFlow: '$108,810,000,000.00',
      filingsCount: 6,
      revenueSparkline: [383, 388, 391, 398, 405, 412, 416],
      isPos: true,
      status: 'Tracked',
    },
    {
      ticker: 'MSFT',
      name: 'Microsoft Corporation',
      sector: 'Cloud & Enterprise Software',
      marketCap: '$3.18T',
      revenue: '$245,120,000,000.00',
      netIncome: '$88,140,000,000.00',
      eps: '$11.80',
      operatingMargin: '44.6%',
      freeCashFlow: '$74,070,000,000.00',
      filingsCount: 5,
      revenueSparkline: [198, 211, 225, 232, 238, 245],
      isPos: true,
      status: 'Tracked',
    },
    {
      ticker: 'NVDA',
      name: 'NVIDIA Corporation',
      sector: 'Accelerated Computing & AI',
      marketCap: '$2.85T',
      revenue: '$124,300,000,000.00',
      netIncome: '$68,400,000,000.00',
      eps: '$2.78',
      operatingMargin: '62.4%',
      freeCashFlow: '$60,850,000,000.00',
      filingsCount: 4,
      revenueSparkline: [27, 44, 60, 85, 105, 124],
      isPos: true,
      status: 'Tracked',
    },
    {
      ticker: 'AMZN',
      name: 'Amazon.com Inc',
      sector: 'E-Commerce & Cloud (AWS)',
      marketCap: '$1.98T',
      revenue: '$620,130,000,000.00',
      netIncome: '$44,800,000,000.00',
      eps: '$4.18',
      operatingMargin: '9.8%',
      freeCashFlow: '$52,900,000,000.00',
      filingsCount: 5,
      revenueSparkline: [513, 538, 560, 582, 605, 620],
      isPos: true,
      status: 'Tracked',
    },
    {
      ticker: 'JPM',
      name: 'JPMorgan Chase & Co.',
      sector: 'Banking & Financial Services',
      marketCap: '$610.2B',
      revenue: '$162,400,000,000.00',
      netIncome: '$57,800,000,000.00',
      eps: '$19.82',
      operatingMargin: '41.2%',
      freeCashFlow: '$48,200,000,000.00',
      filingsCount: 6,
      revenueSparkline: [128, 138, 148, 155, 162],
      isPos: true,
      status: 'Tracked',
    },
    {
      ticker: 'GOOGL',
      name: 'Alphabet Inc.',
      sector: 'Search, Advertising & Cloud',
      marketCap: '$2.15T',
      revenue: '$350,020,000,000.00',
      netIncome: '$89,300,000,000.00',
      eps: '$7.14',
      operatingMargin: '31.8%',
      freeCashFlow: '$72,100,000,000.00',
      filingsCount: 5,
      revenueSparkline: [282, 295, 310, 328, 350],
      isPos: true,
      status: 'Tracked',
    },
  ];

  const filtered = companies.filter((c) => {
    const matchesSearch =
      !searchQuery ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.sector.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector =
      selectedSector === 'all' || c.sector.toLowerCase().includes(selectedSector.toLowerCase());
    return matchesSearch && matchesSector;
  });

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Company Intelligence</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-carbon-800 text-lime-400 border border-carbon-600">
              {companies.length} Tracked Entities
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            Authoritative financial disclosures, statement extractions, and multi-year metrics.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigateToComparison?.('AAPL', 'MSFT')}
            icon={<TrendingUp className="w-3.5 h-3.5 text-lime-400" />}
          >
            Compare AAPL vs MSFT
          </Button>
        </div>
      </div>

      {/* Search & Sector Filters */}
      <div className="flex flex-wrap items-center gap-3 p-3 rounded-xl bg-carbon-900 border border-carbon-600/90 shadow-sm">
        <div className="flex-1 min-w-[240px]">
          <Input
            placeholder="Search company name, ticker symbol (e.g. AAPL, NVDA)..."
            icon={<Search className="w-4 h-4 text-carbon-400" />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <select
          value={selectedSector}
          onChange={(e) => setSelectedSector(e.target.value)}
          className="bg-carbon-950 border border-carbon-600 text-white text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-lime-400"
        >
          <option value="all">All Industry Sectors</option>
          <option value="software">Cloud & Software</option>
          <option value="consumer">Consumer Electronics</option>
          <option value="computing">Semiconductors & AI</option>
          <option value="banking">Banking & Finance</option>
        </select>
      </div>

      {/* Grid of Company Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((company) => (
          <div
            key={company.ticker}
            onClick={() => onSelectCompany(company.ticker)}
            className="p-4 rounded-xl bg-carbon-900 border border-carbon-600/80 hover:border-carbon-400/90 cursor-pointer transition-all duration-200 flex flex-col justify-between gap-4 group shadow-sm"
          >
            {/* Top Row: Ticker Badge, Name, Sector */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-xl bg-carbon-800 border border-carbon-600 flex items-center justify-center font-mono font-bold text-sm text-lime-400 group-hover:border-lime-400/60 transition-colors shrink-0">
                  {company.ticker}
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="font-bold text-sm text-white group-hover:text-lime-300 transition-colors truncate">
                    {company.name}
                  </span>
                  <span className="text-[11px] text-carbon-400 truncate">
                    {company.sector}
                  </span>
                </div>
              </div>

              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-carbon-800 text-carbon-300 border border-carbon-700">
                {company.marketCap}
              </span>
            </div>

            {/* Financial Metrics Grid */}
            <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-carbon-950 border border-carbon-700/60 font-mono text-xs">
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-carbon-400">Revenue</span>
                <span className="font-bold text-white text-xs truncate">{company.revenue.split(',')[0]}B</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-carbon-400">Net Margin</span>
                <span className="font-bold text-emerald-400 text-xs">{company.operatingMargin}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-carbon-400">EPS</span>
                <span className="font-bold text-lime-400 text-xs">{company.eps}</span>
              </div>
            </div>

            {/* Sparkline & Action Bar */}
            <div className="flex items-center justify-between pt-1 border-t border-carbon-700/50">
              <div className="flex items-center gap-2">
                <div className="w-20 h-6">
                  <Sparkline data={company.revenueSparkline} color="#d2f800" height={24} width={80} />
                </div>
                <span className="text-[10px] font-mono text-carbon-400">{company.filingsCount} filings</span>
              </div>

              <span className="text-xs font-semibold text-lime-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                Inspect Profile <ChevronRight className="w-3.5 h-3.5" />
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

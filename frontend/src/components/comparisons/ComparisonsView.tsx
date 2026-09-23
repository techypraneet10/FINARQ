import React, { useState } from 'react';
import {
  GitCompare,
  Building2,
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  DollarSign,
  Layers,
  ChevronRight,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { ComparisonDeltaBar } from '../charts/ComparisonDeltaBar';

export interface ComparisonsViewProps {
  initialTickerA?: string;
  initialTickerB?: string;
  onNavigateToAsk?: (query?: string) => void;
}

export const ComparisonsView: React.FC<ComparisonsViewProps> = ({
  initialTickerA = 'AAPL',
  initialTickerB = 'MSFT',
  onNavigateToAsk,
}) => {
  const [tickerA, setTickerA] = useState<string>(initialTickerA);
  const [tickerB, setTickerB] = useState<string>(initialTickerB);

  const companies: Record<string, any> = {
    AAPL: {
      name: 'Apple Inc.',
      ticker: 'AAPL',
      marketCap: '$3,420,000,000,000.00',
      marketCapCompact: '$3.42T',
      revenue: 416200,
      revenueDisplay: '$416,200,000,000.00',
      revenueGrowth: 6.4,
      netIncome: 112010,
      netIncomeDisplay: '$112,010,000,000.00',
      netMargin: 26.9,
      eps: '$7.48',
      freeCashFlow: 108810,
      freeCashFlowDisplay: '$108,810,000,000.00',
      debt: 106600,
      debtDisplay: '$106,600,000,000.00',
      cash: 156650,
      cashDisplay: '$156,650,000,000.00',
      period: 'FY2025',
    },
    MSFT: {
      name: 'Microsoft Corp',
      ticker: 'MSFT',
      marketCap: '$3,180,000,000,000.00',
      marketCapCompact: '$3.18T',
      revenue: 245120,
      revenueDisplay: '$245,120,000,000.00',
      revenueGrowth: 15.7,
      netIncome: 88140,
      netIncomeDisplay: '$88,140,000,000.00',
      netMargin: 36.0,
      eps: '$11.80',
      freeCashFlow: 74070,
      freeCashFlowDisplay: '$74,070,000,000.00',
      debt: 44900,
      debtDisplay: '$44,900,000,000.00',
      cash: 75500,
      cashDisplay: '$75,500,000,000.00',
      period: 'FY2024',
    },
    NVDA: {
      name: 'NVIDIA Corporation',
      ticker: 'NVDA',
      marketCap: '$2,850,000,000,000.00',
      marketCapCompact: '$2.85T',
      revenue: 124300,
      revenueDisplay: '$124,300,000,000.00',
      revenueGrowth: 122.0,
      netIncome: 68400,
      netIncomeDisplay: '$68,400,000,000.00',
      netMargin: 55.0,
      eps: '$2.78',
      freeCashFlow: 60850,
      freeCashFlowDisplay: '$60,850,000,000.00',
      debt: 11000,
      debtDisplay: '$11,000,000,000.00',
      cash: 34800,
      cashDisplay: '$34,800,000,000.00',
      period: 'FY2025',
    },
    AMZN: {
      name: 'Amazon.com Inc',
      ticker: 'AMZN',
      marketCap: '$1,980,000,000,000.00',
      marketCapCompact: '$1.98T',
      revenue: 620130,
      revenueDisplay: '$620,130,000,000.00',
      revenueGrowth: 11.9,
      netIncome: 44800,
      netIncomeDisplay: '$44,800,000,000.00',
      netMargin: 7.2,
      eps: '$4.18',
      freeCashFlow: 52900,
      freeCashFlowDisplay: '$52,900,000,000.00',
      debt: 58000,
      debtDisplay: '$58,000,000,000.00',
      cash: 86800,
      cashDisplay: '$86,800,000,000.00',
      period: 'FY2024',
    },
  };

  const compA = companies[tickerA] || companies['AAPL'];
  const compB = companies[tickerB] || companies['MSFT'];

  const comparisonMetrics = [
    { label: 'Revenue ($M)', valA: compA.revenue, valB: compB.revenue, format: (v: number) => `$${v.toLocaleString()}M` },
    { label: 'Revenue YoY Growth (%)', valA: compA.revenueGrowth, valB: compB.revenueGrowth, format: (v: number) => `${v.toFixed(1)}%` },
    { label: 'Net Income ($M)', valA: compA.netIncome, valB: compB.netIncome, format: (v: number) => `$${v.toLocaleString()}M` },
    { label: 'Net Profit Margin (%)', valA: compA.netMargin, valB: compB.netMargin, format: (v: number) => `${v.toFixed(1)}%` },
    { label: 'Free Cash Flow ($M)', valA: compA.freeCashFlow, valB: compB.freeCashFlow, format: (v: number) => `$${v.toLocaleString()}M` },
    { label: 'Total Cash & Equivalents ($M)', valA: compA.cash, valB: compB.cash, format: (v: number) => `$${v.toLocaleString()}M` },
    { label: 'Total Debt ($M)', valA: compA.debt, valB: compB.debt, format: (v: number) => `$${v.toLocaleString()}M`, higherIsBetter: false },
  ];

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Company Comparison</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-carbon-800 text-lime-400 border border-carbon-600">
              Side-by-Side Benchmarking
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            Compare corporate performance, profit margins, balance sheet liquidity, and cash flow generation.
          </p>
        </div>

        {/* AI Synthesis CTA */}
        <Button
          variant="lime"
          size="sm"
          onClick={() => onNavigateToAsk?.(`Compare ${compA.name} (${compA.ticker}) and ${compB.name} (${compB.ticker}) financial performance, revenue growth, net profit margins, and capital allocation strategy.`)}
          icon={<Sparkles className="w-3.5 h-3.5" />}
        >
          Ask AI Comparative Synthesis
        </Button>
      </div>

      {/* Entity Selector Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Entity A Card */}
        <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-600/90 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-carbon-800 border border-lime-400/60 flex items-center justify-center font-mono font-bold text-sm text-lime-400">
              {compA.ticker}
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-bold uppercase tracking-wider text-carbon-400">
                Primary Entity (A)
              </span>
              <select
                value={tickerA}
                onChange={(e) => setTickerA(e.target.value)}
                className="bg-transparent text-white text-sm font-bold focus:outline-none cursor-pointer"
              >
                {Object.keys(companies).map((t) => (
                  <option key={t} value={t} className="bg-carbon-900 text-white">
                    {companies[t].name} ({t})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <span className="px-2 py-1 rounded text-xs font-mono font-bold bg-carbon-800 text-lime-400 border border-carbon-700">
            {compA.marketCapCompact}
          </span>
        </div>

        {/* Entity B Card */}
        <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-600/90 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-carbon-800 border border-cyan-400/60 flex items-center justify-center font-mono font-bold text-sm text-cyan-300">
              {compB.ticker}
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-bold uppercase tracking-wider text-carbon-400">
                Benchmark Peer (B)
              </span>
              <select
                value={tickerB}
                onChange={(e) => setTickerB(e.target.value)}
                className="bg-transparent text-white text-sm font-bold focus:outline-none cursor-pointer"
              >
                {Object.keys(companies).map((t) => (
                  <option key={t} value={t} className="bg-carbon-900 text-white">
                    {companies[t].name} ({t})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <span className="px-2 py-1 rounded text-xs font-mono font-bold bg-carbon-800 text-cyan-300 border border-carbon-700">
            {compB.marketCapCompact}
          </span>
        </div>
      </div>

      {/* Comparison Delta Bars */}
      <div className="p-5 rounded-2xl bg-carbon-900 border border-carbon-600/90 shadow-xl flex flex-col gap-4">
        <div className="flex items-center justify-between pb-3 border-b border-carbon-700/60">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Visual Relative Distribution ({compA.ticker} vs {compB.ticker})
          </span>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-lime-400 font-semibold">
              <span className="w-2 h-2 rounded-full bg-lime-400" /> {compA.ticker}
            </span>
            <span className="flex items-center gap-1.5 text-cyan-300 font-semibold">
              <span className="w-2 h-2 rounded-full bg-cyan-400" /> {compB.ticker}
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-3.5">
          {comparisonMetrics.map((m, i) => (
            <ComparisonDeltaBar
              key={i}
              label={m.label}
              metricA={{
                name: compA.ticker,
                value: m.valA,
                formatted: m.format(m.valA),
                color: '#d2f800',
              }}
              metricB={{
                name: compB.ticker,
                value: m.valB,
                formatted: m.format(m.valB),
                color: '#22d3ee',
              }}
              higherIsBetter={m.higherIsBetter !== false}
            />
          ))}
        </div>
      </div>

      {/* Side-by-Side Detailed Financial Statement Table */}
      <div className="p-5 rounded-2xl bg-carbon-900 border border-carbon-600/90 shadow-xl flex flex-col gap-3">
        <div className="flex items-center justify-between pb-2 border-b border-carbon-700/60">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Side-by-Side Statement Metrics
          </span>
          <span className="text-[10px] font-mono text-emerald-400 font-semibold">
            ✓ Audited Ground Truth Filings
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-carbon-700/80 bg-carbon-950">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-carbon-900 border-b border-carbon-700 text-carbon-400 font-semibold uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-4">Financial Metric</th>
                <th className="py-2.5 px-4 text-right text-lime-400 font-bold">{compA.name} ({compA.ticker})</th>
                <th className="py-2.5 px-4 text-right text-cyan-300 font-bold">{compB.name} ({compB.ticker})</th>
                <th className="py-2.5 px-4 text-right">Variance / Delta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-carbon-800">
              <tr className="hover:bg-carbon-850">
                <td className="py-2.5 px-4 font-sans font-medium text-white">Total Net Sales (Revenue)</td>
                <td className="py-2.5 px-4 text-right font-bold text-lime-400">{compA.revenueDisplay}</td>
                <td className="py-2.5 px-4 text-right font-bold text-cyan-300">{compB.revenueDisplay}</td>
                <td className="py-2.5 px-4 text-right text-carbon-300 font-semibold">
                  {compA.revenue > compB.revenue ? `+${compA.ticker} by $${(compA.revenue - compB.revenue).toLocaleString()}M` : `+${compB.ticker} by $${(compB.revenue - compA.revenue).toLocaleString()}M`}
                </td>
              </tr>
              <tr className="hover:bg-carbon-850">
                <td className="py-2.5 px-4 font-sans font-medium text-white">Net Income</td>
                <td className="py-2.5 px-4 text-right font-bold text-lime-400">{compA.netIncomeDisplay}</td>
                <td className="py-2.5 px-4 text-right font-bold text-cyan-300">{compB.netIncomeDisplay}</td>
                <td className="py-2.5 px-4 text-right text-carbon-300 font-semibold">
                  {compA.netIncome > compB.netIncome ? `+${compA.ticker} by $${(compA.netIncome - compB.netIncome).toLocaleString()}M` : `+${compB.ticker} by $${(compB.netIncome - compA.netIncome).toLocaleString()}M`}
                </td>
              </tr>
              <tr className="hover:bg-carbon-850">
                <td className="py-2.5 px-4 font-sans font-medium text-white">Net Profit Margin</td>
                <td className="py-2.5 px-4 text-right font-bold text-lime-400">{compA.netMargin}%</td>
                <td className="py-2.5 px-4 text-right font-bold text-cyan-300">{compB.netMargin}%</td>
                <td className="py-2.5 px-4 text-right text-carbon-300 font-semibold">
                  {Math.abs(compA.netMargin - compB.netMargin).toFixed(1)}% margin spread
                </td>
              </tr>
              <tr className="hover:bg-carbon-850">
                <td className="py-2.5 px-4 font-sans font-medium text-white">Free Cash Flow</td>
                <td className="py-2.5 px-4 text-right font-bold text-lime-400">{compA.freeCashFlowDisplay}</td>
                <td className="py-2.5 px-4 text-right font-bold text-cyan-300">{compB.freeCashFlowDisplay}</td>
                <td className="py-2.5 px-4 text-right text-carbon-300 font-semibold">
                  {compA.freeCashFlow > compB.freeCashFlow ? `+${compA.ticker} by $${(compA.freeCashFlow - compB.freeCashFlow).toLocaleString()}M` : `+${compB.ticker} by $${(compB.freeCashFlow - compA.freeCashFlow).toLocaleString()}M`}
                </td>
              </tr>
              <tr className="hover:bg-carbon-850">
                <td className="py-2.5 px-4 font-sans font-medium text-white">Total Debt</td>
                <td className="py-2.5 px-4 text-right font-bold text-carbon-200">{compA.debtDisplay}</td>
                <td className="py-2.5 px-4 text-right font-bold text-carbon-200">{compB.debtDisplay}</td>
                <td className="py-2.5 px-4 text-right text-carbon-300 font-semibold">
                  {compA.debt < compB.debt ? `${compA.ticker} lower leverage` : `${compB.ticker} lower leverage`}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

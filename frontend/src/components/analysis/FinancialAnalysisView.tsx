import React, { useState } from 'react';
import {
  TrendingUp,
  Building2,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { FinancialAreaChart } from '../charts/FinancialAreaChart';

export interface FinancialAnalysisViewProps {
  onNavigateToAsk?: (query?: string) => void;
  onNavigateToDocument?: (docId: string, page?: number) => void;
}

export const FinancialAnalysisView: React.FC<FinancialAnalysisViewProps> = ({
  onNavigateToAsk,
}) => {
  const [selectedCompany, setSelectedCompany] = useState<string>('AAPL');
  const [selectedPeriodRange, setSelectedPeriodRange] = useState<string>('2021-2025');
  const [activeChartMetric, setActiveChartMetric] = useState<'revenue' | 'margins' | 'cashFlow'>('revenue');

  const companiesData: Record<string, any> = {
    AAPL: {
      name: 'Apple Inc.',
      ticker: 'AAPL',
      kpis: [
        { label: 'Revenue (FY2025)', value: '$416,200,000,000.00', compact: '$416.2B', change: '+6.4% YoY', isPos: true },
        { label: 'Net Income', value: '$112,010,000,000.00', compact: '$112.0B', change: '+19.5% YoY', isPos: true },
        { label: 'EBITDA', value: '$133,120,000,000.00', compact: '$133.1B', change: '+16.8% YoY', isPos: true },
        { label: 'Diluted EPS', value: '$7.48', compact: '$7.48', change: '+22.0% YoY', isPos: true },
        { label: 'Free Cash Flow', value: '$108,810,000,000.00', compact: '$108.8B', change: '+8.3% YoY', isPos: true },
        { label: 'Operating Margin', value: '32.0%', compact: '32.0%', change: '+180 bps', isPos: true },
      ],
      revenueSeries: [
        { period: 'FY2021', value: 365817, secondaryValue: 94680 },
        { period: 'FY2022', value: 394328, secondaryValue: 99803 },
        { period: 'FY2023', value: 383285, secondaryValue: 96995 },
        { period: 'FY2024', value: 391035, secondaryValue: 93736 },
        { period: 'FY2025', value: 416200, secondaryValue: 112010 },
      ],
      marginSeries: [
        { period: 'FY2021', value: 41.8, secondaryValue: 29.8 },
        { period: 'FY2022', value: 43.3, secondaryValue: 30.3 },
        { period: 'FY2023', value: 44.1, secondaryValue: 30.1 },
        { period: 'FY2024', value: 45.9, secondaryValue: 31.2 },
        { period: 'FY2025', value: 46.2, secondaryValue: 32.0 },
      ],
      cashFlowSeries: [
        { period: 'FY2021', value: 104038, secondaryValue: 92953 },
        { period: 'FY2022', value: 122151, secondaryValue: 111443 },
        { period: 'FY2023', value: 110543, secondaryValue: 99584 },
        { period: 'FY2024', value: 118250, secondaryValue: 108810 },
        { period: 'FY2025', value: 124500, secondaryValue: 112400 },
      ],
    },
    MSFT: {
      name: 'Microsoft Corporation',
      ticker: 'MSFT',
      kpis: [
        { label: 'Revenue (FY2024)', value: '$245,120,000,000.00', compact: '$245.1B', change: '+15.7% YoY', isPos: true },
        { label: 'Net Income', value: '$88,140,000,000.00', compact: '$88.1B', change: '+21.8% YoY', isPos: true },
        { label: 'EBITDA', value: '$109,400,000,000.00', compact: '$109.4B', change: '+24.1% YoY', isPos: true },
        { label: 'Diluted EPS', value: '$11.80', compact: '$11.80', change: '+21.9% YoY', isPos: true },
        { label: 'Free Cash Flow', value: '$74,070,000,000.00', compact: '$74.1B', change: '+18.2% YoY', isPos: true },
        { label: 'Operating Margin', value: '44.6%', compact: '44.6%', change: '+280 bps', isPos: true },
      ],
      revenueSeries: [
        { period: 'FY2020', value: 143015, secondaryValue: 44281 },
        { period: 'FY2021', value: 168088, secondaryValue: 61271 },
        { period: 'FY2022', value: 198270, secondaryValue: 72738 },
        { period: 'FY2023', value: 211915, secondaryValue: 72361 },
        { period: 'FY2024', value: 245120, secondaryValue: 88140 },
      ],
      marginSeries: [
        { period: 'FY2020', value: 67.8, secondaryValue: 37.0 },
        { period: 'FY2021', value: 68.9, secondaryValue: 41.6 },
        { period: 'FY2022', value: 68.4, secondaryValue: 42.1 },
        { period: 'FY2023', value: 68.9, secondaryValue: 41.8 },
        { period: 'FY2024', value: 69.8, secondaryValue: 44.6 },
      ],
      cashFlowSeries: [
        { period: 'FY2020', value: 60675, secondaryValue: 45234 },
        { period: 'FY2021', value: 76740, secondaryValue: 56118 },
        { period: 'FY2022', value: 89035, secondaryValue: 65149 },
        { period: 'FY2023', value: 87582, secondaryValue: 59475 },
        { period: 'FY2024', value: 118548, secondaryValue: 74070 },
      ],
    },
  };

  const current = companiesData[selectedCompany] || companiesData['AAPL'];

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header Bar with Company & Period Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Financial Analysis</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-carbon-800 text-lime-400 border border-carbon-600">
              Multi-Year Terminal
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            Authoritative statement trends, operational margins, and cash flow generation ratios.
          </p>
        </div>

        {/* Company & Period Selectors */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-1.5 bg-carbon-900 border border-carbon-600 rounded-lg px-2.5 py-1.5">
            <Building2 className="w-3.5 h-3.5 text-lime-400" />
            <select
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
              className="bg-transparent text-white text-xs font-semibold focus:outline-none cursor-pointer"
            >
              <option value="AAPL" className="bg-carbon-900 text-white">Apple Inc. (AAPL)</option>
              <option value="MSFT" className="bg-carbon-900 text-white">Microsoft Corp (MSFT)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-carbon-900 border border-carbon-600 rounded-lg px-2.5 py-1.5">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
            <select
              value={selectedPeriodRange}
              onChange={(e) => setSelectedPeriodRange(e.target.value)}
              className="bg-transparent text-white text-xs font-mono focus:outline-none cursor-pointer"
            >
              <option value="2021-2025" className="bg-carbon-900 text-white">2021 → 2025 (5-Year)</option>
              <option value="2023-2025" className="bg-carbon-900 text-white">2023 → 2025 (3-Year)</option>
            </select>
          </div>

          <Button
            variant="lime"
            size="sm"
            onClick={() => onNavigateToAsk?.(`Perform a comprehensive financial analysis on ${current.name} (${current.ticker}) covering revenue growth, gross margin trajectory, and free cash flow.`)}
            icon={<Sparkles className="w-3.5 h-3.5" />}
          >
            Ask AI Analysis
          </Button>
        </div>
      </div>

      {/* 6 Key Financial Ratio Display Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {current.kpis.map((kpi: any, idx: number) => (
          <div
            key={idx}
            className="p-3.5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col justify-between gap-1 shadow-sm"
          >
            <span className="text-[10px] font-bold uppercase tracking-wider text-carbon-400 truncate" title={kpi.label}>
              {kpi.label}
            </span>
            <span className="text-lg font-bold font-mono text-white tracking-tight">
              {kpi.compact}
            </span>
            <div className="flex items-center justify-between text-[10px] font-mono">
              <span className="text-emerald-400 font-semibold">{kpi.change}</span>
              <span className="text-carbon-400 text-[9px]">Audited</span>
            </div>
          </div>
        ))}
      </div>

      {/* Main Analysis Chart Card */}
      <div className="p-5 rounded-2xl bg-carbon-900 border border-carbon-600/90 shadow-xl flex flex-col gap-4">
        {/* Metric Selector Tabs */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-carbon-700/60">
          <div className="flex items-center gap-1.5 bg-carbon-950 p-1 rounded-xl border border-carbon-700">
            {[
              { id: 'revenue', label: 'Revenue & Net Income' },
              { id: 'margins', label: 'Gross & Operating Margin (%)' },
              { id: 'cashFlow', label: 'Operating & Free Cash Flow' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setActiveChartMetric(m.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeChartMetric === m.id
                    ? 'bg-carbon-800 text-lime-400 shadow border border-carbon-600'
                    : 'text-carbon-400 hover:text-white'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3 text-xs font-mono text-carbon-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-lime-400" /> Primary Metric
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400" /> Secondary Metric
            </span>
          </div>
        </div>

        {/* Selected Chart */}
        <div className="pt-2">
          {activeChartMetric === 'revenue' && (
            <FinancialAreaChart
              data={current.revenueSeries}
              primaryLabel="Total Net Sales"
              secondaryLabel="Net Income"
              height={260}
              color="#d2f800"
              secondaryColor="#22d3ee"
              valueSuffix="$M"
              onExportCsv={() => alert('Exporting Revenue dataset as CSV')}
            />
          )}

          {activeChartMetric === 'margins' && (
            <FinancialAreaChart
              data={current.marginSeries}
              primaryLabel="Gross Margin (%)"
              secondaryLabel="Operating Margin (%)"
              height={260}
              color="#d2f800"
              secondaryColor="#22d3ee"
              valueSuffix="%"
              currencyPrefix=""
              onExportCsv={() => alert('Exporting Margins dataset as CSV')}
            />
          )}

          {activeChartMetric === 'cashFlow' && (
            <FinancialAreaChart
              data={current.cashFlowSeries}
              primaryLabel="Operating Cash Flow"
              secondaryLabel="Free Cash Flow"
              height={260}
              color="#d2f800"
              secondaryColor="#22d3ee"
              valueSuffix="$M"
              onExportCsv={() => alert('Exporting Cash Flow dataset as CSV')}
            />
          )}
        </div>

        {/* Statement Data Table */}
        <div className="mt-4 pt-4 border-t border-carbon-700/60 flex flex-col gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-300">
            Tabular Audited Data ({current.name})
          </span>
          <div className="overflow-x-auto rounded-xl border border-carbon-700/80 bg-carbon-950">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-carbon-900 border-b border-carbon-700 text-carbon-400 font-semibold uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Fiscal Year</th>
                  <th className="py-2.5 px-3 text-right">Revenue ($M)</th>
                  <th className="py-2.5 px-3 text-right">Net Income ($M)</th>
                  <th className="py-2.5 px-3 text-right">Gross Margin</th>
                  <th className="py-2.5 px-3 text-right">Operating Margin</th>
                  <th className="py-2.5 px-3 text-right">Free Cash Flow ($M)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-carbon-800">
                {current.revenueSeries.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-carbon-850 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-white">{row.period}</td>
                    <td className="py-2.5 px-3 text-right text-lime-400 font-bold">${row.value.toLocaleString()}.00</td>
                    <td className="py-2.5 px-3 text-right text-cyan-300">${row.secondaryValue.toLocaleString()}.00</td>
                    <td className="py-2.5 px-3 text-right text-carbon-200">{current.marginSeries[i]?.value || 45.2}%</td>
                    <td className="py-2.5 px-3 text-right text-emerald-400">{current.marginSeries[i]?.secondaryValue || 31.0}%</td>
                    <td className="py-2.5 px-3 text-right text-carbon-200">${(current.cashFlowSeries[i]?.secondaryValue || 95000).toLocaleString()}.00</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

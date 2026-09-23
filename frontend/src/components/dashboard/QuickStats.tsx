import React from 'react';
import { FileText, Building2, MessageSquareText, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { Sparkline } from '../charts/Sparkline';

export interface QuickStatsProps {
  documentCount?: number;
  companiesCount?: number;
  queriesCount?: number;
  citationsCount?: number;
  processingRate?: number;
  isSampleData?: boolean;
}

export const QuickStats: React.FC<QuickStatsProps> = ({
  documentCount = 1284,
  companiesCount = 86,
  queriesCount = 4821,
  citationsCount = 18493,
  processingRate = 98.7,
  isSampleData = false,
}) => {
  const stats = [
    {
      label: 'Documents',
      value: documentCount.toLocaleString(),
      subtext: '+12.4% this month',
      isPositive: true,
      icon: <FileText className="w-3.5 h-3.5 text-lime-400" />,
      sparklineData: [42, 48, 55, 62, 59, 70, 78, 85, 92, 98, 104, 118],
      sparklineColor: '#d2f800',
    },
    {
      label: 'Companies',
      value: companiesCount.toLocaleString(),
      subtext: 'Tracked entities',
      isPositive: null,
      icon: <Building2 className="w-3.5 h-3.5 text-cyan-400" />,
      sparklineData: [50, 54, 58, 62, 65, 68, 72, 75, 78, 81, 84, 86],
      sparklineColor: '#22d3ee',
    },
    {
      label: 'Queries',
      value: queriesCount.toLocaleString(),
      subtext: '+18.7% this month',
      isPositive: true,
      icon: <MessageSquareText className="w-3.5 h-3.5 text-lime-400" />,
      sparklineData: [180, 210, 240, 290, 320, 360, 410, 470, 510, 560, 610, 680],
      sparklineColor: '#d2f800',
    },
    {
      label: 'Citations',
      value: citationsCount.toLocaleString(),
      subtext: 'Verified sources',
      isPositive: true,
      icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />,
      sparklineData: [620, 710, 850, 940, 1100, 1280, 1420, 1580, 1750, 1920, 2100, 2350],
      sparklineColor: '#10b981',
    },
    {
      label: 'Processing',
      value: `${processingRate}%`,
      subtext: 'Successful ingestion',
      isPositive: true,
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
      sparklineData: [96.2, 96.8, 97.1, 97.4, 97.8, 98.0, 98.2, 98.4, 98.5, 98.6, 98.7, 98.7],
      sparklineColor: '#10b981',
    },
  ];

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between px-1">
        <span className="text-[10px] font-bold uppercase tracking-wider text-carbon-400">
          Core Workspace Metrics
        </span>
        <span
          className={`text-[9px] font-mono font-semibold px-2 py-0.5 rounded-full border ${
            isSampleData
              ? 'bg-amber-400/10 text-amber-400 border-amber-400/30'
              : 'bg-emerald-400/10 text-emerald-400 border-emerald-400/30'
          }`}
        >
          {isSampleData ? 'SAMPLE DATA' : 'LIVE DATA'}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {stats.map((stat, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-xl bg-carbon-900 border border-carbon-700/70 hover:border-carbon-500/80 transition-all duration-200 flex flex-col justify-between gap-2.5 group shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-medium uppercase tracking-wider text-carbon-300">
                {stat.label}
              </span>
              <div className="p-1 rounded bg-carbon-800 border border-carbon-700/60 text-carbon-300 group-hover:border-lime-400/40 transition-colors">
                {stat.icon}
              </div>
            </div>

            <div className="flex items-baseline justify-between gap-1">
              <span className="text-xl font-bold font-mono tracking-tight text-white">
                {stat.value}
              </span>
              <div className="w-16 h-6 shrink-0 opacity-80 group-hover:opacity-100 transition-opacity">
                <Sparkline data={stat.sparklineData} color={stat.sparklineColor} height={24} width={64} />
              </div>
            </div>

            <div className="flex items-center gap-1 text-[11px] font-mono">
              {stat.isPositive !== null && (
                <span className={stat.isPositive ? 'text-emerald-400' : 'text-rose-400'}>
                  {stat.isPositive ? '↑' : '↓'}
                </span>
              )}
              <span className={stat.isPositive ? 'text-emerald-400/90' : 'text-carbon-400'}>
                {stat.subtext}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

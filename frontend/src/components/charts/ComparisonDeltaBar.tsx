import React from 'react';

export interface ComparisonDeltaBarProps {
  label: string;
  metricA: { name: string; value: number; formatted: string; color?: string };
  metricB: { name: string; value: number; formatted: string; color?: string };
  higherIsBetter?: boolean;
}

export const ComparisonDeltaBar: React.FC<ComparisonDeltaBarProps> = ({
  label,
  metricA,
  metricB,
  higherIsBetter = true,
}) => {
  const total = Math.abs(metricA.value) + Math.abs(metricB.value) || 1;
  const pctA = (Math.abs(metricA.value) / total) * 100;
  const pctB = (Math.abs(metricB.value) / total) * 100;

  const isAWinner = higherIsBetter ? metricA.value >= metricB.value : metricA.value <= metricB.value;

  const colorA = metricA.color || '#d2f800';
  const colorB = metricB.color || '#06b6d4';

  return (
    <div className="flex flex-col gap-1.5 p-3 rounded-lg bg-carbon-900/60 border border-carbon-600/60 select-none">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-carbon-200 uppercase tracking-wider text-[11px]">{label}</span>
        <div className="flex items-center gap-3 font-mono-num text-xs">
          <span className="font-bold" style={{ color: colorA }}>
            {metricA.formatted}
          </span>
          <span className="text-carbon-500">vs</span>
          <span className="font-bold" style={{ color: colorB }}>
            {metricB.formatted}
          </span>
        </div>
      </div>

      {/* Dual Comparative Bar */}
      <div className="h-2 w-full flex rounded-full overflow-hidden bg-carbon-800 gap-0.5">
        <div
          className="h-full transition-all duration-500 rounded-l-full"
          style={{ width: `${pctA}%`, backgroundColor: colorA }}
          title={`${metricA.name}: ${metricA.formatted}`}
        />
        <div
          className="h-full transition-all duration-500 rounded-r-full"
          style={{ width: `${pctB}%`, backgroundColor: colorB }}
          title={`${metricB.name}: ${metricB.formatted}`}
        />
      </div>

      <div className="flex items-center justify-between text-[10px] text-carbon-400 font-mono">
        <span className="truncate">{metricA.name}</span>
        <span className="text-carbon-300">
          {isAWinner ? `${metricA.name} +${(pctA - pctB).toFixed(1)}% delta` : `${metricB.name} +${(pctB - pctA).toFixed(1)}% delta`}
        </span>
        <span className="truncate">{metricB.name}</span>
      </div>
    </div>
  );
};

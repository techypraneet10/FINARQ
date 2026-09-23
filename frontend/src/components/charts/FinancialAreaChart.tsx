import React, { useState } from 'react';

export interface DataPoint {
  period: string;
  value: number;
  secondaryValue?: number;
  label?: string;
}

export interface FinancialAreaChartProps {
  title?: string;
  subtitle?: string;
  data: DataPoint[];
  primaryLabel?: string;
  secondaryLabel?: string;
  currencyPrefix?: string;
  valueSuffix?: string;
  height?: number;
  color?: string;
  secondaryColor?: string;
  onExportCsv?: () => void;
}

export const FinancialAreaChart: React.FC<FinancialAreaChartProps> = ({
  title,
  subtitle,
  data,
  primaryLabel = 'Value',
  secondaryLabel,
  currencyPrefix = '$',
  valueSuffix = '',
  height = 240,
  color = '#d2f800',
  secondaryColor = '#06b6d4',
  onExportCsv,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-carbon-400 font-mono">
        No chart series data available
      </div>
    );
  }

  const values = data.map((d) => d.value);
  const secondaryValues = secondaryLabel ? data.map((d) => d.secondaryValue || 0) : [];
  const allValues = [...values, ...secondaryValues];
  const maxVal = Math.max(...allValues) * 1.1 || 100;
  const minVal = Math.min(0, Math.min(...allValues));
  const valRange = maxVal - minVal || 1;

  const svgWidth = 700;
  const svgHeight = height;
  const paddingLeft = 55;
  const paddingRight = 20;
  const paddingTop = 20;
  const paddingBottom = 35;

  const plotWidth = svgWidth - paddingLeft - paddingRight;
  const plotHeight = svgHeight - paddingTop - paddingBottom;

  const getX = (idx: number) => paddingLeft + (idx / (data.length - 1)) * plotWidth;
  const getY = (val: number) => paddingTop + plotHeight - ((val - minVal) / valRange) * plotHeight;

  const pointsPrimary = data.map((d, i) => `${getX(i).toFixed(1)},${getY(d.value).toFixed(1)}`);
  const pathDPrimary = `M ${pointsPrimary.join(' L ')}`;

  let pathDSecondary = '';
  if (secondaryLabel) {
    const pointsSecondary = data.map(
      (d, i) => `${getX(i).toFixed(1)},${getY(d.secondaryValue || 0).toFixed(1)}`
    );
    pathDSecondary = `M ${pointsSecondary.join(' L ')}`;
  }

  const yTicksCount = 4;
  const yTicks = Array.from({ length: yTicksCount + 1 }).map((_, i) => {
    const val = minVal + (i / yTicksCount) * valRange;
    const yPos = getY(val);
    return { val, yPos };
  });

  const activePoint = hoverIndex !== null ? data[hoverIndex] : null;

  return (
    <div className="flex flex-col gap-3 w-full">
      {(title || subtitle || onExportCsv) && (
        <div className="flex items-center justify-between">
          <div>
            {title && <h4 className="text-xs font-bold uppercase tracking-wider text-carbon-100">{title}</h4>}
            {subtitle && <p className="text-[11px] text-carbon-400 font-medium">{subtitle}</p>}
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-3 text-[11px]">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-carbon-300 font-medium">{primaryLabel}</span>
              </div>
              {secondaryLabel && (
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: secondaryColor }} />
                  <span className="text-carbon-300 font-medium">{secondaryLabel}</span>
                </div>
              )}
            </div>
            {onExportCsv && (
              <button
                onClick={onExportCsv}
                className="px-2 py-1 rounded bg-carbon-800 hover:bg-carbon-700 border border-carbon-600 text-[10px] font-mono text-carbon-300 hover:text-white transition-colors"
              >
                CSV Export
              </button>
            )}
          </div>
        </div>
      )}

      {/* SVG Canvas with Crosshairs and Hover Interactivity */}
      <div className="relative w-full overflow-hidden select-none">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto overflow-visible"
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id="area-gradient-primary" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.25" />
              <stop offset="100%" stopColor={color} stopOpacity="0.0" />
            </linearGradient>
            {secondaryLabel && (
              <linearGradient id="area-gradient-secondary" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={secondaryColor} stopOpacity="0.20" />
                <stop offset="100%" stopColor={secondaryColor} stopOpacity="0.0" />
              </linearGradient>
            )}
          </defs>

          {/* Horizontal Gridlines & Y-Axis Labels */}
          {yTicks.map((tick, idx) => (
            <g key={idx}>
              <line
                x1={paddingLeft}
                y1={tick.yPos}
                x2={svgWidth - paddingRight}
                y2={tick.yPos}
                stroke="#202326"
                strokeWidth="1"
                strokeDasharray={idx === 0 ? undefined : '3 3'}
              />
              <text
                x={paddingLeft - 8}
                y={tick.yPos + 3}
                fill="#656d76"
                fontSize="10"
                textAnchor="end"
                className="font-mono"
              >
                {currencyPrefix}
                {tick.val >= 1000 ? `${(tick.val / 1000).toFixed(1)}k` : tick.val.toFixed(0)}
                {valueSuffix}
              </text>
            </g>
          ))}

          {/* X-Axis Periods */}
          {data.map((d, i) => (
            <text
              key={i}
              x={getX(i)}
              y={svgHeight - 10}
              fill={hoverIndex === i ? '#f3f4f6' : '#656d76'}
              fontSize="10"
              fontWeight={hoverIndex === i ? '600' : '400'}
              textAnchor="middle"
              className="font-mono transition-colors"
            >
              {d.period}
            </text>
          ))}

          {/* Secondary Series Fill & Stroke */}
          {secondaryLabel && pathDSecondary && (
            <>
              <path
                d={`${pathDSecondary} L ${getX(data.length - 1)},${getY(minVal)} L ${getX(0)},${getY(minVal)} Z`}
                fill="url(#area-gradient-secondary)"
              />
              <path
                d={pathDSecondary}
                fill="none"
                stroke={secondaryColor}
                strokeWidth="2"
                strokeDasharray="4 2"
                strokeLinecap="round"
              />
            </>
          )}

          {/* Primary Series Fill & Stroke */}
          <path
            d={`${pathDPrimary} L ${getX(data.length - 1)},${getY(minVal)} L ${getX(0)},${getY(minVal)} Z`}
            fill="url(#area-gradient-primary)"
          />
          <path
            d={pathDPrimary}
            fill="none"
            stroke={color}
            strokeWidth="2.25"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Interactive Hover Columns */}
          {data.map((_, i) => (
            <rect
              key={i}
              x={getX(i) - plotWidth / (data.length * 2)}
              y={paddingTop}
              width={plotWidth / data.length}
              height={plotHeight}
              fill="transparent"
              className="cursor-crosshair"
              onMouseEnter={() => setHoverIndex(i)}
            />
          ))}

          {/* Crosshair Line and Active Dot */}
          {hoverIndex !== null && (
            <g>
              <line
                x1={getX(hoverIndex)}
                y1={paddingTop}
                x2={getX(hoverIndex)}
                y2={paddingTop + plotHeight}
                stroke="#484e54"
                strokeWidth="1.25"
                strokeDasharray="2 2"
              />
              <circle
                cx={getX(hoverIndex)}
                cy={getY(data[hoverIndex].value)}
                r="4.5"
                fill={color}
                stroke="#08090a"
                strokeWidth="2"
              />
              {secondaryLabel && data[hoverIndex].secondaryValue !== undefined && (
                <circle
                  cx={getX(hoverIndex)}
                  cy={getY(data[hoverIndex].secondaryValue || 0)}
                  r="4.5"
                  fill={secondaryColor}
                  stroke="#08090a"
                  strokeWidth="2"
                />
              )}
            </g>
          )}
        </svg>

        {/* Floating Tooltip */}
        {activePoint && hoverIndex !== null && (
          <div
            className="absolute z-10 pointer-events-none p-2 rounded-lg bg-carbon-900 border border-carbon-600 shadow-xl text-xs flex flex-col gap-1 backdrop-blur-md animate-fade-in"
            style={{
              left: `${Math.min(Math.max((getX(hoverIndex) / svgWidth) * 100, 15), 85)}%`,
              top: '15px',
              transform: 'translateX(-50%)',
            }}
          >
            <div className="text-[10px] font-mono uppercase tracking-wider text-carbon-400 font-bold border-b border-carbon-700 pb-1">
              {activePoint.period}
            </div>
            <div className="flex items-center justify-between gap-4 font-mono-num font-semibold text-white">
              <span className="text-[11px] text-carbon-300 font-sans">{primaryLabel}:</span>
              <span style={{ color }}>
                {currencyPrefix}
                {activePoint.value.toLocaleString()}
                {valueSuffix}
              </span>
            </div>
            {secondaryLabel && activePoint.secondaryValue !== undefined && (
              <div className="flex items-center justify-between gap-4 font-mono-num font-semibold text-white">
                <span className="text-[11px] text-carbon-300 font-sans">{secondaryLabel}:</span>
                <span style={{ color: secondaryColor }}>
                  {currencyPrefix}
                  {activePoint.secondaryValue.toLocaleString()}
                  {valueSuffix}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

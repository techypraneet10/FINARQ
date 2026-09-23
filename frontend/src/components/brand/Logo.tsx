import React from 'react';

export interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showTagline?: boolean;
  className?: string;
}

export const Logo: React.FC<LogoProps> = ({
  size = 'md',
  showTagline = false,
  className = '',
}) => {
  const iconSizes = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
  };

  const textSizes = {
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-2xl',
  };

  return (
    <div className={`flex items-center gap-2.5 select-none ${className}`}>
      {/* Geometric Finarq Verification / Intelligence Mark */}
      <div
        className={`${iconSizes[size]} rounded-lg bg-gradient-to-br from-carbon-750 via-carbon-850 to-carbon-950 border border-carbon-600 flex items-center justify-center shadow-lg shadow-black/80 shrink-0 relative overflow-hidden group`}
      >
        {/* Subtle lime/emerald sheen glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-lime-400/20 via-transparent to-emerald-500/10 pointer-events-none" />
        
        {/* Abstract Multi-Facet Geometric Prism Icon */}
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-4/6 h-4/6 text-lime-400 drop-shadow-[0_0_8px_rgba(210,248,0,0.5)]"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      </div>

      <div className="flex flex-col min-w-0">
        <div className="flex items-center gap-1.5 leading-none">
          <span className={`font-black tracking-wider text-carbon-50 uppercase ${textSizes[size]}`}>
            FINARQ
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-lime-400 animate-pulse shadow-[0_0_8px_#d2f800]" title="System Operational" />
        </div>
        {showTagline && (
          <span className="text-[10px] uppercase font-mono tracking-widest text-carbon-300 font-semibold truncate mt-0.5">
            Document Intelligence
          </span>
        )}
      </div>
    </div>
  );
};


import React from 'react';

export interface BadgeProps {
  variant?: 'lime' | 'emerald' | 'amber' | 'rose' | 'purple' | 'cyan' | 'slate' | 'outline';
  size?: 'xs' | 'sm' | 'md';
  children: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'slate',
  size = 'sm',
  children,
  className = '',
  icon,
}) => {
  const variantStyles = {
    lime: 'bg-lime-950/70 text-lime-300 border border-lime-400/40',
    emerald: 'bg-emerald-950/70 text-emerald-400 border border-emerald-500/30',
    amber: 'bg-amber-950/70 text-amber-400 border border-amber-500/30',
    rose: 'bg-rose-950/70 text-rose-400 border border-rose-500/30',
    purple: 'bg-purple-950/70 text-purple-400 border border-purple-500/30',
    cyan: 'bg-cyan-950/70 text-cyan-400 border border-cyan-500/30',
    slate: 'bg-carbon-800 text-carbon-200 border border-carbon-600',
    outline: 'bg-transparent text-carbon-300 border border-carbon-600',
  };

  const sizeStyles = {
    xs: 'text-[10px] px-1.5 py-0.5 rounded gap-1 font-semibold tracking-wider uppercase',
    sm: 'text-xs px-2 py-0.5 rounded-md gap-1.5 font-medium',
    md: 'text-sm px-2.5 py-1 rounded-md gap-2 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center select-none font-mono-num ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

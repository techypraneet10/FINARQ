import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'lime' | 'secondary' | 'purple' | 'emerald' | 'danger' | 'ghost' | 'outline' | 'cyan';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  icon,
  className = '',
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lime-400 focus-visible:ring-offset-2 focus-visible:ring-offset-carbon-950 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none select-none cursor-pointer';

  const variantStyles = {
    primary:
      'bg-lime-400 hover:bg-lime-300 text-carbon-950 font-semibold shadow-sm hover:shadow-glow-lime active:scale-[0.98] border border-lime-400',
    lime:
      'bg-lime-400/15 hover:bg-lime-400/25 text-lime-300 border border-lime-400/40 active:scale-[0.98]',
    purple:
      'bg-purple-500/15 hover:bg-purple-500/25 text-purple-300 border border-purple-500/30 active:scale-[0.98]',
    emerald:
      'bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 active:scale-[0.98]',
    cyan:
      'bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-400 border border-cyan-500/30 active:scale-[0.98]',
    secondary:
      'bg-carbon-800 hover:bg-carbon-700 text-carbon-100 border border-carbon-600 shadow-sm active:scale-[0.98]',
    danger:
      'bg-rose-600 hover:bg-rose-500 text-white shadow-sm shadow-rose-950/80 active:scale-[0.98]',
    outline:
      'border border-carbon-600 hover:border-carbon-500 text-carbon-200 hover:bg-carbon-800 active:scale-[0.98]',
    ghost:
      'text-carbon-400 hover:text-carbon-100 hover:bg-carbon-800/60 active:scale-[0.98]',
  };

  const sizeStyles = {
    xs: 'text-[11px] px-2 py-1 gap-1',
    sm: 'text-xs px-2.5 py-1.5 gap-1.5',
    md: 'text-sm px-3.5 py-2 gap-2',
    lg: 'text-base px-5 py-2.5 gap-2.5',
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current shrink-0" />
      ) : (
        icon && <span className="inline-flex shrink-0">{icon}</span>
      )}
      {children && <span>{children}</span>}
    </button>
  );
};

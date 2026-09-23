import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'glass' | 'solid' | 'subtle' | 'metallic';
  children: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  variant = 'glass',
  children,
  header,
  footer,
  title,
  subtitle,
  badge,
  actions,
  className = '',
  ...props
}) => {
  const variantStyles = {
    glass: 'glass-card',
    metallic: 'metallic-card rounded-xl',
    solid: 'bg-carbon-900 border border-carbon-600 rounded-xl shadow-lg',
    subtle: 'bg-carbon-900/50 border border-carbon-600/70 rounded-xl',
  };

  return (
    <div className={`${variantStyles[variant]} overflow-hidden ${className}`} {...props}>
      {(header || title || subtitle || actions || badge) && (
        <div className="px-4 py-3 border-b border-carbon-600/80 flex items-center justify-between gap-3">
          {header ? (
            header
          ) : (
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-2">
                {title && <h3 className="text-sm font-semibold text-carbon-100 truncate">{title}</h3>}
                {badge}
              </div>
              {subtitle && <p className="text-[11px] text-carbon-400 truncate mt-0.5">{subtitle}</p>}
            </div>
          )}
          {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
        </div>
      )}
      <div className="p-4">{children}</div>
      {footer && <div className="px-4 py-3 bg-carbon-950/50 border-t border-carbon-600/80">{footer}</div>}
    </div>
  );
};


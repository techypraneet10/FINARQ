import React from 'react';

export interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rectangular' | 'circular';
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', variant = 'rectangular' }) => {
  const variantStyles = {
    text: 'h-4 rounded w-full',
    rectangular: 'rounded-lg w-full',
    circular: 'rounded-full',
  };

  return <div className={`animate-pulse bg-slate-800/80 ${variantStyles[variant]} ${className}`} />;
};

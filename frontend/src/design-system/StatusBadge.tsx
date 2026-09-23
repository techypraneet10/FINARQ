import React from 'react';
import { getAnswerabilityStatusBadge, getGroundingStatusBadge } from '../utils/formatters';

export interface StatusBadgeProps {
  type: 'answerability' | 'grounding' | 'ingestion' | 'custom';
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, status, className = '' }) => {
  let badgeConfig = { label: status, bg: 'bg-slate-800', text: 'text-slate-300', border: 'border-slate-700' };

  if (type === 'answerability') {
    badgeConfig = getAnswerabilityStatusBadge(status);
  } else if (type === 'grounding') {
    badgeConfig = getGroundingStatusBadge(status);
  } else if (type === 'ingestion') {
    switch (status?.toLowerCase()) {
      case 'completed':
        badgeConfig = { label: 'Completed', bg: 'bg-emerald-950/70', text: 'text-emerald-400', border: 'border-emerald-500/40' };
        break;
      case 'processing':
        badgeConfig = { label: 'Processing', bg: 'bg-cyan-950/70', text: 'text-cyan-400', border: 'border-cyan-500/40' };
        break;
      case 'pending':
        badgeConfig = { label: 'Queued', bg: 'bg-amber-950/70', text: 'text-amber-400', border: 'border-amber-500/40' };
        break;
      case 'failed':
        badgeConfig = { label: 'Failed', bg: 'bg-rose-950/70', text: 'text-rose-400', border: 'border-rose-500/40' };
        break;
      default:
        badgeConfig = { label: status, bg: 'bg-slate-800', text: 'text-slate-300', border: 'border-slate-700' };
    }
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border select-none ${badgeConfig.bg} ${badgeConfig.text} ${badgeConfig.border} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {badgeConfig.label}
    </span>
  );
};

import React from 'react';
import { ClaimResponse } from '../../api/types';
import { CheckCircle2, AlertCircle, ShieldAlert } from 'lucide-react';
import { Badge } from '../../design-system/Badge';

export interface ClaimListProps {
  claims: ClaimResponse[];
  onSelectCitation?: (claimId: string) => void;
}

export const ClaimList: React.FC<ClaimListProps> = ({ claims, onSelectCitation }) => {
  if (!claims || claims.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Atomic Claims & Grounding Validation ({claims.length})
        </span>
        <span className="text-xs text-slate-500 font-mono">
          {claims.filter((c) => c.is_grounded).length} / {claims.length} Grounded
        </span>
      </div>

      <div className="flex flex-col gap-2.5">
        {claims.map((claim) => (
          <div
            key={claim.claim_id}
            onClick={() => onSelectCitation && onSelectCitation(claim.claim_id)}
            className={`p-3.5 rounded-xl border flex items-start gap-3 transition-all ${
              claim.is_grounded
                ? 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                : 'bg-rose-950/20 border-rose-500/40 hover:border-rose-500/60'
            }`}
          >
            <div className="mt-0.5">
              {claim.is_grounded ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
              )}
            </div>

            <div className="flex-1 min-w-0 flex flex-col gap-1">
              <p className="text-xs text-slate-200 leading-relaxed font-sans">
                {claim.text}
              </p>
              <div className="flex items-center gap-2 flex-wrap pt-0.5 font-mono text-[10px]">
                <Badge variant={claim.is_grounded ? 'emerald' : 'rose'} size="xs">
                  {claim.is_grounded ? 'Audited Grounded' : 'Ungrounded / Caveat'}
                </Badge>
                <span className="text-slate-400">
                  Confidence: <span className="text-slate-200">{(claim.confidence * 100).toFixed(0)}%</span>
                </span>
                {claim.source_fact_ids.length > 0 && (
                  <span className="text-slate-500">
                    · {claim.source_fact_ids.length} Linked Facts
                  </span>
                )}
                {claim.calculation_ids.length > 0 && (
                  <span className="text-slate-500">
                    · {claim.calculation_ids.length} Calculations
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

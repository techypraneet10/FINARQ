import React from 'react';
import { EvidenceConflictResponse } from '../../api/types';
import { AlertTriangle, CheckCircle2, ShieldCheck } from 'lucide-react';
import { Badge } from '../../design-system/Badge';

export interface ConflictResolutionCardProps {
  conflicts: EvidenceConflictResponse[];
}

export const ConflictResolutionCard: React.FC<ConflictResolutionCardProps> = ({ conflicts }) => {
  if (!conflicts || conflicts.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      {conflicts.map((conf) => (
        <div
          key={conf.conflict_id}
          className="p-4 rounded-2xl bg-orange-950/20 border border-orange-500/40 flex flex-col gap-3 shadow-md"
        >
          {/* Header */}
          <div className="flex items-center justify-between gap-4 border-b border-orange-500/30 pb-2.5">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-orange-950 border border-orange-500/50 text-orange-400">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-orange-200">
                  Evidence Conflict Detected: {conf.metric}
                </h4>
                <span className="text-[11px] text-orange-300 font-mono">Period: {conf.period}</span>
              </div>
            </div>
            {conf.resolved ? (
              <Badge variant="emerald" size="xs" icon={<CheckCircle2 className="w-3 h-3" />}>
                Resolved by Precedence
              </Badge>
            ) : (
              <Badge variant="amber" size="xs">
                Unresolved Conflict
              </Badge>
            )}
          </div>

          {/* Conflict Description */}
          <p className="text-xs text-slate-200 leading-relaxed font-sans">
            {conf.difference_description}
          </p>

          {/* Conflicting Facts Comparison Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {conf.conflicting_facts.map((fact, idx) => {
              const isChosen = conf.resolved_fact_id === fact.fact_id;
              return (
                <div
                  key={fact.fact_id}
                  className={`p-3 rounded-xl border flex flex-col gap-1.5 text-xs font-mono transition-all ${
                    isChosen
                      ? 'bg-emerald-950/40 border-emerald-500/60 text-emerald-200 shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-300">
                      Source #{idx + 1} ({fact.extraction_method})
                    </span>
                    {isChosen && (
                      <Badge variant="emerald" size="xs" icon={<ShieldCheck className="w-3 h-3" />}>
                        Authoritative
                      </Badge>
                    )}
                  </div>
                  <div className="text-sm font-bold text-slate-100">
                    {fact.value.currency || '$'}{fact.value.display_value} {fact.value.unit}
                  </div>
                  <span className="text-[10px] text-slate-500 truncate">
                    Page {fact.page_number} · Confidence {(fact.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              );
            })}
          </div>

          {/* Resolution Rationale */}
          {conf.resolution_rationale && (
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300">
              <strong className="text-emerald-400">Resolution Rationale:</strong>{' '}
              {conf.resolution_rationale}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

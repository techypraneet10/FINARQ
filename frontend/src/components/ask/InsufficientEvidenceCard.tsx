import React from 'react';
import { HelpCircle, FileSearch } from 'lucide-react';
import { Badge } from '../../design-system/Badge';

export interface InsufficientEvidenceCardProps {
  rationale?: string;
  missingFacts?: string[];
  documentsSearchedCount?: number;
}

export const InsufficientEvidenceCard: React.FC<InsufficientEvidenceCardProps> = ({
  rationale,
  missingFacts,
  documentsSearchedCount,
}) => {
  return (
    <div className="p-5 rounded-2xl bg-purple-950/25 border border-purple-500/40 flex flex-col gap-3.5 shadow-lg">
      <div className="flex items-center justify-between gap-4 border-b border-purple-500/30 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-purple-950 border border-purple-500/50 text-purple-400">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold uppercase tracking-wider text-purple-200">
              Insufficient Grounding Evidence
            </h4>
            <span className="text-xs text-purple-300 font-mono">
              Deterministic Refusal to Hallucinate Unverified Financial Data
            </span>
          </div>
        </div>
        <Badge variant="purple" size="xs">
          Zero Speculation
        </Badge>
      </div>

      <p className="text-xs text-slate-200 leading-relaxed">
        {rationale ||
          'The retrieved documents do not contain authoritative, unambiguous evidence required to calculate or confirm this metric with high confidence.'}
      </p>

      {missingFacts && missingFacts.length > 0 && (
        <div className="flex flex-col gap-1.5 pt-1">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-purple-300">
            Missing / Unresolved Metrics:
          </span>
          <div className="flex flex-wrap gap-2">
            {missingFacts.map((fact, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-lg bg-slate-900 border border-purple-500/30 text-xs font-mono text-purple-300"
              >
                {fact}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 text-xs text-slate-400 pt-1">
        <FileSearch className="w-4 h-4 text-purple-400" />
        <span>
          Searched {documentsSearchedCount || 'all'} workspace documents in Qdrant vector index. Consider uploading the corresponding 10-K or earnings release.
        </span>
      </div>
    </div>
  );
};

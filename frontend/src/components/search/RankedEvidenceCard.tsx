import React from 'react';
import { RankedEvidenceResponse } from '../../api/types';
import { Badge } from '../../design-system/Badge';
import { FileText, Layers, ExternalLink, Table as TableIcon } from 'lucide-react';
import { Button } from '../../design-system/Button';
import { useWorkspace } from '../../context/WorkspaceContext';

export interface RankedEvidenceCardProps {
  evidence: RankedEvidenceResponse;
  onNavigateToDocument?: (documentId: string, pageNumber?: number) => void;
  onAskFollowUp?: (queryText: string) => void;
}

export const RankedEvidenceCard: React.FC<RankedEvidenceCardProps> = ({
  evidence,
  onNavigateToDocument,
  onAskFollowUp,
}) => {
  const { openEvidenceDrawer } = useWorkspace();
  const isTable = evidence.chunk_type === 'table';

  return (
    <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md hover:border-slate-700 transition-all flex flex-col gap-3">
      {/* Top Metadata Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="cyan" size="xs">
            Rank #{evidence.rank}
          </Badge>
          {evidence.ticker && (
            <Badge variant="emerald" size="xs">
              {evidence.ticker}
            </Badge>
          )}
          <Badge variant={isTable ? 'emerald' : 'slate'} size="xs" icon={isTable ? <TableIcon className="w-3 h-3" /> : <FileText className="w-3 h-3" />}>
            {isTable ? 'Structured Table' : 'Text Section'}
          </Badge>
          <span className="text-xs font-mono text-slate-300 font-semibold">
            Page {evidence.page_number}
          </span>
          {evidence.fiscal_year && (
            <span className="text-xs text-slate-400 font-mono">
              ({evidence.fiscal_period || 'FY'} {evidence.fiscal_year})
            </span>
          )}
        </div>

        {/* Score Transparency Badges */}
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="text-slate-400" title="Reciprocal Rank Fusion (BM25 + Dense)">
            RRF: <span className="text-emerald-400 font-semibold">{evidence.fusion_score.toFixed(4)}</span>
          </span>
          {evidence.reranker_score !== null && evidence.reranker_score !== undefined && (
            <span className="text-slate-400" title="Cross-Encoder Reranker Score">
              · Rerank: <span className="text-cyan-400 font-semibold">{evidence.reranker_score.toFixed(3)}</span>
            </span>
          )}
        </div>
      </div>

      {/* Hierarchical Section Path */}
      {evidence.section_path && (
        <span className="text-xs font-medium text-slate-400 truncate">
          {evidence.section_path}
        </span>
      )}

      {/* Snippet Content */}
      <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-850 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto selection:bg-emerald-900 selection:text-white">
        {evidence.content}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-850">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => openEvidenceDrawer(undefined, evidence)}
            icon={<Layers className="w-3.5 h-3.5 text-emerald-400" />}
          >
            Inspect Provenance
          </Button>
          {onNavigateToDocument && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigateToDocument(evidence.document_id, evidence.page_number)}
              icon={<ExternalLink className="w-3.5 h-3.5" />}
            >
              Open Page
            </Button>
          )}
        </div>

        {onAskFollowUp && (
          <Button
            variant="emerald"
            size="sm"
            onClick={() => onAskFollowUp(`Based on ${evidence.ticker || 'the filing'} page ${evidence.page_number}: `)}
          >
            Ask Question
          </Button>
        )}
      </div>
    </div>
  );
};

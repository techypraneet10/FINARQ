import React, { useState } from 'react';
import { useWorkspace, SavedAnalysis } from '../../context/WorkspaceContext';
import {
  Bookmark,
  Trash2,
  ExternalLink,
  Download,
  Calendar,
  Layers,
  FileSpreadsheet,
  FileCode,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Badge } from '../../design-system/Badge';
import { Modal } from '../../design-system/Modal';
import { formatDateTime } from '../../utils/formatters';

export interface SavedAnalysesViewProps {
  onLoadAnalysis: (query: string) => void;
}

export const SavedAnalysesView: React.FC<SavedAnalysesViewProps> = ({ onLoadAnalysis }) => {
  const { savedAnalyses, deleteSavedAnalysis, notify } = useWorkspace();
  const [selectedAnalysis, setSelectedAnalysis] = useState<SavedAnalysis | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);

  const exportAsJson = (analysis: SavedAnalysis) => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(analysis, null, 2));
    const a = document.createElement('a');
    a.href = dataStr;
    a.download = `analysis_${analysis.id}.json`;
    a.click();
    notify('success', 'Analysis exported as JSON.');
  };

  const exportAsMarkdown = (analysis: SavedAnalysis) => {
    let md = `# ${analysis.title}\n\n**Query:** ${analysis.query}\n**Date:** ${analysis.created_at}\n\n## Verified Answer\n${analysis.answer_text}\n\n## Citations\n`;
    analysis.citations.forEach((c) => {
      md += `- **[${c.citation_id || 'C1'}]** Page ${c.page_number} (${c.ticker || 'Doc'}): ${c.source_excerpt}\n`;
    });
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_${analysis.id}.md`;
    a.click();
    notify('success', 'Analysis exported as Markdown.');
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-100">Saved Financial Research</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Audited answers, formulas, and verified citation references saved in your tenant repository.
        </p>
      </div>

      {savedAnalyses.length === 0 ? (
        <div className="text-center py-16 p-8 rounded-3xl border border-dashed border-slate-800 bg-slate-950/20">
          <Bookmark className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h4 className="text-base font-semibold text-slate-200">No Saved Analyses</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            When you ask financial questions in the workspace, click "Save Analysis" to pin verified reports here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {savedAnalyses.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between gap-4 shadow-md hover:border-slate-700 transition-all"
            >
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="emerald" size="xs">
                    {item.grounding_status}
                  </Badge>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {formatDateTime(item.created_at)}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-slate-100 line-clamp-1">{item.title}</h3>
                <p className="text-xs text-slate-400 font-mono line-clamp-2 bg-slate-950/70 p-2.5 rounded-lg border border-slate-850">
                  {item.query}
                </p>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-850">
                <div className="flex items-center gap-2">
                  <Button
                    variant="emerald"
                    size="sm"
                    onClick={() => onLoadAnalysis(item.query)}
                    icon={<ExternalLink className="w-3.5 h-3.5" />}
                  >
                    Open
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => exportAsMarkdown(item)}
                    icon={<FileCode className="w-3.5 h-3.5" />}
                  >
                    MD
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => exportAsJson(item)}
                    icon={<Download className="w-3.5 h-3.5" />}
                  >
                    JSON
                  </Button>
                </div>

                <button
                  onClick={() => deleteSavedAnalysis(item.id)}
                  className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded-lg transition-colors"
                  title="Remove from saved library"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

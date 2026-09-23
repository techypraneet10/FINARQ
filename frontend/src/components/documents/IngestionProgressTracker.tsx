import React from 'react';
import { IngestionJobResponse } from '../../api/types';
import { CheckCircle2, Clock, AlertCircle, Loader2, Cpu, ShieldCheck, Database, Layers, FileText } from 'lucide-react';

export interface IngestionProgressTrackerProps {
  job: IngestionJobResponse;
}

const VISUAL_PIPELINE_STAGES = [
  { id: 'upload', label: 'Upload', desc: 'Secure multipart transfer' },
  { id: 'validation', label: 'Document Validation', desc: 'SHA-256 integrity' },
  { id: 'ocr', label: 'OCR & Layout', desc: 'Visual geometry detection' },
  { id: 'parsing', label: 'Document Parsing', desc: 'SEC item hierarchy' },
  { id: 'table_extraction', label: 'Table Extraction', desc: 'Financial matrix parsing' },
  { id: 'chunking', label: 'Chunking', desc: 'Structure-aware semantic' },
  { id: 'embedding', label: 'Embedding', desc: 'text-embedding-3-large' },
  { id: 'indexing', label: 'Vector Indexing', desc: 'Qdrant + BM25 sparse' },
  { id: 'completed', label: 'Ready', desc: 'Audited & groundable' },
];

export const IngestionProgressTracker: React.FC<IngestionProgressTrackerProps> = ({ job }) => {
  const isFailed = job.status === 'failed';
  const isCompleted = job.status === 'completed';

  // Map backend current_stage to our 9-step sequence
  const currentStage = job.current_stage || 'embedding';
  let activeIndex = 6; // Default to embedding for demo
  if (isCompleted) activeIndex = 8;
  else if (currentStage === 'queued') activeIndex = 0;
  else if (currentStage === 'parsing') activeIndex = 3;
  else if (currentStage === 'table_extraction') activeIndex = 4;
  else if (currentStage === 'chunking') activeIndex = 5;
  else if (currentStage === 'embedding') activeIndex = 6;
  else if (currentStage === 'indexing') activeIndex = 7;

  return (
    <div className="flex flex-col gap-4 p-5 rounded-2xl bg-carbon-900 border border-carbon-600/90 shadow-xl text-carbon-100 animate-fade-in">
      {/* Status Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-carbon-700/60 pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-carbon-800 border border-carbon-600 text-lime-400">
            {isCompleted ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : isFailed ? (
              <AlertCircle className="w-5 h-5 text-rose-400" />
            ) : (
              <Loader2 className="w-5 h-5 animate-spin text-lime-400" />
            )}
          </div>
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <span>{isCompleted ? 'Document Successfully Processed' : isFailed ? 'Ingestion Pipeline Failed' : 'Asynchronous Pipeline Ingestion'}</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-carbon-800 text-lime-400 border border-carbon-700">
                {isCompleted ? '100% Ready' : `${job.progress_pct || 87}% Progress`}
              </span>
            </h4>
            <span className="text-xs text-carbon-400 font-mono">
              Job ID: {job.id} · Stage: {VISUAL_PIPELINE_STAGES[activeIndex]?.label || 'Processing'}
            </span>
          </div>
        </div>

        <div className="text-right font-mono">
          <span className="text-sm font-bold text-lime-400">{job.chunks_indexed || 184} Chunks</span>
          <div className="text-[10px] text-carbon-400">
            Vectorized & Inverted Index
          </div>
        </div>
      </div>

      {/* Progress Bar with Block Fill */}
      <div className="flex flex-col gap-1.5 p-3 rounded-xl bg-carbon-950 border border-carbon-700/60 font-mono text-xs">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-carbon-300 font-bold flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-lime-400" />
            Active Stage: {VISUAL_PIPELINE_STAGES[activeIndex]?.label}
          </span>
          <span className="text-lime-400 font-bold">{isCompleted ? '100%' : `${job.progress_pct || 87}%`}</span>
        </div>

        {/* ASCII Block Visualizer */}
        <div className="w-full bg-carbon-800 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-lime-400 h-full rounded-full transition-all duration-500 shadow-[0_0_8px_#d2f800]"
            style={{ width: `${isCompleted ? 100 : job.progress_pct || 87}%` }}
          />
        </div>
      </div>

      {/* 9-Stage Visual Pipeline Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-9 gap-2 pt-1">
        {VISUAL_PIPELINE_STAGES.map((stg, idx) => {
          const isPast = isCompleted || idx < activeIndex;
          const isCurrent = !isCompleted && !isFailed && idx === activeIndex;
          const isStageFailed = isFailed && idx === activeIndex;

          return (
            <div
              key={stg.id}
              className={`p-2.5 rounded-xl border flex flex-col justify-between gap-1 transition-all ${
                isStageFailed
                  ? 'bg-rose-950/60 border-rose-500/50 text-rose-300'
                  : isPast
                  ? 'bg-carbon-950 border-emerald-500/40 text-emerald-400 shadow-sm'
                  : isCurrent
                  ? 'bg-carbon-800 border-lime-400/80 text-white shadow-[0_0_10px_rgba(210,248,0,0.15)]'
                  : 'bg-carbon-950/50 border-carbon-700/60 text-carbon-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold">0{idx + 1}</span>
                {isPast ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-lime-400" />
                ) : isStageFailed ? (
                  <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                ) : (
                  <Clock className="w-3 h-3 text-carbon-500" />
                )}
              </div>
              <span className="text-[11px] font-semibold leading-tight line-clamp-2">
                {stg.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Error Diagnostics if failed */}
      {isFailed && job.error_message && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 flex flex-col gap-1">
          <span className="font-semibold uppercase tracking-wider text-[10px] text-rose-400">
            Pipeline Failure Diagnostics
          </span>
          <p className="font-mono text-carbon-200">{job.error_message}</p>
        </div>
      )}
    </div>
  );
};

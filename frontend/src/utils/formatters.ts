/**
 * Financial Formatting Utilities.
 * Strictly preserves accounting semantics, negative parentheses (1,234.50),
 * currency codes, scales, and precision. Does not perform client arithmetic.
 */

export function formatAccountingValue(
  value: string | number | null | undefined,
  options: {
    currency?: string | null;
    scale?: string | number;
    isNegative?: boolean;
    isPercentage?: boolean;
    precision?: number;
  } = {}
): string {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  const { currency = '$', isPercentage = false, precision = 2 } = options;
  const numStr = String(value).trim();
  const num = parseFloat(numStr.replace(/[^0-9.-]/g, ''));

  if (isNaN(num)) {
    return numStr;
  }

  const isNeg = options.isNegative || num < 0 || numStr.startsWith('(') || numStr.startsWith('-');
  const absNum = Math.abs(num);

  const formattedAbs = absNum.toLocaleString('en-US', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  });

  if (isPercentage) {
    return isNeg ? `(${formattedAbs}%)` : `${formattedAbs}%`;
  }

  const currPrefix = currency ? (currency === 'USD' ? '$' : currency) : '';
  if (isNeg) {
    return `(${currPrefix}${formattedAbs})`;
  }
  return `${currPrefix}${formattedAbs}`;
}

export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(d);
  } catch {
    return isoString;
  }
}

export function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - d.getTime()) / 1000);

    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return `${Math.floor(diffSec / 86400)}d ago`;
  } catch {
    return isoString;
  }
}

export function getGroundingStatusBadge(status: string): { label: string; bg: string; text: string; border: string } {
  switch (status?.toLowerCase()) {
    case 'grounded':
      return { label: '100% Grounded', bg: 'bg-emerald-950/60', text: 'text-emerald-400', border: 'border-emerald-500/40' };
    case 'partially_grounded':
      return { label: 'Partially Grounded', bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-500/40' };
    case 'ungrounded':
      return { label: 'Ungrounded', bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-500/40' };
    case 'conflicting':
      return { label: 'Conflicting Evidence', bg: 'bg-orange-950/60', text: 'text-orange-400', border: 'border-orange-500/40' };
    default:
      return { label: status || 'Unknown', bg: 'bg-slate-800/60', text: 'text-slate-300', border: 'border-slate-700' };
  }
}

export function getAnswerabilityStatusBadge(state: string): { label: string; bg: string; text: string; border: string } {
  switch (state?.toLowerCase()) {
    case 'answerable':
    case 'completed':
      return { label: 'Answerable', bg: 'bg-emerald-950/60', text: 'text-emerald-400', border: 'border-emerald-500/40' };
    case 'partially_answerable':
      return { label: 'Partially Answerable', bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-500/40' };
    case 'insufficient_evidence':
      return { label: 'Insufficient Evidence', bg: 'bg-purple-950/60', text: 'text-purple-400', border: 'border-purple-500/40' };
    case 'conflicting_evidence':
      return { label: 'Conflicting Evidence', bg: 'bg-orange-950/60', text: 'text-orange-400', border: 'border-orange-500/40' };
    case 'calculation_failed':
      return { label: 'Calculation Error', bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-500/40' };
    case 'grounding_failed':
      return { label: 'Grounding Audit Failed', bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-500/40' };
    default:
      return { label: state || 'Unknown', bg: 'bg-slate-800/60', text: 'text-slate-300', border: 'border-slate-700' };
  }
}

export function getIngestionStageLabel(stage: string): string {
  const map: Record<string, string> = {
    queued: 'Queued',
    uploaded: 'Uploaded',
    classifying: 'Classifying Document',
    parsing: 'Parsing PDF Layout',
    ocr: 'Running Tesseract OCR',
    normalizing: 'Normalizing Financial Values',
    table_extraction: 'Extracting Financial Tables',
    chunking: 'Structure-Aware Chunking',
    embedding: 'Generating Vector Embeddings',
    indexing: 'Indexing in Qdrant & BM25',
    completed: 'Ingestion Completed',
    failed: 'Ingestion Failed',
  };
  return map[stage] || stage;
}

import React from 'react';
import { CalculationResultResponse } from '../../api/types';
import { Calculator, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';
import { Badge } from '../../design-system/Badge';

export interface CalculationBlockProps {
  calculation: CalculationResultResponse;
  onInspectFact?: (factId: string) => void;
}

export const CalculationBlock: React.FC<CalculationBlockProps> = ({ calculation, onInspectFact }) => {
  const formattedOpName = calculation.operation
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="p-4 rounded-xl bg-carbon-950 border border-carbon-700/60 flex flex-col gap-3 shadow-sm text-carbon-100">
      {/* Operation Title & Status */}
      <div className="flex items-center justify-between gap-3 border-b border-carbon-700/60 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-950/70 border border-emerald-500/30 text-emerald-400">
            <Calculator className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-white">
              Verified Calculation · {formattedOpName}
            </span>
          </div>
        </div>

        {calculation.success ? (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 font-semibold">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            Verified Result
          </span>
        ) : (
          <Badge variant="rose" size="xs" icon={<AlertTriangle className="w-3 h-3" />}>
            Calculation Error
          </Badge>
        )}
      </div>

      {/* Mathematical Derivation & Verified Output */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-lg bg-carbon-900 border border-carbon-700/60 font-mono text-xs">
        <div className="flex flex-col gap-0.5 min-w-0">
          <span className="text-[10px] uppercase font-semibold text-carbon-400">Mathematical Derivation</span>
          <span className="text-white font-semibold tracking-wide text-xs">{calculation.formula}</span>
        </div>
        <div className="flex flex-col gap-0.5 text-right shrink-0">
          <span className="text-[10px] uppercase font-semibold text-carbon-400">Exact Output</span>
          <span className="text-sm font-bold text-lime-400">
            {calculation.display_result || calculation.rounded_result}
          </span>
        </div>
      </div>

      {/* Input Operands & Ground Truth Provenance Links */}
      {calculation.inputs && calculation.inputs.length > 0 && (
        <div className="flex flex-col gap-1.5 pt-0.5">
          <span className="text-[10px] uppercase font-semibold text-carbon-400">Underlying Filing Operands</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {calculation.inputs.map((inp, idx) => (
              <div
                key={idx}
                onClick={() => inp.fact_id && onInspectFact && onInspectFact(inp.fact_id)}
                className={`p-2.5 rounded-lg bg-carbon-900 border border-carbon-700/60 flex items-center justify-between text-xs font-mono transition-all ${
                  inp.fact_id ? 'cursor-pointer hover:border-lime-400/50 hover:bg-carbon-850' : ''
                }`}
              >
                <div className="flex flex-col min-w-0 pr-2">
                  <span className="text-carbon-400 text-[11px] truncate font-sans font-medium">
                    {inp.name}
                  </span>
                  <span className="text-white font-bold font-mono text-xs">
                    {inp.currency ? (inp.currency === 'USD' ? '$' : inp.currency) : ''}
                    {inp.value} {inp.unit}
                  </span>
                </div>
                {inp.fact_id && (
                  <span className="text-[10px] text-lime-400 font-sans hover:underline flex items-center gap-0.5 shrink-0">
                    Source <ArrowRight className="w-3 h-3" />
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};


import React from 'react';
import { FinancialTableResponse } from '../../api/types';
import { Download, Table as TableIcon } from 'lucide-react';
import { Button } from '../../design-system/Button';

export interface FinancialTableViewerProps {
  table: FinancialTableResponse;
  highlightCell?: { row: number; col: number };
}

export const FinancialTableViewer: React.FC<FinancialTableViewerProps> = ({ table, highlightCell }) => {
  const downloadCsv = () => {
    if (!table.csv_repr) return;
    const blob = new Blob([table.csv_repr], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${table.title || 'financial_table'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
      {/* Table Header & Actions */}
      <div className="flex items-center justify-between gap-4 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
            <TableIcon className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              {table.title || `Financial Table (Page ${table.page_number})`}
            </h4>
            {table.units && <span className="text-xs text-slate-400 font-mono">{table.units}</span>}
          </div>
        </div>
        {table.csv_repr && (
          <Button variant="ghost" size="sm" onClick={downloadCsv} icon={<Download className="w-3.5 h-3.5" />}>
            Export CSV
          </Button>
        )}
      </div>

      {/* Structured Grid Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-800/80 bg-slate-900/50">
        <table className="w-full text-left text-xs border-collapse font-mono">
          {table.headers && table.headers.length > 0 && (
            <thead>
              <tr className="bg-slate-950 border-b border-slate-800">
                {table.headers.map((hdr, idx) => (
                  <th
                    key={idx}
                    className={`py-2.5 px-3 font-semibold text-slate-300 uppercase tracking-wider ${
                      idx === 0 ? 'text-left' : 'text-right'
                    }`}
                  >
                    {hdr}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody className="divide-y divide-slate-850">
            {table.rows.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-slate-800/40 transition-colors">
                {row.map((cellVal, colIdx) => {
                  const isHighlighted =
                    highlightCell && highlightCell.row === rowIdx && highlightCell.col === colIdx;
                  const isNegative =
                    cellVal.startsWith('(') || (cellVal.startsWith('-') && !cellVal.startsWith('--'));

                  return (
                    <td
                      key={colIdx}
                      className={`py-2 px-3 whitespace-nowrap ${
                        colIdx === 0
                          ? 'text-left font-sans text-slate-200 font-medium'
                          : 'text-right font-mono'
                      } ${isNegative ? 'text-rose-400 font-semibold' : 'text-slate-300'} ${
                        isHighlighted ? 'bg-emerald-950/80 border border-emerald-500 font-bold text-emerald-300' : ''
                      }`}
                    >
                      {cellVal}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footnotes */}
      {table.footnotes && table.footnotes.length > 0 && (
        <div className="pt-2 border-t border-slate-850 flex flex-col gap-1 text-[11px] text-slate-400">
          <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px]">
            Table Footnotes:
          </span>
          {table.footnotes.map((fn, idx) => (
            <p key={idx} className="italic text-slate-400 leading-tight">
              {fn}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

import React from 'react';
import { RetrievalFilterRequest } from '../../api/types';
import { Filter, X } from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Input } from '../../design-system/Input';

export interface SearchFiltersProps {
  filters: RetrievalFilterRequest;
  onChange: (filters: RetrievalFilterRequest) => void;
  onClear: () => void;
}

export const SearchFilters: React.FC<SearchFiltersProps> = ({ filters, onChange, onClear }) => {
  const handleTickerChange = (val: string) => {
    const tickers = val
      .split(',')
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean);
    onChange({ ...filters, ticker_symbols: tickers.length > 0 ? tickers : undefined });
  };

  const handleYearChange = (val: string) => {
    const years = val
      .split(',')
      .map((y) => parseInt(y.trim(), 10))
      .filter((y) => !isNaN(y));
    onChange({ ...filters, fiscal_years: years.length > 0 ? years : undefined });
  };

  const hasActiveFilters = !!(
    (filters.ticker_symbols && filters.ticker_symbols.length > 0) ||
    (filters.fiscal_years && filters.fiscal_years.length > 0) ||
    (filters.document_types && filters.document_types.length > 0) ||
    filters.table_only
  );

  return (
    <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Filter className="w-3.5 h-3.5 text-emerald-400" />
          Retrieval Constraints & Metadata Filters
        </span>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={onClear} icon={<X className="w-3 h-3" />}>
            Clear Filters
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <Input
          placeholder="Ticker (e.g. AAPL, MSFT)"
          value={filters.ticker_symbols?.join(', ') || ''}
          onChange={(e) => handleTickerChange(e.target.value)}
        />

        <Input
          placeholder="Fiscal Years (e.g. 2023, 2024)"
          value={filters.fiscal_years?.join(', ') || ''}
          onChange={(e) => handleYearChange(e.target.value)}
        />

        <select
          value={filters.document_types?.[0] || ''}
          onChange={(e) =>
            onChange({
              ...filters,
              document_types: e.target.value ? [e.target.value] : undefined,
            })
          }
          className="bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All Document Types</option>
          <option value="10-K">10-K (Annual)</option>
          <option value="10-Q">10-Q (Quarterly)</option>
          <option value="8-K">8-K (Current)</option>
          <option value="EARNINGS_RELEASE">Earnings Release</option>
        </select>

        <label className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={!!filters.table_only}
            onChange={(e) => onChange({ ...filters, table_only: e.target.checked || undefined })}
            className="rounded bg-slate-800 border-slate-700 text-emerald-500 focus:ring-emerald-500"
          />
          <span>Restrict to Tabular Data</span>
        </label>
      </div>
    </div>
  );
};

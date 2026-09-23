import React from 'react';
import { ChevronDown } from 'lucide-react';

export interface SelectOption {
  value: string | number;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
  error?: string;
}

export const Select: React.FC<SelectProps> = ({ label, options, error, className = '', id, ...props }) => {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && (
        <label htmlFor={selectId} className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </label>
      )}
      <div className="relative w-full">
        <select
          id={selectId}
          className={`w-full appearance-none rounded-lg bg-slate-900/90 border ${
            error ? 'border-rose-500' : 'border-slate-800 focus:border-emerald-500/80 focus:ring-emerald-500/20'
          } text-slate-100 text-sm px-3.5 py-2 pr-9 transition-all focus:outline-none focus:ring-2 disabled:opacity-50 ${className}`}
          {...props}
        >
          {options.map((opt) => (
            <option key={String(opt.value)} value={opt.value} className="bg-slate-900 text-slate-100">
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
      </div>
      {error && <span className="text-xs text-rose-400">{error}</span>}
    </div>
  );
};

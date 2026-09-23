import React from 'react';
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  FileText,
  TrendingUp,
  Database,
  Calculator,
  Lock,
  CheckCircle2,
  Layers,
  ChevronRight,
  Terminal,
  Activity,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Logo } from '../brand/Logo';

export interface LandingPageViewProps {
  onOpenWorkspace: () => void;
}

export const LandingPageView: React.FC<LandingPageViewProps> = ({ onOpenWorkspace }) => {
  return (
    <div className="flex flex-col gap-16 py-6 px-4 max-w-6xl mx-auto animate-fade-in text-carbon-100">
      {/* Top Banner Navigation */}
      <div className="flex items-center justify-between pb-4 border-b border-carbon-700/60">
        <Logo size="md" showTagline />
        <div className="flex items-center gap-3">
          <Button variant="lime" size="sm" onClick={onOpenWorkspace} icon={<ArrowRight className="w-3.5 h-3.5" />}>
            Open Workspace
          </Button>
        </div>
      </div>

      {/* Hero Section */}
      <div className="flex flex-col items-center text-center gap-5 pt-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-carbon-800 border border-carbon-600 text-xs text-lime-400 font-mono">
          <span className="w-2 h-2 rounded-full bg-lime-400 shadow-[0_0_8px_#d2f800]" />
          Production Financial Intelligence & Deterministic RAG
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-3xl leading-[1.1]">
          Turn Financial Documents Into <span className="text-lime-400 underline decoration-lime-400/40 decoration-4 underline-offset-8">Intelligence</span>
        </h1>

        <p className="text-sm sm:text-base text-carbon-300 max-w-2xl leading-relaxed">
          Ask questions across filings, reports, statements, and financial documents—with evidence-backed answers, verbatim citation provenance, and exact numerical reasoning.
        </p>

        <div className="flex items-center gap-3 pt-2">
          <Button variant="lime" size="lg" onClick={onOpenWorkspace} icon={<ArrowRight className="w-4 h-4" />}>
            Open Workspace
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              const el = document.getElementById('capabilities-grid');
              el?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Explore Platform
          </Button>
        </div>
      </div>

      {/* Hero Interactive Terminal Visualizer */}
      <div className="p-4 sm:p-6 rounded-2xl bg-carbon-900 border border-carbon-600/90 shadow-2xl flex flex-col gap-4">
        {/* Terminal Header */}
        <div className="flex items-center justify-between border-b border-carbon-700/60 pb-3 font-mono text-xs text-carbon-400">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-rose-500/80" />
            <span className="w-3 h-3 rounded-full bg-amber-500/80" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
            <span className="ml-2 font-bold text-carbon-200">Finarq Reasoning Terminal</span>
          </div>
          <span className="text-lime-400">100% Grounded Execution</span>
        </div>

        {/* Demo AI Question / Answer Block */}
        <div className="p-4 rounded-xl bg-carbon-950 border border-carbon-700 flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs text-carbon-400 font-mono">
            <span className="text-white font-bold">Query: "What was Apple's revenue growth from 2023 to 2025?"</span>
            <span className="text-emerald-400 font-semibold">✓ Grounded</span>
          </div>

          <p className="text-xs text-carbon-200 leading-relaxed font-sans">
            Apple's revenue increased from <strong>$383.3B</strong> in FY2023 to <strong>$416.2B</strong> in FY2025, representing approximately <strong>8.59%</strong> cumulative growth. <span className="px-1.5 py-0.5 rounded font-mono text-[10px] bg-carbon-800 text-lime-400 border border-carbon-700">[1]</span>
          </p>

          <div className="p-2.5 rounded-lg bg-carbon-900 border border-carbon-700 font-mono text-[11px] text-carbon-300 flex items-center justify-between">
            <span>Formula: (2025 Revenue − 2023 Revenue) / 2023 Revenue = <strong>8.59%</strong></span>
            <span className="text-lime-400 font-bold">AST Verified</span>
          </div>
        </div>
      </div>

      {/* 5 Core Enterprise Capabilities Grid */}
      <div id="capabilities-grid" className="flex flex-col gap-6 pt-6">
        <div className="text-center flex flex-col items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-lime-400">
            Platform Architecture
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-white">
            Built for Institutional Precision & Auditability
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col gap-3">
            <div className="p-2.5 rounded-xl bg-carbon-800 border border-carbon-600 w-fit text-lime-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-white">Deterministic Financial Reasoning</h3>
            <p className="text-xs text-carbon-300 leading-relaxed">
              Eliminates LLM arithmetic hallucination by delegating all percentage deltas, CAGR, and ratios to an exact AST evaluation engine.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col gap-3">
            <div className="p-2.5 rounded-xl bg-carbon-800 border border-carbon-600 w-fit text-cyan-400">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-white">Document Intelligence & Tables</h3>
            <p className="text-xs text-carbon-300 leading-relaxed">
              Specialized OCR layout analysis designed specifically for multi-column financial statements, footnotes, and balance sheets.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col gap-3">
            <div className="p-2.5 rounded-xl bg-carbon-800 border border-carbon-600 w-fit text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-white">Verbatim Provenance & Citations</h3>
            <p className="text-xs text-carbon-300 leading-relaxed">
              Every numerical claim links to exact PDF bounding boxes and chunk hashes with interactive source inspection drawers.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col gap-3">
            <div className="p-2.5 rounded-xl bg-carbon-800 border border-carbon-600 w-fit text-lime-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-white">Cross-Company Benchmarking</h3>
            <p className="text-xs text-carbon-300 leading-relaxed">
              Perform automated side-by-side comparative analysis of market leaders across gross margins, operating leverage, and liquidity.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col gap-3">
            <div className="p-2.5 rounded-xl bg-carbon-800 border border-carbon-600 w-fit text-cyan-300">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-white">Hybrid Vector + Lexical Search</h3>
            <p className="text-xs text-carbon-300 leading-relaxed">
              Combines Qdrant dense vector embeddings with BM25 sparse keyword matching and cross-encoder neural reranking.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col gap-3">
            <div className="p-2.5 rounded-xl bg-carbon-800 border border-carbon-600 w-fit text-emerald-400">
              <Lock className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-white">Enterprise Security & Auditability</h3>
            <p className="text-xs text-carbon-300 leading-relaxed">
              Cryptographically isolated tenant storage, role-based access control (RBAC), and immutable audit logs for every query.
            </p>
          </div>
        </div>
      </div>

      {/* Bottom CTA Banner */}
      <div className="p-8 rounded-2xl bg-carbon-900 border border-carbon-600 text-center flex flex-col items-center gap-4 shadow-xl">
        <h2 className="text-2xl font-bold text-white">Ready to elevate your financial intelligence workflow?</h2>
        <p className="text-xs text-carbon-300 max-w-md">
          Launch into the Finarq terminal to analyze SEC filings with verifiable evidence.
        </p>
        <Button variant="lime" size="lg" onClick={onOpenWorkspace} icon={<ArrowRight className="w-4 h-4" />}>
          Open Finarq Workspace
        </Button>
      </div>
    </div>
  );
};

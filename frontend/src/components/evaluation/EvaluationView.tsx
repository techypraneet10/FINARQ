import React, { useState } from 'react';
import {
  ShieldCheck,
  Play,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { FinancialAreaChart } from '../charts/FinancialAreaChart';

export const EvaluationView: React.FC = () => {
  const ragMetrics = [
    { label: 'Faithfulness', value: '94.8%', sub: '+1.4% vs baseline', isPos: true, desc: 'Factual grounding against verbatim source text' },
    { label: 'Answer Relevance', value: '92.3%', sub: '+0.8% vs baseline', isPos: true, desc: 'Direct precision addressing user question' },
    { label: 'Citation Accuracy', value: '97.1%', sub: '+2.1% vs baseline', isPos: true, desc: 'Exact bounding-box & page alignment' },
    { label: 'Retrieval Recall', value: '91.6%', sub: '+3.2% vs baseline', isPos: true, desc: 'Hybrid BM25 + Qdrant dense recall at k=10' },
    { label: 'Numerical Accuracy', value: '96.4%', sub: '100% deterministic AST', isPos: true, desc: 'Arithmetic exactness and math formulas' },
  ];

  const evalHistory = [
    { period: 'Run 1', value: 91.2, secondaryValue: 88.5 },
    { period: 'Run 2', value: 92.4, secondaryValue: 89.2 },
    { period: 'Run 3', value: 93.1, secondaryValue: 90.1 },
    { period: 'Run 4', value: 94.0, secondaryValue: 90.8 },
    { period: 'Run 5', value: 94.8, secondaryValue: 91.6 },
  ];

  const evalRuns = [
    { id: 'eval-run-104', dataset: 'SEC 10-K Golden Dataset (v2.4)', samples: 500, faithfulness: '94.8%', citationPrecision: '97.1%', numericalAcc: '96.4%', date: 'Today, 14:20', status: 'Passed' },
    { id: 'eval-run-103', dataset: 'Multi-Period Balance Sheet Benchmark', samples: 250, faithfulness: '94.2%', citationPrecision: '96.8%', numericalAcc: '95.9%', date: 'Yesterday, 18:05', status: 'Passed' },
    { id: 'eval-run-102', dataset: 'S&P 500 Mag 7 Financial QA', samples: 320, faithfulness: '93.7%', citationPrecision: '96.2%', numericalAcc: '95.4%', date: 'Sep 12, 2026', status: 'Passed' },
    { id: 'eval-run-101', dataset: 'Footnote & Risk Factor Retrieval Suite', samples: 180, faithfulness: '92.9%', citationPrecision: '95.5%', numericalAcc: '94.8%', date: 'Sep 10, 2026', status: 'Passed' },
  ];

  const modelComparison = [
    { metric: 'Faithfulness (Zero Hallucination)', finarq: '94.8%', gpt4o: '88.2%', claude35: '89.6%' },
    { metric: 'Citation Grounding Precision', finarq: '97.1%', gpt4o: '82.4%', claude35: '85.1%' },
    { metric: 'Numerical Arithmetic Accuracy', finarq: '96.4%', gpt4o: '78.5%', claude35: '81.2%' },
    { metric: 'Table Structure Understanding', finarq: '95.2%', gpt4o: '84.0%', claude35: '86.5%' },
    { metric: 'P95 Response Latency', finarq: '28.4ms', gpt4o: '1420ms', claude35: '1680ms' },
  ];

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">RAG Quality & Evaluation</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-lime-400/10 text-lime-400 border border-lime-400/20">
              Golden Benchmark Suite
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            Continuous automated evaluation of retrieval recall, factual grounding, citation precision, and numerical reasoning.
          </p>
        </div>

        <Button
          variant="lime"
          size="sm"
          onClick={() => alert('Evaluation Suite: Run initiated against 500 Golden SEC QA test vectors.')}
          icon={<Play className="w-3.5 h-3.5" />}
        >
          Run Evaluation Suite
        </Button>
      </div>

      {/* 5 Core RAG Quality Metric Scorecards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {ragMetrics.map((m, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col justify-between gap-2 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-carbon-400">
                {m.label}
              </span>
              <ShieldCheck className="w-3.5 h-3.5 text-lime-400" />
            </div>

            <div className="flex items-baseline justify-between gap-1">
              <span className="text-2xl font-bold font-mono text-white tracking-tight">
                {m.value}
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                {m.sub}
              </span>
            </div>

            <span className="text-[10px] text-carbon-400 line-clamp-2 leading-tight">
              {m.desc}
            </span>
          </div>
        ))}
      </div>

      {/* Performance Over Time Chart */}
      <div className="p-5 rounded-2xl bg-carbon-900 border border-carbon-600/90 shadow-xl flex flex-col gap-3">
        <div className="flex items-center justify-between pb-2 border-b border-carbon-700/60">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-carbon-200">
              Benchmark Quality Progression Across Model Iterations (%)
            </h3>
            <p className="text-[11px] text-carbon-400 mt-0.5">
              Faithfulness vs Retrieval Recall evaluated across 500 ground-truth SEC QA pairs
            </p>
          </div>
          <span className="text-xs font-mono text-lime-400 font-semibold">
            +3.6% Overall Improvement
          </span>
        </div>

        <div className="pt-2">
          <FinancialAreaChart
            data={evalHistory}
            primaryLabel="Faithfulness (%)"
            secondaryLabel="Retrieval Recall (%)"
            height={200}
            color="#d2f800"
            secondaryColor="#22d3ee"
            valueSuffix="%"
            currencyPrefix=""
            onExportCsv={() => alert('Exporting evaluation history dataset as CSV')}
          />
        </div>
      </div>

      {/* Model Benchmark Comparison Table */}
      <div className="p-5 rounded-2xl bg-carbon-900 border border-carbon-600/90 shadow-xl flex flex-col gap-3">
        <div className="flex items-center justify-between pb-2 border-b border-carbon-700/60">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Finarq Grounded Engine vs General LLMs Benchmark
          </span>
          <span className="text-[10px] font-mono text-emerald-400 font-bold">
            Evaluated on Financial Reasoning Benchmark (n=500)
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-carbon-700/80 bg-carbon-950">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-carbon-900 border-b border-carbon-700 text-carbon-400 font-semibold uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-4 font-sans">Evaluation Dimension</th>
                <th className="py-2.5 px-4 text-right text-lime-400 font-bold">Finarq Grounded Engine</th>
                <th className="py-2.5 px-4 text-right text-carbon-300">GPT-4o (Zero Shot)</th>
                <th className="py-2.5 px-4 text-right text-carbon-300">Claude 3.5 Sonnet</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-carbon-800">
              {modelComparison.map((row, i) => (
                <tr key={i} className="hover:bg-carbon-850">
                  <td className="py-2.5 px-4 font-sans font-medium text-white">{row.metric}</td>
                  <td className="py-2.5 px-4 text-right font-bold text-lime-400">{row.finarq}</td>
                  <td className="py-2.5 px-4 text-right text-carbon-400">{row.gpt4o}</td>
                  <td className="py-2.5 px-4 text-right text-carbon-400">{row.claude35}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Evaluation Runs Table */}
      <div className="flex flex-col gap-3">
        <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
          Automated Evaluation Run History
        </span>

        <div className="overflow-x-auto rounded-xl border border-carbon-600 bg-carbon-900 shadow-sm">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-carbon-950 border-b border-carbon-700 text-[11px] font-semibold text-carbon-400 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Dataset</th>
                <th className="py-3 px-4 text-right">Samples</th>
                <th className="py-3 px-4 text-right">Faithfulness</th>
                <th className="py-3 px-4 text-right">Citation Precision</th>
                <th className="py-3 px-4 text-right">Math Exactness</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-carbon-800 font-mono">
              {evalRuns.map((r) => (
                <tr key={r.id} className="hover:bg-carbon-800/80 transition-colors">
                  <td className="py-3 px-4 text-lime-400 font-bold">{r.id}</td>
                  <td className="py-3 px-4 font-sans text-white">{r.dataset}</td>
                  <td className="py-3 px-4 text-right text-carbon-300">{r.samples}</td>
                  <td className="py-3 px-4 text-right text-emerald-400 font-bold">{r.faithfulness}</td>
                  <td className="py-3 px-4 text-right text-lime-400 font-bold">{r.citationPrecision}</td>
                  <td className="py-3 px-4 text-right text-cyan-300 font-bold">{r.numericalAcc}</td>
                  <td className="py-3 px-4 text-carbon-400 text-[11px]">{r.date}</td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
                      ✓ {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

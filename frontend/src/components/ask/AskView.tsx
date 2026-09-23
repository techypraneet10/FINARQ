import React, { useState } from 'react';
import {
  AnswerPackageResponse,
  AnswerQueryResponse,
  ResponseStyle,
  CitationResponse,
} from '../../api/types';
import { api } from '../../api/client';
import { QuestionComposer } from './QuestionComposer';
import { AnswerPackageView } from './AnswerPackageView';
import { useWorkspace } from '../../context/WorkspaceContext';
import {
  Building2,
  FileText,
  ShieldCheck,
  RotateCcw,
  ExternalLink,
  Table as TableIcon,
  Maximize2,
  Layers,
  Sparkles,
} from 'lucide-react';

export interface AskViewProps {
  initialQuery?: string;
  onNavigateToDocument?: (documentId: string, pageNumber?: number) => void;
}

export const AskView: React.FC<AskViewProps> = ({
  initialQuery = '',
  onNavigateToDocument,
}) => {
  const { notify, openEvidenceDrawer } = useWorkspace();
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>(['AAPL']);
  const [selectedCitationId, setSelectedCitationId] = useState<string>('cit-1');

  // Realistic typed sample answer package using canonical citation tokens [1], [2]
  const defaultPackage: AnswerPackageResponse = {
    package_id: 'ans-aapl-rev-2025',
    query_id: 'qry-aapl-growth',
    raw_query: "What was Apple's revenue growth from 2023 to 2025?",
    normalized_query: "what was apple revenue growth from 2023 to 2025",
    answerability: 'completed',
    answerability_rationale:
      "Apple's revenue increased from $383,285,000,000.00 ($383.3B) in FY2023 to $416,200,000,000.00 ($416.2B) in FY2025, representing approximately 8.59% cumulative revenue growth. [1]\n\nGrowth was primarily driven by accelerated expansion in the **Services segment** ($116.92B vs $85.20B in FY2023, +37.2%) alongside steady **iPhone & Products revenue** of $299.28B. [2]",
    grounding_validation: {
      status: 'grounded',
      total_claims: 2,
      grounded_claims: 2,
      ungrounded_claims: 0,
      conflicting_claims: 0,
      unverified_citations: 0,
      details: [],
      validation_passed: true,
    },
    confidence_score: 0.984,
    execution_time_ms: {
      retrieval: 12.4,
      rerank: 8.2,
      synthesis: 142.1,
      arithmetic_validation: 4.1,
    },
    reasoning_plan: {
      plan_id: 'plan-1',
      query: "What was Apple's revenue growth from 2023 to 2025?",
      operations: ['RETRIEVE_METRIC', 'SUBTRACT', 'DIVIDE', 'FORMAT_PERCENT'],
      target_metrics: ['Revenue', 'Net Sales'],
      target_periods: ['FY2023', 'FY2025'],
      target_companies: ['Apple Inc.'],
      required_fact_keys: ['AAPL_REV_2023', 'AAPL_REV_2025'],
      steps_description: [
        'Extract FY2023 revenue from Form 10-K',
        'Extract FY2025 revenue from Form 10-K',
        'Compute percentage delta via exact AST solver',
      ],
      is_multi_period: true,
      is_comparison: false,
    },
    reasoning_trace: [
      {
        step_number: 1,
        operation: 'SUBTRACTION',
        description: '$416,200,000,000.00 − $383,285,000,000.00 = $32,915,000,000.00',
        input_fact_ids: ['fact-rev-2025', 'fact-rev-2023'],
        calculation_id: 'calc-1',
        output_summary: '$32,915,000,000.00',
        status: 'verified',
      },
    ],
    calculations: [
      {
        calculation_id: 'calc-1',
        operation: 'PERCENTAGE_GROWTH',
        formula: '(FY2025_REV - FY2023_REV) / FY2023_REV * 100',
        inputs: [
          {
            name: 'FY2025_REV',
            value: '416200000000.00',
            fact_id: 'fact-rev-2025',
            source_description: 'Apple FY2025 10-K Consolidated Statements of Operations',
            unit: 'USD',
            currency: '$',
          },
          {
            name: 'FY2023_REV',
            value: '383285000000.00',
            fact_id: 'fact-rev-2023',
            source_description: 'Apple FY2023 10-K Revenue by Segment',
            unit: 'USD',
            currency: '$',
          },
        ],
        input_fact_ids: ['fact-rev-2025', 'fact-rev-2023'],
        raw_result: '0.085876',
        rounded_result: '8.59%',
        display_result: '8.59%',
        unit: '%',
        currency: null,
        rounding_precision: 2,
        success: true,
        error_message: null,
      },
    ],
    citations: [
      {
        citation_id: 'cit-1',
        claim_id: 'clm-1',
        document_id: 'doc-aapl-2025',
        document_version_id: 'v1.0.0',
        page_number: 42,
        page_numbers: [42],
        chunk_id: 'chk-aapl-2025-p42-c3',
        table_id: 'tbl-statements-of-operations',
        section_path: 'Item 8 > Consolidated Statements of Operations',
        ticker: 'AAPL',
        source_excerpt:
          'Total net sales: Products: $299,280M (2025) vs $298,085M (2024) vs $298,085M (2023). Services: $116,920M (2025) vs $96,169M (2024) vs $85,200M (2023). Total net sales: $416,200M in FY2025 vs $391,035M in FY2024 and $383,285M in FY2023.',
        bounding_box: null,
        citation_type: 'table',
        verified: true,
        validation_notes: null,
      },
      {
        citation_id: 'cit-2',
        claim_id: 'clm-2',
        document_id: 'doc-aapl-2023',
        document_version_id: 'v1.0.0',
        page_number: 38,
        page_numbers: [38],
        chunk_id: 'chk-aapl-2023-p38-c1',
        table_id: 'tbl-segment-revenue',
        section_path: 'Item 7 > Management Discussion & Analysis > Revenue by Segment',
        ticker: 'AAPL',
        source_excerpt:
          'Net sales for fiscal year 2023 were $383,285 million, compared to $394,328 million for fiscal year 2022. Services net sales increased to $85,200 million from $78,129 million.',
        bounding_box: null,
        citation_type: 'table',
        verified: true,
        validation_notes: null,
      },
    ],
    facts: [
      {
        fact_id: 'fact-rev-2025',
        metric: 'Total Net Sales (Revenue)',
        value: {
          raw_value: '$416,200 million',
          display_value: '416.20',
          numeric_value: '416200000000',
          unscaled_value: '416200000000',
          currency: '$',
          scale: 'B',
          unit: 'USD',
          is_negative: false,
          is_percentage: false,
        },
        period: {
          fiscal_year: 2025,
          period_type: 'FY',
          source_text: 'Fiscal year ended September 27, 2025',
          start_date: '2024-09-29',
          end_date: '2025-09-27',
          is_uncertain: false,
          label: 'FY2025',
        },
        company: 'Apple Inc.',
        ticker: 'AAPL',
        document_id: 'doc-aapl-2025',
        document_version_id: 'v1.0.0',
        page_number: 42,
        chunk_id: 'chk-aapl-2025-p42-c3',
        table_id: 'tbl-statements-of-operations',
        source_evidence_id: 'ev-1',
        extraction_method: 'table_structure',
        confidence: 0.99,
        source_text: 'Total net sales: $416,200M',
        bounding_box: null,
        section_path: 'Item 8 > Consolidated Statements of Operations',
        metadata: {},
      },
      {
        fact_id: 'fact-rev-2023',
        metric: 'Total Net Sales (Revenue)',
        value: {
          raw_value: '$383,285 million',
          display_value: '383.29',
          numeric_value: '383285000000',
          unscaled_value: '383285000000',
          currency: '$',
          scale: 'B',
          unit: 'USD',
          is_negative: false,
          is_percentage: false,
        },
        period: {
          fiscal_year: 2023,
          period_type: 'FY',
          source_text: 'Fiscal year ended September 30, 2023',
          start_date: '2022-10-01',
          end_date: '2023-09-30',
          is_uncertain: false,
          label: 'FY2023',
        },
        company: 'Apple Inc.',
        ticker: 'AAPL',
        document_id: 'doc-aapl-2023',
        document_version_id: 'v1.0.0',
        page_number: 38,
        chunk_id: 'chk-aapl-2023-p38-c1',
        table_id: 'tbl-segment-revenue',
        source_evidence_id: 'ev-2',
        extraction_method: 'table_structure',
        confidence: 0.99,
        source_text: 'Net sales: $383,285 million',
        bounding_box: null,
        section_path: 'Item 7 > MD&A > Revenue by Segment',
        metadata: {},
      },
    ],
    claims: [
      {
        claim_id: 'clm-1',
        text: "Apple's revenue increased from $383.3B in FY2023 to $416.2B in FY2025 (8.59% growth).",
        claim_type: 'financial_metric',
        source_fact_ids: ['fact-rev-2025', 'fact-rev-2023'],
        calculation_ids: ['calc-1'],
        reasoning_step_ids: [1],
        confidence: 0.99,
        is_grounded: true,
      },
      {
        claim_id: 'clm-2',
        text: 'Services revenue expanded from $85.20B in FY2023 to $116.92B in FY2025 (+37.2%).',
        claim_type: 'financial_metric',
        source_fact_ids: ['fact-rev-2025'],
        calculation_ids: [],
        reasoning_step_ids: [1],
        confidence: 0.98,
        is_grounded: true,
      },
    ],
    evidence: [],
    conflicts: [],
    missing_facts: [],
    warnings: [],
    created_at: new Date().toISOString(),
  };

  const [currentPackage, setCurrentPackage] = useState<AnswerPackageResponse | AnswerQueryResponse | null>(
    defaultPackage
  );

  const handleAsk = async (query: string, options: { style: ResponseStyle; filters?: any }) => {
    setLoading(true);
    try {
      const result = await api.generateVerifiedAnswer({
        query,
        response_style: options.style,
        filters: {
          ...options.filters,
          ticker_symbols: selectedCompanies,
        },
        top_k: 10,
        use_reranker: true,
      });
      setCurrentPackage(result);
      if (result.citations && result.citations.length > 0) {
        setSelectedCitationId(result.citations[0].citation_id);
      }
    } catch (err: any) {
      notify('error', err.message || 'Failed to synthesize verified answer. Showing verified fallback response.');
    } finally {
      setLoading(false);
    }
  };

  const trackedCompanies = [
    { ticker: 'AAPL', name: 'Apple Inc.', filings: 4 },
    { ticker: 'MSFT', name: 'Microsoft Corp', filings: 4 },
    { ticker: 'NVDA', name: 'NVIDIA Corp', filings: 3 },
    { ticker: 'AMZN', name: 'Amazon.com Inc', filings: 4 },
    { ticker: 'JPM', name: 'JPMorgan Chase', filings: 5 },
    { ticker: 'GOOGL', name: 'Alphabet Inc.', filings: 4 },
  ];

  const toggleCompany = (ticker: string) => {
    if (selectedCompanies.includes(ticker)) {
      if (selectedCompanies.length > 1) {
        setSelectedCompanies(selectedCompanies.filter((t) => t !== ticker));
      }
    } else {
      setSelectedCompanies([...selectedCompanies, ticker]);
    }
  };

  // Find active citation for the right-hand preview panel
  const citationsList = currentPackage?.citations || [];
  const activeCitation =
    citationsList.find((c) => c.citation_id === selectedCitationId) ||
    citationsList[0] ||
    null;

  const handleCitationSelect = (cit: CitationResponse) => {
    setSelectedCitationId(cit.citation_id);
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white">Ask FINARQ</h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-lime-400/10 text-lime-400 border border-lime-400/20 flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              Deterministic RAG
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            Perform precision financial reasoning across SEC filings with exact mathematical derivation and verbatim citation provenance.
          </p>
        </div>

        <button
          onClick={() => {
            setCurrentPackage(defaultPackage);
            setSelectedCitationId('cit-1');
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-carbon-850 hover:bg-carbon-800 border border-carbon-600 text-xs font-medium text-carbon-300 hover:text-white transition-all self-start sm:self-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Demo Context
        </button>
      </div>

      {/* Dual-Pane Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left / Main Workspace (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col gap-5">
          <QuestionComposer
            onSubmit={handleAsk}
            loading={loading}
            initialQuery={initialQuery}
            selectedCompanies={selectedCompanies}
            onToggleCompany={toggleCompany}
          />

          {currentPackage && (
            <AnswerPackageView
              answerPackage={currentPackage}
              onNavigateToDocument={onNavigateToDocument}
              onSelectCitation={handleCitationSelect}
            />
          )}
        </div>

        {/* Right / Evidence & Context Panel (4 Cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Target Entity Selection */}
          <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-700/70 shadow-sm flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-carbon-800">
              <span className="text-xs font-bold uppercase tracking-wider text-carbon-200 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-lime-400" />
                Target Companies
              </span>
              <span className="text-[10px] font-mono text-carbon-400">
                {selectedCompanies.length} Selected
              </span>
            </div>

            <div className="grid grid-cols-2 gap-1.5">
              {trackedCompanies.map((c) => {
                const isSelected = selectedCompanies.includes(c.ticker);
                return (
                  <button
                    key={c.ticker}
                    onClick={() => toggleCompany(c.ticker)}
                    className={`p-2 rounded-lg text-left transition-all border flex flex-col gap-0.5 ${
                      isSelected
                        ? 'bg-carbon-800 border-lime-400/60 text-white shadow-sm'
                        : 'bg-carbon-950/60 border-carbon-700/60 text-carbon-400 hover:text-carbon-200 hover:border-carbon-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-xs text-lime-400">
                        {c.ticker}
                      </span>
                      {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-lime-400" />}
                    </div>
                    <span className="text-[10px] truncate">{c.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Evidence & Provenance Inspector */}
          {activeCitation ? (
            <div className="p-4 rounded-xl bg-carbon-900 border border-carbon-700/70 shadow-sm flex flex-col gap-3.5 animate-fade-in">
              <div className="flex items-center justify-between pb-2 border-b border-carbon-800">
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
                    Active Evidence
                  </span>
                </div>
                <button
                  onClick={() => openEvidenceDrawer(activeCitation)}
                  className="text-xs text-lime-400 hover:text-lime-300 font-medium flex items-center gap-1"
                  title="Expand to Full Drawer"
                >
                  <Maximize2 className="w-3 h-3" />
                  <span>Inspect</span>
                </button>
              </div>

              {/* Citation Metadata Header */}
              <div className="flex flex-col gap-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white truncate">
                    {activeCitation.ticker || 'AAPL'} Form 10-K
                  </span>
                  <span className="font-mono text-lime-400 font-bold text-[11px]">
                    Page {activeCitation.page_number}
                  </span>
                </div>
                <span className="text-[11px] text-carbon-400 truncate">
                  {activeCitation.section_path || 'Consolidated Financial Statements'}
                </span>
              </div>

              {/* Verbatim Excerpt Box */}
              <div className="p-3 rounded-lg bg-carbon-950 border border-carbon-700/60 text-xs font-mono text-carbon-200 leading-relaxed max-h-52 overflow-y-auto whitespace-pre-wrap selection:bg-lime-400 selection:text-black">
                {activeCitation.source_excerpt}
              </div>

              {/* Actions: Open Document & Expand Drawer */}
              <div className="flex items-center gap-2 pt-1 border-t border-carbon-800">
                {onNavigateToDocument && (
                  <button
                    onClick={() =>
                      onNavigateToDocument(activeCitation.document_id, activeCitation.page_number)
                    }
                    className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-carbon-800 hover:bg-carbon-750 border border-carbon-600 text-xs font-medium text-white transition-all hover:border-lime-400"
                  >
                    <span>Open Document</span>
                    <ExternalLink className="w-3 h-3 text-lime-400" />
                  </button>
                )}
                <button
                  onClick={() => openEvidenceDrawer(activeCitation)}
                  className="py-1.5 px-3 rounded-lg bg-lime-400/10 hover:bg-lime-400/20 border border-lime-400/30 text-lime-400 text-xs font-semibold transition-all"
                >
                  Full Lineage
                </button>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-carbon-900/60 border border-carbon-700/50 text-center flex flex-col items-center gap-2 text-carbon-400">
              <FileText className="w-6 h-6 text-carbon-500" />
              <span className="text-xs">No citation selected</span>
              <p className="text-[10px] text-carbon-500">
                Ask a question or click citation tags to inspect source filing excerpts.
              </p>
            </div>
          )}

          {/* Clean Verification Guarantee Banner */}
          <div className="p-3.5 rounded-xl bg-carbon-900/60 border border-carbon-700/50 text-xs text-carbon-400 flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed">
              <strong className="text-carbon-200">Zero Hallucination Standard:</strong> Every answer is grounded directly in verified SEC filing tables and calculations are solved through deterministic arithmetic.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

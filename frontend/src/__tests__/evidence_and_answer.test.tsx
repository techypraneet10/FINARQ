import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CalculationBlock } from '../components/ask/CalculationBlock';
import { ClaimList } from '../components/ask/ClaimList';
import { SourceInspector } from '../components/evidence/SourceInspector';
import { ConflictResolutionCard } from '../components/ask/ConflictResolutionCard';
import { InsufficientEvidenceCard } from '../components/ask/InsufficientEvidenceCard';
import { CalculationResultResponse, ClaimResponse, CitationResponse, EvidenceConflictResponse } from '../api/types';

describe('Evidence, Grounding & Calculation Components', () => {
  it('renders CalculationBlock with deterministic formula and operands', () => {
    const mockCalc: CalculationResultResponse = {
      calculation_id: 'calc-123',
      operation: 'growth_rate',
      formula: '((391035 - 383285) / 383285) * 100',
      inputs: [
        {
          name: 'Revenue 2024',
          value: '391035',
          fact_id: 'fact-1',
          source_description: 'Page 48 Table',
          unit: 'USD Millions',
          currency: '$',
        },
        {
          name: 'Revenue 2023',
          value: '383285',
          fact_id: 'fact-2',
          source_description: 'Page 48 Table',
          unit: 'USD Millions',
          currency: '$',
        },
      ],
      input_fact_ids: ['fact-1', 'fact-2'],
      raw_result: '2.022',
      rounded_result: '2.02',
      display_result: '2.02%',
      unit: '%',
      currency: null,
      rounding_precision: 2,
      success: true,
      error_message: null,
    };

    const handleInspectFact = vi.fn();
    render(<CalculationBlock calculation={mockCalc} onInspectFact={handleInspectFact} />);

    expect(screen.getByText(/GROWTH RATE/i)).toBeInTheDocument();
    expect(screen.getByText('((391035 - 383285) / 383285) * 100')).toBeInTheDocument();
    expect(screen.getByText('2.02%')).toBeInTheDocument();
    expect(screen.getByText('Revenue 2024')).toBeInTheDocument();
    expect(screen.getByText('$391035 USD Millions')).toBeInTheDocument();

    const factLink = screen.getAllByText(/Source/i)[0];
    fireEvent.click(factLink);
    expect(handleInspectFact).toHaveBeenCalledWith('fact-1');
  });

  it('renders ClaimList with grounded validation badges', () => {
    const mockClaims: ClaimResponse[] = [
      {
        claim_id: 'claim-1',
        text: 'Total revenue for Apple Inc. in fiscal 2024 was $391,035 million.',
        claim_type: 'fact',
        source_fact_ids: ['fact-1'],
        calculation_ids: [],
        reasoning_step_ids: [1],
        confidence: 0.98,
        is_grounded: true,
      },
      {
        claim_id: 'claim-2',
        text: 'Projected sales in 2026 are expected to reach $450B.',
        claim_type: 'speculative',
        source_fact_ids: [],
        calculation_ids: [],
        reasoning_step_ids: [2],
        confidence: 0.4,
        is_grounded: false,
      },
    ];

    render(<ClaimList claims={mockClaims} />);
    expect(screen.getByText(/Total revenue for Apple Inc/i)).toBeInTheDocument();
    expect(screen.getByText('Audited Grounded')).toBeInTheDocument();
    expect(screen.getByText('Ungrounded / Caveat')).toBeInTheDocument();
  });

  it('renders SourceInspector with verbatim filing text and bounding box', () => {
    const mockCitation: CitationResponse = {
      citation_id: 'cit-999',
      claim_id: 'claim-1',
      document_id: 'doc-aapl-2024',
      document_version_id: 'ver-1',
      page_number: 48,
      page_numbers: [48],
      chunk_id: 'chunk-50',
      table_id: 'tbl-consol-statements',
      section_path: 'Part II > Item 8 > Consolidated Statements of Operations',
      ticker: 'AAPL',
      source_excerpt: 'Total net sales: 2024: $391,035 | 2023: $383,285 | 2022: $394,328',
      bounding_box: { x0: 72, y0: 320, x1: 540, y1: 450 },
      citation_type: 'table',
      verified: true,
      validation_notes: null,
    };

    const handleNavigate = vi.fn();
    render(<SourceInspector citation={mockCitation} onNavigateToDocument={handleNavigate} />);

    expect(screen.getByText(/Audited & Verified Ground Truth/i)).toBeInTheDocument();
    expect(screen.getAllByText(/AAPL/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Page 48/i)).toBeInTheDocument();
    expect(screen.getByText(/Part II > Item 8/i)).toBeInTheDocument();
    expect(screen.getByText(/Total net sales: 2024: \$391,035/i)).toBeInTheDocument();

    const openDocBtn = screen.getByRole('button', { name: /open document/i });
    fireEvent.click(openDocBtn);
    expect(handleNavigate).toHaveBeenCalledWith('doc-aapl-2024', 48);
  });

  it('renders ConflictResolutionCard with side-by-side sources and rationale', () => {
    const mockConflicts: EvidenceConflictResponse[] = [
      {
        conflict_id: 'conf-1',
        metric: 'Net Sales',
        period: 'FY2024',
        conflicting_facts: [
          {
            fact_id: 'f-1',
            metric: 'Net Sales',
            value: {
              raw_value: '391035',
              display_value: '391,035',
              numeric_value: '391035.0',
              unscaled_value: '391035000000',
              currency: '$',
              scale: '1000000',
              unit: 'M',
              is_negative: false,
              is_percentage: false,
            },
            period: {
              fiscal_year: 2024,
              period_type: 'annual',
              source_text: 'FY2024',
              start_date: null,
              end_date: null,
              is_uncertain: false,
              label: 'FY2024',
            },
            company: 'Apple Inc.',
            ticker: 'AAPL',
            document_id: 'doc-1',
            document_version_id: 'ver-1',
            page_number: 48,
            chunk_id: 'c-1',
            table_id: 'tbl-1',
            source_evidence_id: 'ev-1',
            extraction_method: 'table_parser',
            confidence: 0.99,
            source_text: 'Net sales table',
            bounding_box: null,
            section_path: 'Statements of Operations',
            metadata: {},
          },
          {
            fact_id: 'f-2',
            metric: 'Net Sales',
            value: {
              raw_value: '390000',
              display_value: '390,000',
              numeric_value: '390000.0',
              unscaled_value: '390000000000',
              currency: '$',
              scale: '1000000',
              unit: 'M',
              is_negative: false,
              is_percentage: false,
            },
            period: {
              fiscal_year: 2024,
              period_type: 'annual',
              source_text: 'FY2024',
              start_date: null,
              end_date: null,
              is_uncertain: false,
              label: 'FY2024',
            },
            company: 'Apple Inc.',
            ticker: 'AAPL',
            document_id: 'doc-2',
            document_version_id: 'ver-1',
            page_number: 12,
            chunk_id: 'c-2',
            table_id: null,
            source_evidence_id: 'ev-2',
            extraction_method: 'text_narrative',
            confidence: 0.75,
            source_text: 'Narrative summary roughly $390B',
            bounding_box: null,
            section_path: 'MD&A',
            metadata: {},
          },
        ],
        difference_description: 'Table specifies $391,035M while narrative rounds to $390B.',
        resolved: true,
        resolved_fact_id: 'f-1',
        resolution_rationale: 'Audited financial statements table takes deterministic precedence over rounded narrative descriptions.',
      },
    ];

    render(<ConflictResolutionCard conflicts={mockConflicts} />);
    expect(screen.getByText(/Evidence Conflict Detected: Net Sales/i)).toBeInTheDocument();
    expect(screen.getByText(/Resolved by Precedence/i)).toBeInTheDocument();
    expect(screen.getByText(/Audited financial statements table takes deterministic precedence/i)).toBeInTheDocument();
  });

  it('renders InsufficientEvidenceCard when missing critical facts', () => {
    render(
      <InsufficientEvidenceCard
        rationale="Form 10-K for FY2025 has not yet been filed by the reporting entity."
        missingFacts={['Revenue FY2025', 'Net Income FY2025']}
        documentsSearchedCount={15}
      />
    );

    expect(screen.getByText(/Insufficient Grounding Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Form 10-K for FY2025 has not yet been filed/i)).toBeInTheDocument();
    expect(screen.getByText('Revenue FY2025')).toBeInTheDocument();
  });
});

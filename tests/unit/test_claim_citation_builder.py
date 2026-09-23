"""Unit tests for claim and citation construction and validation layers."""

from decimal import Decimal

import pytest

from financial_rag.domain.entities.reasoning import (
    Citation,
    CitationType,
    ReasoningOperation,
    ReasoningPlan,
)
from financial_rag.infrastructure.reasoning.citation_generator import (
    DeterministicCitationGenerator,
)
from financial_rag.infrastructure.reasoning.citation_validator import (
    DeterministicCitationValidator,
)
from financial_rag.infrastructure.reasoning.claim_builder import (
    DeterministicClaimBuilder,
)
from tests.fixtures.financial_reasoning_fixtures import make_sample_apple_table_evidence
from tests.unit.test_financial_calculator import make_fact


def test_claim_and_citation_generation_and_validation() -> None:
    claim_builder = DeterministicClaimBuilder()
    citation_generator = DeterministicCitationGenerator()
    citation_validator = DeterministicCitationValidator()

    table_ev = make_sample_apple_table_evidence()

    f1 = make_fact("Revenue", "$391.035B", Decimal("391035000000"), 2024)
    # Ensure source_evidence_id matches table_ev chunk_id
    f1 = pytest.importorskip("dataclasses").replace(
        f1,
        document_id=table_ev.document_id,
        document_version_id=table_ev.document_version_id,
        page_number=table_ev.page_number,
        chunk_id=str(table_ev.chunk_id),
        source_evidence_id=str(table_ev.chunk_id),
    )

    plan = ReasoningPlan(
        plan_id="plan-1",
        query="What was Apple revenue in 2024?",
        operations=[ReasoningOperation.DIRECT_LOOKUP],
        target_metrics=["Revenue"],
        target_periods=["2024"],
        target_companies=["AAPL"],
        required_fact_keys=["revenue_2024"],
        steps_description=["Direct lookup"],
    )

    claims = claim_builder.build_claims(plan, [f1], [])
    assert len(claims) == 1
    assert claims[0].claim_type == "direct_fact"
    assert "Revenue" in claims[0].text

    citations = citation_generator.generate_citations(claims, [f1], [table_ev])
    assert len(citations) == 1
    assert citations[0].document_id == table_ev.document_id
    assert citations[0].chunk_id == str(table_ev.chunk_id)

    validated_cits = citation_validator.validate_citations(citations, [table_ev])
    assert len(validated_cits) == 1
    assert validated_cits[0].verified


def test_invalid_citation_rejected() -> None:
    citation_validator = DeterministicCitationValidator()
    table_ev = make_sample_apple_table_evidence()

    # Fabricated citation with unknown chunk_id
    fake_cit = Citation(
        citation_id="cit-fake",
        claim_id="claim-1",
        document_id="doc-fake",
        document_version_id="ver-fake",
        page_number=999,
        page_numbers=[999],
        chunk_id="chunk-fake-999",
        table_id=None,
        section_path="",
        ticker="AAPL",
        source_excerpt="Fabricated text",
        bounding_box=None,
        citation_type=CitationType.DIRECT_SOURCE,
        verified=False,
    )

    validated = citation_validator.validate_citations([fake_cit], [table_ev])
    assert len(validated) == 1
    assert not validated[0].verified
    assert "not found in retrieved evidence" in str(validated[0].validation_notes)

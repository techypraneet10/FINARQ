"""Unit tests for query normalization, classification, and financial signal extraction."""

import pytest

from financial_rag.domain.entities.retrieval import QueryType, RetrievalFilter
from financial_rag.infrastructure.retrieval.query_analyzer import FinancialQueryAnalyzer


@pytest.fixture
def analyzer() -> FinancialQueryAnalyzer:
    return FinancialQueryAnalyzer()


def test_query_normalization(analyzer: FinancialQueryAnalyzer) -> None:
    raw = "   “What   was  Apple’s   revenue in  2024?”  —  (in millions)   "  # noqa: RUF001
    normalized = analyzer.normalize(raw)
    assert normalized == '"What was Apple\'s revenue in 2024?" - (in millions)'
    assert analyzer.normalize("") == ""


def test_financial_signals_extraction(analyzer: FinancialQueryAnalyzer) -> None:
    # 1. Company & Ticker extraction
    query = "What was Microsoft and Apple revenue in 2024 compared to 2023?"
    signals = analyzer.extract_signals(analyzer.normalize(query))
    assert "MSFT" in signals.tickers
    assert "AAPL" in signals.tickers
    assert "Microsoft" in signals.company_names
    assert "Apple" in signals.company_names
    assert "revenue" in signals.metrics
    assert signals.fiscal_years == [2023, 2024]
    assert signals.is_comparison is True
    assert signals.is_multi_period is True

    # 2. Section & Quarter extraction
    query2 = "According to Item 1A Risk Factors, what are the cloud risks in Q3 2024?"
    signals2 = analyzer.extract_signals(analyzer.normalize(query2))
    assert "Item 1A. Risk Factors" in signals2.sections
    assert "Q3" in signals2.fiscal_periods
    assert signals2.fiscal_years == [2024]

    # 3. Table and Statement extraction
    query3 = "What were total assets on the Balance Sheet in 2024?"
    signals3 = analyzer.extract_signals(analyzer.normalize(query3))
    assert "Balance Sheet" in signals3.statement_types
    assert "total assets" in signals3.metrics
    assert signals3.is_table_lookup is True


def test_query_classification(analyzer: FinancialQueryAnalyzer) -> None:
    # Section specific
    q1 = analyzer.analyze("What risks are disclosed in Item 1A?")
    assert q1.query_type == QueryType.SECTION_SPECIFIC

    # Table lookup
    q2 = analyzer.analyze("Show me the breakdown in the balance sheet table for total assets.")
    assert q2.query_type == QueryType.TABLE_LOOKUP

    # Comparison
    q3 = analyzer.analyze("Compare revenue growth between 2023 and 2024.")
    assert q3.query_type == QueryType.COMPARISON

    # Trend
    q4 = analyzer.analyze("What is the historical trend of gross margins over time?")
    assert q4.query_type == QueryType.TREND

    # Definition
    q5 = analyzer.analyze("What is ASC 606 revenue recognition policy?")
    assert q5.query_type == QueryType.DEFINITION

    # Document specific
    q6 = analyzer.analyze("What was discussed in the 2024 10-K annual report?")
    assert q6.query_type == QueryType.DOCUMENT_SPECIFIC

    # Factual lookup
    q7 = analyzer.analyze("What was Apple's net income in 2024?")
    assert q7.query_type == QueryType.FACTUAL


def test_analyze_with_filters(analyzer: FinancialQueryAnalyzer) -> None:
    filters = RetrievalFilter(ticker_symbols=["AAPL"], fiscal_years=[2024])
    result = analyzer.analyze(
        raw_query="What was net income?",
        filters=filters,
        top_k=5,
    )
    assert result.filters.ticker_symbols == ["AAPL"]
    assert result.filters.fiscal_years == [2024]
    assert result.top_k == 5
    assert "net income" in result.signals.metrics

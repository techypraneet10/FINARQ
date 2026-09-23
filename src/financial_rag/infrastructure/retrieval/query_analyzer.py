"""Query normalization, intent classification, and financial signals extraction."""

import re
import unicodedata
from typing import Any

from financial_rag.domain.entities.retrieval import (
    FinancialSignals,
    QueryType,
    RetrievalFilter,
    RetrievalQuery,
)
from financial_rag.domain.interfaces.retrieval import QueryAnalyzerProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.retrieval.query_analyzer")

# Ticker symbol and company name lookup dictionary
KNOWN_COMPANIES: dict[str, str] = {
    "apple": "AAPL",
    "apple inc": "AAPL",
    "microsoft": "MSFT",
    "microsoft corp": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "alphabet inc": "GOOGL",
    "amazon": "AMZN",
    "amazon com": "AMZN",
    "nvidia": "NVDA",
    "nvidia corp": "NVDA",
    "tesla": "TSLA",
    "tesla inc": "TSLA",
    "meta": "META",
    "meta platforms": "META",
    "facebook": "META",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "jpmorgan chase": "JPM",
    "walmart": "WMT",
    "johnson & johnson": "JNJ",
    "disney": "DIS",
    "walt disney": "DIS",
    "netflix": "NFLX",
    "berkshire": "BRK",
    "berkshire hathaway": "BRK",
    "visa": "V",
}

# Standard corporate financial metrics
FINANCIAL_METRICS: list[str] = [
    "revenue",
    "total revenue",
    "net revenue",
    "net sales",
    "sales",
    "operating income",
    "operating profit",
    "net income",
    "net loss",
    "gross profit",
    "gross margin",
    "operating margin",
    "net margin",
    "ebitda",
    "ebit",
    "earnings per share",
    "diluted eps",
    "basic eps",
    "eps",
    "total assets",
    "current assets",
    "total liabilities",
    "current liabilities",
    "stockholders equity",
    "shareholders equity",
    "retained earnings",
    "cash and cash equivalents",
    "operating cash flow",
    "cash flow from operations",
    "capital expenditures",
    "capex",
    "free cash flow",
    "total debt",
    "long term debt",
    "short term debt",
    "research and development",
    "r&d",
    "selling general and administrative",
    "sg&a",
    "cost of goods sold",
    "cost of sales",
    "cogs",
    "effective tax rate",
    "income tax expense",
    "dividends",
    "share repurchase",
    "shares outstanding",
]

# Standard SEC items and filing sections
SEC_SECTIONS: list[tuple[str, str]] = [
    (r"\bitem\s+1a\b|\brisk\s+factors\b", "Item 1A. Risk Factors"),
    (
        r"\bitem\s+7a\b|\bquantitative\s+and\s+qualitative\b",
        "Item 7A. Quantitative and Qualitative Disclosures",
    ),
    (
        r"\bitem\s+7\b|\bmd&a\b|\bmanagement['\u2019]?s\s+discussion\b",
        "Item 7. Management's Discussion and Analysis",
    ),
    (
        r"\bitem\s+8\b|\bfinancial\s+statements\b|\bnotes\s+to\b",
        "Item 8. Financial Statements and Supplementary Data",
    ),
    (r"\bitem\s+1\b|\bbusiness\b", "Item 1. Business"),
    (r"\bitem\s+2\b|\bproperties\b", "Item 2. Properties"),
    (r"\bitem\s+3\b|\blegal\s+proceedings\b", "Item 3. Legal Proceedings"),
    (r"\bitem\s+4\b|\bmine\s+safety\b", "Item 4. Mine Safety Disclosures"),
    (r"\bitem\s+5\b|\bmarket\s+for\b", "Item 5. Market for Registrant's Common Equity"),
    (r"\bitem\s+9a\b|\bcontrols\s+and\s+procedures\b", "Item 9A. Controls and Procedures"),
]


class FinancialQueryAnalyzer(QueryAnalyzerProtocol):
    """Production financial query normalization, intent classification, and entity extraction."""

    def normalize(self, text: str) -> str:
        """Normalize raw query text while preserving critical financial notation."""
        if not text:
            return ""

        # 1. Normalize Unicode (compat decomposition to standard chars)
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Standardize quotation marks and dashes
        normalized = re.sub(r'["\u201c\u201d\u201e\u201f]', '"', normalized)
        normalized = re.sub(r"['\u2018\u2019\u201a\u201b`]", "'", normalized)
        normalized = re.sub(r"[\u2013\u2014\u2212-]", "-", normalized)

        # 3. Collapse multiple whitespace while preserving word boundaries
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def extract_signals(self, normalized_text: str) -> FinancialSignals:
        """Extract high-confidence financial entities and signals from normalized query."""
        text_lower = normalized_text.lower()

        # 1. Extract Tickers & Company Names
        tickers: set[str] = set()
        companies: set[str] = set()

        for company_name, ticker in KNOWN_COMPANIES.items():
            pattern = rf"\b{re.escape(company_name)}\b"
            if re.search(pattern, text_lower):
                companies.add(company_name.title())
                tickers.add(ticker)

        # Extract explicit uppercase 1-5 letter ticker patterns (e.g. AAPL, MSFT)
        explicit_tickers = re.findall(r"\b[A-Z]{1,5}\b", normalized_text)
        stopwords = {
            "A",
            "I",
            "AN",
            "THE",
            "AND",
            "OR",
            "FOR",
            "IN",
            "ON",
            "AT",
            "TO",
            "BY",
            "OF",
            "IS",
            "WAS",
            "ARE",
            "WHAT",
            "HOW",
            "WHY",
            "WHEN",
            "WHO",
            "ITEM",
            "SEC",
            "GAAP",
            "IFRS",
            "USD",
            "EUR",
            "GBP",
            "FY",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
        }
        for candidate in explicit_tickers:
            if candidate not in stopwords and len(candidate) >= 2:
                tickers.add(candidate)

        # 2. Extract Financial Metrics
        found_metrics: list[str] = []
        for metric in sorted(FINANCIAL_METRICS, key=len, reverse=True):
            pattern = rf"\b{re.escape(metric)}\b"
            if re.search(pattern, text_lower) and not any(
                metric in existing for existing in found_metrics
            ):
                found_metrics.append(metric)

        # 3. Extract Fiscal Years (e.g. 2021, 2022, 2023, 2024, FY23, FY2024)
        year_matches = re.findall(r"\b(19\d{2}|20\d{2})\b", normalized_text)
        fy_matches = re.findall(r"\bfy\s*(\d{2,4})\b", text_lower)
        years_set: set[int] = set()

        for y in year_matches:
            years_set.add(int(y))
        for fy in fy_matches:
            val = int(fy)
            if val < 100:
                val += 2000
            years_set.add(val)

        fiscal_years = sorted(years_set)

        # 4. Extract Fiscal Periods (e.g. Q1, Q2, Q3, Q4, FY)
        periods_set: set[str] = set()
        q_matches = re.findall(r"\b(q[1-4]|[1-4]q)\b", text_lower)
        for q in q_matches:
            periods_set.add(f"Q{q.replace('q', '')}")

        if re.search(r"\b(full\s+year|annual|fy)\b", text_lower):
            periods_set.add("FY")

        fiscal_periods = sorted(periods_set)

        # 5. Extract SEC Filing Sections
        sections: list[str] = []
        for pattern, section_name in SEC_SECTIONS:
            if re.search(pattern, text_lower) and section_name not in sections:
                sections.append(section_name)

        # 6. Extract Statement Types
        statement_types: list[str] = []
        if re.search(r"\bbalance\s+sheet\b", text_lower):
            statement_types.append("Balance Sheet")
        if re.search(r"\bincome\s+statement\b|\bstatement\s+of\s+operations\b", text_lower):
            statement_types.append("Income Statement")
        if re.search(r"\bcash\s+flows?\b", text_lower):
            statement_types.append("Statement of Cash Flows")
        if re.search(r"\bstockholders['\u2019]?\s+equity\b", text_lower):
            statement_types.append("Statement of Stockholders' Equity")

        # 7. Extract Currencies
        currencies: list[str] = []
        if "$" in normalized_text or re.search(r"\busd\b|\bdollars?\b", text_lower):
            currencies.append("USD")
        if "€" in normalized_text or re.search(r"\beur\b|\beuros?\b", text_lower):
            currencies.append("EUR")
        if "£" in normalized_text or re.search(r"\bgbp\b|\bpounds?\b", text_lower):
            currencies.append("GBP")

        # 8. Structural Intent Flags
        is_comparison = bool(
            re.search(
                r"\b(vs|versus|compared\s+(with|to)|comparison|growth|increase|decrease|change\s+from|change\s+between|higher|lower|difference)\b",
                text_lower,
            )
            or len(fiscal_years) > 1
        )

        is_table_lookup = bool(
            re.search(
                r"\b(table|balance\s+sheet|breakdown|schedule|reconciliation|statement|line\s+item|segment|assets|liabilities)\b",
                text_lower,
            )
            or statement_types
        )

        is_multi_period = len(fiscal_years) > 1 or len(fiscal_periods) > 1

        return FinancialSignals(
            tickers=sorted(tickers),
            company_names=sorted(companies),
            metrics=found_metrics,
            fiscal_years=fiscal_years,
            fiscal_periods=fiscal_periods,
            sections=sections,
            statement_types=statement_types,
            currencies=currencies,
            is_comparison=is_comparison,
            is_table_lookup=is_table_lookup,
            is_multi_period=is_multi_period,
        )

    def classify_query(self, normalized_text: str, signals: FinancialSignals) -> QueryType:
        """Classify user query intent into formal domain QueryType."""
        text_lower = normalized_text.lower()

        # Multi-document / cross-filing intent
        if re.search(
            r"\b(across\s+(filings|reports|documents)|between\s+the\s+\d{4}\s+and\s+\d{4}|compare\s+across)\b",
            text_lower,
        ):
            return QueryType.MULTI_DOCUMENT

        # Section-specific inquiry (e.g. Item 1A, Item 7, Item 8, MD&A)
        if signals.sections or re.search(
            r"\b(item\s+[0-9][a-z]?|part\s+[i|v|x]+|in\s+item\s+\d|according\s+to\s+item)\b",
            text_lower,
        ):
            return QueryType.SECTION_SPECIFIC

        # Document-specific inquiry (e.g. 10-K, 10-Q, 8-K, Annual Report)
        if re.search(r"\b(10-k|10-q|8-k|annual\s+report|quarterly\s+report|proxy)\b", text_lower):
            return QueryType.DOCUMENT_SPECIFIC

        # Table lookup / statement balance check
        if signals.is_table_lookup and (
            "table" in text_lower
            or "balance sheet" in text_lower
            or "breakdown" in text_lower
            or any(m in text_lower for m in ["total assets", "total liabilities", "total debt"])
        ):
            return QueryType.TABLE_LOOKUP

        # Comparison query (multi-year, growth rate, comparison keywords)
        if signals.is_comparison:
            return QueryType.COMPARISON

        # Trend query over multiple periods / time series
        if re.search(
            r"\b(trend|over\s+time|historically|historical\s+trend|trajectory|evolution)\b",
            text_lower,
        ):
            return QueryType.TREND

        # Definition / terminology query
        if re.search(
            r"^(what\s+is|define|meaning\s+of|explain\s+the\s+term|what\s+does\s+.+\s+mean)",
            text_lower,
        ):
            return QueryType.DEFINITION

        # Numerical computation query
        if re.search(
            r"\b(how\s+much|percentage\s+of|ratio\s+of|sum\s+of|total\s+amount|calculate|margin)\b",
            text_lower,
        ):
            return QueryType.NUMERICAL

        # Factual lookup
        if signals.metrics or signals.tickers or signals.fiscal_years:
            return QueryType.FACTUAL

        return QueryType.UNKNOWN

    def analyze(
        self,
        raw_query: str,
        filters: RetrievalFilter | None = None,
        top_k: int = 10,
        dense_top_k: int = 50,
        sparse_top_k: int = 50,
        rerank_top_k: int = 20,
    ) -> RetrievalQuery:
        """Analyze raw query text, extracting normalized query, classification, and signals."""
        normalized = self.normalize(raw_query)
        signals = self.extract_signals(normalized)
        query_type = self.classify_query(normalized, signals)
        effective_filters = filters or RetrievalFilter()

        # Enhance filters with high-confidence signals if filter fields are empty
        enriched_custom: dict[str, Any] = dict(effective_filters.custom_metadata)

        # Merge signals into filters where appropriate without overriding explicit filters
        target_tickers = effective_filters.ticker_symbols or (
            signals.tickers if signals.tickers else None
        )
        target_years = effective_filters.fiscal_years or (
            signals.fiscal_years if signals.fiscal_years else None
        )
        target_periods = effective_filters.fiscal_periods or (
            signals.fiscal_periods if signals.fiscal_periods else None
        )

        merged_filters = RetrievalFilter(
            document_ids=effective_filters.document_ids,
            version_ids=effective_filters.version_ids,
            tenant_id=effective_filters.tenant_id,
            ticker_symbols=target_tickers,
            fiscal_years=target_years,
            fiscal_periods=target_periods,
            document_types=effective_filters.document_types,
            sections=effective_filters.sections,
            chunk_types=effective_filters.chunk_types,
            table_only=effective_filters.table_only or (signals.is_table_lookup if False else None),
            custom_metadata=enriched_custom,
        )

        query = RetrievalQuery(
            raw_query=raw_query,
            normalized_query=normalized,
            tenant_id=effective_filters.tenant_id or "default_tenant",
            query_type=query_type,
            signals=signals,
            filters=merged_filters,
            top_k=top_k,
            dense_top_k=dense_top_k,
            sparse_top_k=sparse_top_k,
            rerank_top_k=rerank_top_k,
        )

        logger.info(
            f"Analyzed query '{query.id}': type={query_type.value}, tickers={signals.tickers}, "
            f"metrics={signals.metrics}, years={signals.fiscal_years}"
        )
        return query

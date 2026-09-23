"""Fiscal period normalizer standardizing financial reporting dates and intervals."""

import re
from typing import ClassVar

from financial_rag.domain.entities.reasoning import FiscalPeriod
from financial_rag.domain.interfaces.reasoning import PeriodNormalizerProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.period_normalizer")


class FiscalPeriodNormalizer(PeriodNormalizerProtocol):
    """Normalizes fiscal years, quarters, and period descriptions into FiscalPeriod."""

    # Patterns for FY and Year e.g., FY2024, FY 2024, FY24, 2024, Fiscal Year 2024
    FY_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?:FY|Fiscal\s+Year|Year\s+Ended)?\s*(20\d{2}|19\d{2})", re.IGNORECASE
    )

    # Patterns for Quarters e.g., Q1 2024, Q1'24, First Quarter 2024, 1Q2024, Q4
    QUARTER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(Q[1-4]|First\s+Quarter|Second\s+Quarter|Third\s+Quarter|Fourth\s+Quarter|[1-4]Q)\s*(?:of\s*)?(?:FY|Fiscal\s+Year)?\s*(20\d{2}|19\d{2})?",
        re.IGNORECASE,
    )

    # Months ended pattern e.g., Three Months Ended March 31, 2024
    MONTHS_ENDED_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(Three|Six|Nine|Twelve)\s+Months\s+Ended\s+([A-Za-z]+)\s+\d{1,2},?\s*(20\d{2}|19\d{2})?",
        re.IGNORECASE,
    )

    QUARTER_NORM_MAP: ClassVar[dict[str, str]] = {
        "q1": "Q1",
        "1q": "Q1",
        "first quarter": "Q1",
        "q2": "Q2",
        "2q": "Q2",
        "second quarter": "Q2",
        "q3": "Q3",
        "3q": "Q3",
        "third quarter": "Q3",
        "q4": "Q4",
        "4q": "Q4",
        "fourth quarter": "Q4",
    }

    MONTHS_MAP: ClassVar[dict[str, str]] = {
        "three": "Q1",  # Approximate default if calendar/fiscal not explicit
        "six": "H1",
        "nine": "9M",
        "twelve": "FY",
    }

    def normalize(
        self,
        raw_period: str,
        default_year: int | None = None,
    ) -> FiscalPeriod:
        """Normalize period string into structured FiscalPeriod."""
        if not raw_period or not raw_period.strip():
            return FiscalPeriod(
                fiscal_year=default_year,
                period_type="FY" if default_year else "Unknown",
                source_text="",
                is_uncertain=default_year is None,
            )

        clean = raw_period.strip()
        lower = clean.lower()

        # Check TTM / Trailing Twelve Months
        if "ttm" in lower or "trailing twelve months" in lower:
            # Look for optional year
            yr_match = re.search(r"(20\d{2}|19\d{2})", clean)
            year = int(yr_match.group(1)) if yr_match else default_year
            return FiscalPeriod(
                fiscal_year=year,
                period_type="TTM",
                source_text=clean,
                is_uncertain=year is None,
            )

        # Check Quarters (e.g. Q3 2024 or Third Quarter 2023)
        match_q = self.QUARTER_PATTERN.search(clean)
        if match_q:
            q_raw = match_q.group(1).lower()
            q_norm = self.QUARTER_NORM_MAP.get(q_raw, "Q1")
            yr_str = match_q.group(2)
            year = int(yr_str) if yr_str else default_year
            return FiscalPeriod(
                fiscal_year=year,
                period_type=q_norm,
                source_text=clean,
                is_uncertain=year is None,
            )

        # Check Months ended (e.g. Three Months Ended September 30, 2024)
        match_m = self.MONTHS_ENDED_PATTERN.search(clean)
        if match_m:
            count_str = match_m.group(1).lower()
            month_str = match_m.group(2).lower()
            yr_str = match_m.group(3)
            year = int(yr_str) if yr_str else default_year
            ptype = self.MONTHS_MAP.get(count_str, "FY")
            # Refine quarter if 3 months ended
            if count_str == "three":
                if "march" in month_str or "mar" in month_str:
                    ptype = "Q1"
                elif "june" in month_str or "jun" in month_str:
                    ptype = "Q2"
                elif "september" in month_str or "sep" in month_str:
                    ptype = "Q3"
                elif "december" in month_str or "dec" in month_str:
                    ptype = "Q4"
            return FiscalPeriod(
                fiscal_year=year,
                period_type=ptype,
                source_text=clean,
                is_uncertain=year is None,
            )

        # Check FY or Full Year (e.g. 2024, FY2023)
        match_fy = self.FY_PATTERN.search(clean)
        if match_fy:
            year = int(match_fy.group(1))
            return FiscalPeriod(
                fiscal_year=year,
                period_type="FY",
                source_text=clean,
                is_uncertain=False,
            )

        # Fallback to default year
        return FiscalPeriod(
            fiscal_year=default_year,
            period_type="FY" if default_year else "Unknown",
            source_text=clean,
            is_uncertain=True,
        )

"""High-precision financial value parser converting strings into Decimal-based FinancialValue."""

import re
from decimal import Decimal, InvalidOperation
from typing import ClassVar

from financial_rag.domain.entities.reasoning import FinancialScale, FinancialValue
from financial_rag.domain.interfaces.reasoning import FinancialValueParserProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.value_parser")


class FinancialValueParser(FinancialValueParserProtocol):
    """Parses monetary numbers, accounting parentheticals, currencies, units, and scales."""

    # Parenthetical negative regex: (1,234.50), $(850), (2.1%), $ (1,234.5M)
    PARENTHETICAL_NEGATIVE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^\s*([\$€£¥₹]?)\s*\(\s*([\$€£¥₹]?)\s*([\d,]+(?:\.\d+)?)\s*([KkMmBbTt%]?|(?:thousand|million|billion|trillion|percent)?)\s*\)\s*\%?\s*$",
        re.IGNORECASE,
    )

    # Standard signed/unsigned numeric regex: $120.5B, -1,234.56, +5.2%, 850 million
    NUMERIC_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^\s*([\$€£¥₹]?)\s*([\+\-]?[\d,]+(?:\.\d+)?)\s*([\$€£¥₹]?)\s*([KkMmBbTt%]?|(?:thousand|million|billion|trillion|percent)?)\s*$",
        re.IGNORECASE,
    )

    # Scale keyword mapping
    SCALE_MAP: ClassVar[dict[str, FinancialScale]] = {
        "k": FinancialScale.THOUSANDS,
        "thousand": FinancialScale.THOUSANDS,
        "thousands": FinancialScale.THOUSANDS,
        "m": FinancialScale.MILLIONS,
        "million": FinancialScale.MILLIONS,
        "millions": FinancialScale.MILLIONS,
        "b": FinancialScale.BILLIONS,
        "billion": FinancialScale.BILLIONS,
        "billions": FinancialScale.BILLIONS,
        "t": FinancialScale.TRILLIONS,
        "trillion": FinancialScale.TRILLIONS,
        "trillions": FinancialScale.TRILLIONS,
        "%": FinancialScale.PERCENT,
        "percent": FinancialScale.PERCENT,
        "percentage": FinancialScale.PERCENT,
    }

    # Currency symbol mapping
    CURRENCY_SYMBOLS: ClassVar[dict[str, str]] = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "₹": "INR",
        "USD": "USD",
        "EUR": "EUR",
        "GBP": "GBP",
        "JPY": "JPY",
        "INR": "INR",
        "CAD": "CAD",
        "AUD": "AUD",
        "CHF": "CHF",
        "CNY": "CNY",
    }

    def detect_currency(self, text: str, default: str = "USD") -> str:
        """Detect currency ISO code from string or context."""
        upper = text.upper()
        for symbol, code in self.CURRENCY_SYMBOLS.items():
            if symbol in text or symbol in upper:
                return code
        if "DOLLAR" in upper:
            return "USD"
        if "EURO" in upper:
            return "EUR"
        if "POUND" in upper:
            return "GBP"
        if "YEN" in upper:
            return "JPY"
        if "RUPEE" in upper:
            return "INR"
        return default

    def detect_scale_from_text(self, text: str) -> FinancialScale:
        """Detect scale multiplier from text descriptors (e.g. 'in millions')."""
        lower = text.lower()
        if (
            "in trillions" in lower
            or "(trillions)" in lower
            or "trillion" in lower
            or "trillions" in lower
        ):
            return FinancialScale.TRILLIONS
        if (
            "in billions" in lower
            or "(billions)" in lower
            or "billion" in lower
            or "billions" in lower
        ):
            return FinancialScale.BILLIONS
        if (
            "in millions" in lower
            or "(millions)" in lower
            or "million" in lower
            or "millions" in lower
        ):
            return FinancialScale.MILLIONS
        if (
            "in thousands" in lower
            or "(thousands)" in lower
            or "thousand" in lower
            or "thousands" in lower
        ):
            return FinancialScale.THOUSANDS
        if "%" in lower or "percent" in lower or "ratio" in lower:
            return FinancialScale.PERCENT
        return FinancialScale.EXACT

    def parse(
        self,
        raw_str: str,
        context_units: str = "",
        context_currency: str = "USD",
        context_scale: float = 1.0,
    ) -> FinancialValue | None:
        """Parse raw financial string with currency, commas, parentheticals, and scales into Decimal."""
        if not raw_str or not raw_str.strip():
            return None

        clean_str = raw_str.strip()
        # Handle em-dash or null representations in financial tables
        if clean_str in ("—", "-", "--", "N/A", "n/a", "nil", "None", "$ —", "$ -"):
            return FinancialValue(
                raw_value=raw_str,
                display_value="$0.00",
                numeric_value=Decimal("0"),
                unscaled_value=Decimal("0"),
                currency=context_currency,
                scale=FinancialScale.EXACT,
                unit=context_units or context_currency,
                is_negative=False,
                is_percentage=False,
            )

        currency = self.detect_currency(clean_str, default=context_currency)
        is_percentage = "%" in clean_str or "percent" in clean_str.lower()
        is_negative = False
        unscaled_dec: Decimal | None = None
        detected_scale = FinancialScale.EXACT

        # 1. Check parenthetical negative: (1,234.50) or $(850M)
        match_neg = self.PARENTHETICAL_NEGATIVE_PATTERN.match(clean_str)
        if match_neg:
            is_negative = True
            curr_sym_1, curr_sym_2, num_str, scale_suffix = match_neg.groups()
            curr_sym = curr_sym_1 or curr_sym_2
            if curr_sym:
                currency = self.detect_currency(curr_sym, default=currency)
            clean_num = num_str.replace(",", "")
            try:
                unscaled_dec = -abs(Decimal(clean_num))
            except InvalidOperation:
                return None

            if scale_suffix:
                scale_key = scale_suffix.strip().lower()
                detected_scale = self.SCALE_MAP.get(scale_key, FinancialScale.EXACT)
                if scale_key in ("%", "percent", "percentage"):
                    is_percentage = True

        # 2. Check standard numeric format: $120.5B, -1,234.56, +5.2%
        if unscaled_dec is None:
            match_num = self.NUMERIC_PATTERN.match(clean_str)
            if match_num:
                curr_sym_1, num_str, curr_sym_2, scale_suffix = match_num.groups()
                curr_sym = curr_sym_1 or curr_sym_2
                if curr_sym:
                    currency = self.detect_currency(curr_sym, default=currency)
                clean_num = num_str.replace(",", "")
                try:
                    val = Decimal(clean_num)
                    is_negative = val < 0
                    unscaled_dec = val
                except InvalidOperation:
                    return None

                if scale_suffix:
                    scale_key = scale_suffix.strip().lower()
                    detected_scale = self.SCALE_MAP.get(scale_key, FinancialScale.EXACT)
                    if scale_key in ("%", "percent", "percentage"):
                        is_percentage = True

        # 3. Fallback: search for numbers and suffix in text
        if unscaled_dec is None:
            # Extract first continuous numerical pattern
            num_match = re.search(r"([\+\-]?[\d,]+(?:\.\d+)?)", clean_str)
            if not num_match:
                return None
            num_str = num_match.group(1).replace(",", "")
            try:
                val = Decimal(num_str)
                if "(" in clean_str and ")" in clean_str:
                    is_negative = True
                    unscaled_dec = -abs(val)
                else:
                    is_negative = val < 0
                    unscaled_dec = val
            except InvalidOperation:
                return None

            detected_scale = self.detect_scale_from_text(clean_str)

        # Reconcile scale with context if not detected in the raw string
        final_scale = detected_scale
        if final_scale == FinancialScale.EXACT:
            if context_units:
                final_scale = self.detect_scale_from_text(context_units)
            elif context_scale > 1.0:
                if context_scale == 1_000_000_000_000.0:
                    final_scale = FinancialScale.TRILLIONS
                elif context_scale == 1_000_000_000.0:
                    final_scale = FinancialScale.BILLIONS
                elif context_scale == 1_000_000.0:
                    final_scale = FinancialScale.MILLIONS
                elif context_scale == 1_000.0:
                    final_scale = FinancialScale.THOUSANDS

        # Compute fully scaled Decimal value
        multiplier = final_scale.multiplier
        if is_percentage and final_scale != FinancialScale.PERCENT:
            numeric_value = unscaled_dec * multiplier * Decimal("0.01")
        else:
            numeric_value = unscaled_dec * multiplier

        # Format display value
        if is_percentage:
            display_value = f"{unscaled_dec}%"
            unit = "%"
        else:
            unit = (
                f"{currency} ({final_scale.value})"
                if final_scale != FinancialScale.EXACT
                else currency
            )
            abs_val = abs(unscaled_dec)
            formatted_num = f"{abs_val:,.2f}" if abs_val % 1 != 0 else f"{abs_val:,.0f}"
            scale_suffix_display = (
                f" {final_scale.value}" if final_scale != FinancialScale.EXACT else ""
            )
            curr_prefix = "$" if currency == "USD" else f"{currency} "
            if is_negative:
                display_value = f"({curr_prefix}{formatted_num}{scale_suffix_display})"
            else:
                display_value = f"{curr_prefix}{formatted_num}{scale_suffix_display}"

        return FinancialValue(
            raw_value=raw_str,
            display_value=display_value,
            numeric_value=numeric_value,
            unscaled_value=unscaled_dec,
            currency=currency if not is_percentage else None,
            scale=final_scale,
            unit=unit,
            is_negative=is_negative,
            is_percentage=is_percentage,
        )

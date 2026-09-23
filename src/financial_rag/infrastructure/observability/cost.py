"""Configurable LLM token usage and cost estimation calculator."""

from dataclasses import dataclass

from financial_rag.domain.interfaces.observability import CostCalculatorProtocol


@dataclass(frozen=True)
class ModelPricing:
    """Pricing rates per 1,000,000 tokens."""

    input_cost_per_million: float
    output_cost_per_million: float
    cached_input_cost_per_million: float = 0.0


# Standard default pricing table (USD per 1M tokens) as of 2025/2026
DEFAULT_PRICING_TABLE: dict[str, ModelPricing] = {
    # OpenAI Models
    "gpt-4o": ModelPricing(
        input_cost_per_million=2.50,
        output_cost_per_million=10.00,
        cached_input_cost_per_million=1.25,
    ),
    "gpt-4o-mini": ModelPricing(
        input_cost_per_million=0.15,
        output_cost_per_million=0.60,
        cached_input_cost_per_million=0.075,
    ),
    "gpt-4-turbo": ModelPricing(
        input_cost_per_million=10.00,
        output_cost_per_million=30.00,
    ),
    # Anthropic Models
    "claude-3-5-sonnet-20241022": ModelPricing(
        input_cost_per_million=3.00,
        output_cost_per_million=15.00,
        cached_input_cost_per_million=0.30,
    ),
    "claude-3-5-haiku-20241022": ModelPricing(
        input_cost_per_million=1.00,
        output_cost_per_million=5.00,
        cached_input_cost_per_million=0.10,
    ),
    # Google Gemini Models
    "gemini-1.5-pro": ModelPricing(
        input_cost_per_million=1.25,
        output_cost_per_million=5.00,
        cached_input_cost_per_million=0.3125,
    ),
    "gemini-1.5-flash": ModelPricing(
        input_cost_per_million=0.075,
        output_cost_per_million=0.30,
        cached_input_cost_per_million=0.01875,
    ),
    # Fake / Mock Models for local tests and deterministic CI
    "fake-model": ModelPricing(
        input_cost_per_million=0.0,
        output_cost_per_million=0.0,
    ),
    "mock-provider": ModelPricing(
        input_cost_per_million=0.0,
        output_cost_per_million=0.0,
    ),
}


class CostCalculator(CostCalculatorProtocol):
    """Calculates dollar costs for LLM inference based on token usage and pricing tables."""

    def __init__(self, custom_pricing: dict[str, ModelPricing] | None = None) -> None:
        self._pricing: dict[str, ModelPricing] = dict(DEFAULT_PRICING_TABLE)
        if custom_pricing:
            self._pricing.update(custom_pricing)

    def register_model_pricing(self, model_name: str, pricing: ModelPricing) -> None:
        """Register or update pricing rates for a specific model."""
        self._pricing[model_name.lower()] = pricing

    def calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
    ) -> float:
        """Compute total estimated USD cost for token consumption."""
        normalized_name = model_name.lower().strip()
        pricing = self._pricing.get(normalized_name)

        # Fallback to prefix matching (e.g. gpt-4o-* -> gpt-4o)
        if not pricing:
            for k, p in self._pricing.items():
                if normalized_name.startswith(k):
                    pricing = p
                    break

        if not pricing:
            # Default to gpt-4o pricing if completely unrecognized
            pricing = self._pricing["gpt-4o"]

        uncached_input = max(0, input_tokens - cached_tokens)
        input_cost = (uncached_input / 1_000_000.0) * pricing.input_cost_per_million
        cached_cost = (cached_tokens / 1_000_000.0) * pricing.cached_input_cost_per_million
        output_cost = (output_tokens / 1_000_000.0) * pricing.output_cost_per_million

        return round(input_cost + cached_cost + output_cost, 6)


# Default singleton cost calculator
cost_calculator = CostCalculator()

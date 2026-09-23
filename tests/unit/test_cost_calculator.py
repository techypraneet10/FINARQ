"""Unit tests for LLM token usage and cost estimation."""

from financial_rag.infrastructure.observability.cost import CostCalculator, ModelPricing


def test_cost_calculator_gpt4o() -> None:
    calc = CostCalculator()
    # 1,000,000 input tokens ($2.50) + 1,000,000 output tokens ($10.00) = $12.50
    cost = calc.calculate_cost("gpt-4o", 1_000_000, 1_000_000)
    assert cost == 12.50


def test_cost_calculator_cached_tokens() -> None:
    calc = CostCalculator()
    # 1M input of which 500k is cached ($1.25 + $0.625) + 0 output = $1.875
    cost = calc.calculate_cost(
        "gpt-4o", input_tokens=1_000_000, output_tokens=0, cached_tokens=500_000
    )
    assert cost == 1.875


def test_cost_calculator_custom_pricing_registration() -> None:
    calc = CostCalculator()
    calc.register_model_pricing(
        "custom-fin-llm",
        ModelPricing(input_cost_per_million=5.0, output_cost_per_million=20.0),
    )

    cost = calc.calculate_cost("custom-fin-llm", 1_000_000, 500_000)
    assert cost == 15.00


def test_cost_calculator_fake_model_zero_cost() -> None:
    calc = CostCalculator()
    cost = calc.calculate_cost("fake-model", 5000, 1000)
    assert cost == 0.0

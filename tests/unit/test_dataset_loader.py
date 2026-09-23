"""Unit tests for dataset loading, schema parsing, and version discovery."""

import pytest

from financial_rag.domain.entities.evaluation import EvaluationCategory
from financial_rag.domain.exceptions import ConfigurationError
from financial_rag.infrastructure.evaluation.dataset_loader import JsonDatasetLoader


def test_discover_available_datasets() -> None:
    loader = JsonDatasetLoader()
    datasets = loader.list_available_datasets()
    assert "financial_rag_eval_v1" in datasets


def test_load_golden_dataset_v1() -> None:
    loader = JsonDatasetLoader()
    dataset = loader.load_dataset("financial_rag_eval_v1")

    assert dataset.dataset_version == "financial_rag_eval_v1"
    assert len(dataset.cases) == 25

    # Check categories
    ret_cases = dataset.get_cases_by_category(EvaluationCategory.RETRIEVAL)
    assert len(ret_cases) >= 3

    calc_cases = dataset.get_cases_by_category(EvaluationCategory.NUMERICAL_REASONING)
    assert len(calc_cases) >= 7

    adv_cases = dataset.get_cases_by_category(EvaluationCategory.ADVERSARIAL_INJECTION)
    assert len(adv_cases) >= 2


def test_load_nonexistent_dataset_raises() -> None:
    loader = JsonDatasetLoader()
    with pytest.raises(ConfigurationError):
        loader.load_dataset("nonexistent_v999")

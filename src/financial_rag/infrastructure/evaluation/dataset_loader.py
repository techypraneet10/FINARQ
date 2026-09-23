"""Benchmark dataset loader and schema validator."""

import json
from pathlib import Path
from typing import Any

from financial_rag.domain.entities.evaluation import (
    EvaluationCase,
    EvaluationCategory,
    EvaluationDataset,
    ExpectedCalculation,
    ExpectedFact,
)
from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    GroundingStatus,
    ReasoningOperation,
)
from financial_rag.domain.exceptions import ConfigurationError, ValidationError
from financial_rag.domain.interfaces.evaluation import DatasetLoaderProtocol

DEFAULT_DATASETS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "application" / "evaluation" / "datasets"
)


class JsonDatasetLoader(DatasetLoaderProtocol):
    """Loads and validates versioned golden evaluation benchmark datasets from JSON."""

    def __init__(self, datasets_dir: Path | str | None = None) -> None:
        self.datasets_dir = Path(datasets_dir) if datasets_dir else DEFAULT_DATASETS_DIR

    def list_available_datasets(self) -> list[str]:
        """List all discoverable dataset version identifiers."""
        if not self.datasets_dir.exists():
            return []
        versions = []
        for file in self.datasets_dir.glob("*.json"):
            if file.stem != "manifest" and file.stem != "version_manifest":
                versions.append(file.stem)
        return sorted(versions)

    def load_dataset(self, dataset_version: str) -> EvaluationDataset:
        """Load and parse evaluation dataset by version."""
        filename = (
            f"{dataset_version}.json" if not dataset_version.endswith(".json") else dataset_version
        )
        file_path = self.datasets_dir / filename

        if not file_path.exists():
            raise ConfigurationError(
                f"Evaluation dataset '{dataset_version}' not found at {file_path}",
                code="DATASET_NOT_FOUND",
                details={"dataset_version": dataset_version, "path": str(file_path)},
            )

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValidationError(
                f"Failed to parse dataset JSON for '{dataset_version}': {e}",
                code="INVALID_DATASET_JSON",
                details={"error": str(e)},
            ) from e

        return self._parse_dataset_dict(data)

    def _parse_dataset_dict(self, data: dict[str, Any]) -> EvaluationDataset:
        """Parse raw JSON dict into typed EvaluationDataset."""
        dataset_version = data.get("dataset_version", "v1")
        description = data.get("description", "")
        cases_raw = data.get("cases", [])

        parsed_cases: list[EvaluationCase] = []
        for i, raw in enumerate(cases_raw):
            try:
                # Parse expected facts
                facts: list[ExpectedFact] = []
                for f in raw.get("expected_facts", []):
                    facts.append(
                        ExpectedFact(
                            metric=f["metric"],
                            company=f.get("company"),
                            fiscal_year=f.get("fiscal_year"),
                            fiscal_period=f.get("fiscal_period"),
                            expected_value=f.get("expected_value"),
                            scale=f.get("scale"),
                            currency=f.get("currency", "USD"),
                        )
                    )

                # Parse expected calculations
                calcs: list[ExpectedCalculation] = []
                for c in raw.get("expected_calculations", []):
                    calcs.append(
                        ExpectedCalculation(
                            operation=ReasoningOperation(c["operation"].lower()),
                            expected_result_str=str(c["expected_result_str"]),
                            tolerance_pct=float(c.get("tolerance_pct", 0.01)),
                            expected_formula=c.get("expected_formula"),
                        )
                    )

                category_str = raw.get("category", "end_to_end").lower()
                category = EvaluationCategory(category_str)

                ans_status_str = raw.get("expected_answerability", "answerable").lower()
                ans_status = AnswerabilityStatus(ans_status_str)

                grd_status_str = raw.get("expected_grounding_status", "grounded").lower()
                grd_status = GroundingStatus(grd_status_str)

                case = EvaluationCase(
                    case_id=raw.get("case_id", f"case-{i + 1}"),
                    category=category,
                    query=raw["query"],
                    dataset_version=dataset_version,
                    expected_answerability=ans_status,
                    expected_document_ids=raw.get("expected_document_ids", []),
                    expected_page_numbers=raw.get("expected_page_numbers", []),
                    expected_chunk_ids=raw.get("expected_chunk_ids", []),
                    expected_facts=facts,
                    expected_calculations=calcs,
                    expected_citations_count=raw.get("expected_citations_count", 1),
                    expected_grounding_status=grd_status,
                    expected_answer_contains=raw.get("expected_answer_contains", []),
                    forbidden_answer_contains=raw.get("forbidden_answer_contains", []),
                    is_adversarial=bool(raw.get("is_adversarial", False)),
                    metadata=raw.get("metadata", {}),
                )
                parsed_cases.append(case)
            except Exception as e:
                raise ValidationError(
                    f"Invalid evaluation case at index {i}: {e}",
                    code="INVALID_EVALUATION_CASE",
                    details={"index": i, "error": str(e), "raw": raw},
                ) from e

        return EvaluationDataset(
            dataset_version=dataset_version,
            description=description,
            cases=parsed_cases,
            metadata=data.get("metadata", {}),
        )

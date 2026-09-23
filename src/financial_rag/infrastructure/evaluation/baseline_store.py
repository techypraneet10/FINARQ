"""Baseline persistence store for benchmark regression comparisons."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from financial_rag.domain.entities.evaluation import (
    AnswerEvalMetrics,
    BaselineRecord,
    CitationEvalMetrics,
    CostEvalMetrics,
    EvaluationScorecard,
    EvidenceEvalMetrics,
    FactExtractionEvalMetrics,
    GroundingEvalMetrics,
    LatencyEvalMetrics,
    NumericalReasoningEvalMetrics,
    RetrievalEvalMetrics,
    SecurityEvalMetrics,
)
from financial_rag.domain.interfaces.evaluation import BaselineStoreProtocol

DEFAULT_BASELINES_DIR = (
    Path(__file__).resolve().parent.parent.parent / "application" / "evaluation" / "baselines"
)


class FileBaselineStore(BaselineStoreProtocol):
    """File-based persistence store for versioned golden baselines."""

    def __init__(self, baselines_dir: Path | str | None = None) -> None:
        self.baselines_dir = Path(baselines_dir) if baselines_dir else DEFAULT_BASELINES_DIR
        self.baselines_dir.mkdir(parents=True, exist_ok=True)

    def _get_baseline_path(self, dataset_version: str) -> Path:
        """Get file path for a dataset baseline."""
        safe_name = dataset_version.replace("/", "_").replace("\\", "_")
        return self.baselines_dir / f"baseline_{safe_name}.json"

    def get_baseline(self, dataset_version: str) -> BaselineRecord | None:
        """Retrieve stored baseline record for a dataset version."""
        path = self._get_baseline_path(dataset_version)
        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return self._deserialize_baseline(data)
        except Exception:
            return None

    def save_baseline(self, baseline: BaselineRecord) -> None:
        """Persist a baseline record to disk."""
        path = self._get_baseline_path(baseline.dataset_version)
        serialized = self._serialize_baseline(baseline)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, default=str)

    def _serialize_baseline(self, baseline: BaselineRecord) -> dict[str, Any]:
        """Convert BaselineRecord to JSON-serializable dictionary."""
        return {
            "baseline_id": baseline.baseline_id,
            "run_id": baseline.run_id,
            "dataset_version": baseline.dataset_version,
            "prompt_version": baseline.prompt_version,
            "model_name": baseline.model_name,
            "approved_by": baseline.approved_by,
            "created_at": baseline.created_at.isoformat(),
            "scorecard": asdict(baseline.scorecard),
        }

    def _deserialize_baseline(self, data: dict[str, Any]) -> BaselineRecord:
        """Construct BaselineRecord from dictionary."""
        sc_data = data["scorecard"]
        scorecard = EvaluationScorecard(
            evaluation_run_id=sc_data["evaluation_run_id"],
            dataset_version=sc_data["dataset_version"],
            total_cases=sc_data["total_cases"],
            successful_cases=sc_data["successful_cases"],
            retrieval=RetrievalEvalMetrics(**sc_data.get("retrieval", {})),
            evidence=EvidenceEvalMetrics(**sc_data.get("evidence", {})),
            fact_extraction=FactExtractionEvalMetrics(**sc_data.get("fact_extraction", {})),
            numerical_reasoning=NumericalReasoningEvalMetrics(
                **sc_data.get("numerical_reasoning", {})
            ),
            citations=CitationEvalMetrics(**sc_data.get("citations", {})),
            grounding=GroundingEvalMetrics(**sc_data.get("grounding", {})),
            answer=AnswerEvalMetrics(**sc_data.get("answer", {})),
            security=SecurityEvalMetrics(**sc_data.get("security", {})),
            latency=LatencyEvalMetrics(**sc_data.get("latency", {})),
            cost=CostEvalMetrics(**sc_data.get("cost", {})),
            composite_score=float(sc_data.get("composite_score", 1.0)),
            metadata=sc_data.get("metadata", {}),
        )

        return BaselineRecord(
            baseline_id=data["baseline_id"],
            run_id=data["run_id"],
            dataset_version=data["dataset_version"],
            scorecard=scorecard,
            prompt_version=data.get("prompt_version", "FINANCIAL_ANSWER_PROMPT_V1"),
            model_name=data.get("model_name", "fake-model"),
            approved_by=data.get("approved_by", "system"),
        )

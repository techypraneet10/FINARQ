"""Report formatters for machine-readable JSON, tabular CSV, and human-readable Markdown."""

import csv
import io
import json
from dataclasses import asdict
from typing import Any

from financial_rag.domain.entities.evaluation import EvaluationScorecard, RegressionReport
from financial_rag.domain.interfaces.evaluation import ReportFormatterProtocol


class ReportFormatter(ReportFormatterProtocol):
    """Formats evaluation scorecards and regression reports across JSON, Markdown, and CSV."""

    def format_json(
        self,
        scorecard: EvaluationScorecard,
        regression: RegressionReport | None = None,
    ) -> str:
        """Export as machine-readable JSON string."""
        payload: dict[str, Any] = {
            "evaluation_run_id": scorecard.evaluation_run_id,
            "dataset_version": scorecard.dataset_version,
            "timestamp": scorecard.created_at.isoformat(),
            "total_cases": scorecard.total_cases,
            "successful_cases": scorecard.successful_cases,
            "composite_score": scorecard.composite_score,
            "metrics": {
                "retrieval": asdict(scorecard.retrieval),
                "evidence": asdict(scorecard.evidence),
                "fact_extraction": asdict(scorecard.fact_extraction),
                "numerical_reasoning": asdict(scorecard.numerical_reasoning),
                "citations": asdict(scorecard.citations),
                "grounding": asdict(scorecard.grounding),
                "answer": asdict(scorecard.answer),
                "security": asdict(scorecard.security),
                "latency": asdict(scorecard.latency),
                "cost": asdict(scorecard.cost),
            },
            "failures": [
                {
                    "case_id": f.case_id,
                    "first_failed_stage": f.first_failed_stage.value,
                    "error_type": f.error_type,
                    "severity": f.severity.value,
                    "details": f.details,
                    "recommendation": f.recommendation,
                }
                for f in scorecard.failures
            ],
            "metadata": scorecard.metadata,
        }

        if regression:
            payload["regression_audit"] = {
                "baseline_id": regression.baseline_id,
                "has_regressions": regression.has_regressions,
                "regressions": [
                    {
                        "metric": r.metric_name,
                        "baseline": r.baseline_value,
                        "current": r.current_value,
                        "delta": r.delta,
                        "severity": r.severity.value,
                        "details": r.details,
                    }
                    for r in regression.regressions
                ],
            }

        return json.dumps(payload, indent=2, default=str)

    def format_markdown(
        self,
        scorecard: EvaluationScorecard,
        regression: RegressionReport | None = None,
    ) -> str:
        """Format as comprehensive human-readable Markdown report."""
        lines = [
            "# Financial RAG Evaluation Scorecard & Quality Report",
            "",
            f"**Evaluation Run ID**: `{scorecard.evaluation_run_id}`  ",
            f"**Dataset Version**: `{scorecard.dataset_version}`  ",
            f"**Total Cases**: `{scorecard.total_cases}` (Successful: `{scorecard.successful_cases}`)  ",
            f"**Composite Score**: `{scorecard.composite_score:.4f}`  ",
            f"**Timestamp**: `{scorecard.created_at.isoformat()}`  ",
            "",
            "---",
            "",
            "## 1. Quality Dimensions Scorecard",
            "",
            "| Layer | Key Metric | Score | Status |",
            "|---|---|:---:|:---:|",
            f"| **Retrieval** | Recall@10 | `{scorecard.retrieval.recall_at_10:.4f}` | {'✅ PASS' if scorecard.retrieval.recall_at_10 >= 0.85 else '⚠️ WARN'} |",
            f"| **Retrieval** | MRR | `{scorecard.retrieval.mrr:.4f}` | {'✅ PASS' if scorecard.retrieval.mrr >= 0.70 else '⚠️ WARN'} |",
            f"| **Retrieval** | MAP | `{scorecard.retrieval.map_score:.4f}` | {'✅ PASS' if scorecard.retrieval.map_score >= 0.70 else '⚠️ WARN'} |",
            f"| **Evidence** | Evidence Recall | `{scorecard.evidence.evidence_recall:.4f}` | {'✅ PASS' if scorecard.evidence.evidence_recall >= 0.90 else '⚠️ WARN'} |",
            f"| **Evidence** | Required Source Coverage | `{scorecard.evidence.required_source_coverage:.4f}` | {'✅ PASS' if scorecard.evidence.required_source_coverage >= 0.90 else '⚠️ WARN'} |",
            f"| **Fact Extraction** | Exact Match / F1 | `{scorecard.fact_extraction.f1:.4f}` | {'✅ PASS' if scorecard.fact_extraction.f1 >= 0.90 else '⚠️ WARN'} |",
            f"| **Reasoning** | Calculation Accuracy | `{scorecard.numerical_reasoning.calculation_accuracy:.4f}` | {'✅ PASS' if scorecard.numerical_reasoning.calculation_accuracy >= 0.99 else '❌ FAIL'} |",
            f"| **Citations** | Citation Precision | `{scorecard.citations.citation_precision:.4f}` | {'✅ PASS' if scorecard.citations.citation_precision >= 0.90 else '⚠️ WARN'} |",
            f"| **Citations** | Citation Recall | `{scorecard.citations.citation_recall:.4f}` | {'✅ PASS' if scorecard.citations.citation_recall >= 0.90 else '⚠️ WARN'} |",
            f"| **Grounding** | Grounded Answer Rate | `{scorecard.grounding.grounded_answer_rate:.4f}` | {'✅ PASS' if scorecard.grounding.grounded_answer_rate >= 0.90 else '❌ FAIL'} |",
            f"| **Grounding** | Unsupported Claim Rate | `{scorecard.grounding.unsupported_claim_rate:.4f}` | {'✅ PASS' if scorecard.grounding.unsupported_claim_rate <= 0.05 else '⚠️ WARN'} |",
            f"| **Answer Quality** | Factual Faithfulness | `{scorecard.answer.faithfulness_score:.4f}` | {'✅ PASS' if scorecard.answer.faithfulness_score >= 0.95 else '⚠️ WARN'} |",
            f"| **Answer Quality** | Refusal Correctness | `{scorecard.answer.refusal_correctness_score:.4f}` | {'✅ PASS' if scorecard.answer.refusal_correctness_score >= 0.95 else '⚠️ WARN'} |",
            f"| **Security** | Prompt Injection Resistance | `{scorecard.security.prompt_injection_resistance_rate:.4f}` | {'✅ PASS' if scorecard.security.prompt_injection_resistance_rate >= 0.99 else '❌ FAIL'} |",
            f"| **Security** | Tenant Isolation Violation Rate | `{scorecard.security.tenant_isolation_violation_rate:.4f}` | {'✅ PASS' if scorecard.security.tenant_isolation_violation_rate == 0.0 else '❌ FAIL'} |",
            "",
            "---",
            "",
            "## 2. Operational & Latency Metrics",
            "",
            f"- **P50 Latency**: `{scorecard.latency.p50_ms:.2f} ms`",
            f"- **P95 Latency**: `{scorecard.latency.p95_ms:.2f} ms`",
            f"- **P99 Latency**: `{scorecard.latency.p99_ms:.2f} ms`",
            f"- **Total LLM Tokens**: `{scorecard.cost.total_tokens}` (Input: `{scorecard.cost.total_input_tokens}`, Output: `{scorecard.cost.total_output_tokens}`)",
            f"- **Total Estimated Cost**: `${scorecard.cost.total_estimated_cost_usd:.6f}` (${scorecard.cost.cost_per_query_usd:.6f}/query)",
            "",
        ]

        if scorecard.failures:
            lines.extend(
                [
                    "---",
                    "",
                    "## 3. Pipeline Failure Attribution & Diagnostics",
                    "",
                    "| Case ID | Failed Stage | Error Type | Severity | Details |",
                    "|---|:---:|:---:|:---:|---|",
                ]
            )
            for f in scorecard.failures:
                sev_badge = "🔴 CRITICAL" if f.severity.value == "CRITICAL" else "🟡 WARNING"
                lines.append(
                    f"| `{f.case_id}` | **{f.first_failed_stage.value}** | `{f.error_type}` | {sev_badge} | {f.details} |"
                )
            lines.append("")

        if regression:
            lines.extend(
                [
                    "---",
                    "",
                    f"## 4. Regression Audit (vs Baseline `{regression.baseline_id}`)",
                    "",
                ]
            )
            if not regression.has_regressions:
                lines.append(
                    "🎉 **No regressions detected against baseline.** All metrics met or exceeded thresholds."
                )
            else:
                lines.extend(
                    [
                        "| Metric | Baseline | Current | Delta | Severity | Details |",
                        "|---|:---:|:---:|:---:|:---:|---|",
                    ]
                )
                for r in regression.regressions:
                    sev_badge = "🔴 CRITICAL" if r.severity.value == "CRITICAL" else "🟡 WARNING"
                    lines.append(
                        f"| **{r.metric_name}** | `{r.baseline_value}` | `{r.current_value}` | `{r.delta:+.4f}` | {sev_badge} | {r.details} |"
                    )

        return "\n".join(lines)

    def format_csv(self, scorecard: EvaluationScorecard) -> str:
        """Format metrics as flat CSV table."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric Group", "Metric Name", "Value"])

        writer.writerow(["Retrieval", "Recall@10", scorecard.retrieval.recall_at_10])
        writer.writerow(["Retrieval", "Precision@10", scorecard.retrieval.precision_at_10])
        writer.writerow(["Retrieval", "MRR", scorecard.retrieval.mrr])
        writer.writerow(["Retrieval", "MAP", scorecard.retrieval.map_score])
        writer.writerow(["Retrieval", "NDCG@10", scorecard.retrieval.ndcg_at_10])
        writer.writerow(["Evidence", "Evidence Recall", scorecard.evidence.evidence_recall])
        writer.writerow(
            ["Evidence", "Source Coverage", scorecard.evidence.required_source_coverage]
        )
        writer.writerow(
            [
                "Reasoning",
                "Calculation Accuracy",
                scorecard.numerical_reasoning.calculation_accuracy,
            ]
        )
        writer.writerow(["Citations", "Citation Precision", scorecard.citations.citation_precision])
        writer.writerow(["Citations", "Citation Recall", scorecard.citations.citation_recall])
        writer.writerow(
            ["Grounding", "Grounded Answer Rate", scorecard.grounding.grounded_answer_rate]
        )
        writer.writerow(["Answer", "Faithfulness Score", scorecard.answer.faithfulness_score])
        writer.writerow(
            ["Answer", "Refusal Correctness", scorecard.answer.refusal_correctness_score]
        )
        writer.writerow(
            [
                "Security",
                "Prompt Injection Resistance",
                scorecard.security.prompt_injection_resistance_rate,
            ]
        )
        writer.writerow(
            [
                "Security",
                "Tenant Isolation Violations",
                scorecard.security.tenant_isolation_violation_rate,
            ]
        )
        writer.writerow(["Performance", "P50 Latency (ms)", scorecard.latency.p50_ms])
        writer.writerow(["Performance", "P95 Latency (ms)", scorecard.latency.p95_ms])
        writer.writerow(["Cost", "Total Tokens", scorecard.cost.total_tokens])
        writer.writerow(["Cost", "Estimated Cost USD", scorecard.cost.total_estimated_cost_usd])

        return output.getvalue()

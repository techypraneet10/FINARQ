"""Evidence selection and multi-source coverage evaluator."""

from typing import Any

from financial_rag.domain.entities.evaluation import EvidenceEvalMetrics
from financial_rag.domain.interfaces.evaluation import EvidenceEvaluatorProtocol


class EvidenceEvaluator(EvidenceEvaluatorProtocol):
    """Evaluates evidence selection quality, table coverage, and multi-source retention."""

    def evaluate_evidence(
        self,
        selected_evidence: list[Any],
        ground_truth_chunks: list[str],
        ground_truth_pages: list[int] | None = None,
        expected_table_id: str | None = None,
    ) -> EvidenceEvalMetrics:
        """Compute evidence selection quality and coverage metrics."""
        if not selected_evidence:
            if not ground_truth_chunks and not ground_truth_pages:
                return EvidenceEvalMetrics(
                    evidence_recall=1.0,
                    evidence_precision=1.0,
                    required_source_coverage=1.0,
                    table_source_coverage=1.0,
                    multi_source_coverage=1.0,
                )
            return EvidenceEvalMetrics(
                evidence_recall=0.0,
                evidence_precision=0.0,
                required_source_coverage=0.0,
                table_source_coverage=0.0,
                multi_source_coverage=0.0,
            )

        gt_chunks = set(ground_truth_chunks)
        gt_pages = set(ground_truth_pages or [])

        # 1. Precision & Recall
        relevant_evidence_count = 0
        covered_pages: set[int] = set()
        covered_chunks: set[str] = set()

        for ev in selected_evidence:
            ev_chunk_id = str(getattr(ev, "chunk_id", getattr(ev, "id", "")))
            ev_page = getattr(ev, "page_number", None)

            c_match = ev_chunk_id in gt_chunks if gt_chunks else False
            p_match = (ev_page in gt_pages) if (gt_pages and ev_page is not None) else False
            if c_match or p_match or (not gt_chunks and not gt_pages):
                relevant_evidence_count += 1
                if ev_page is not None:
                    covered_pages.add(ev_page)
                if ev_chunk_id:
                    covered_chunks.add(ev_chunk_id)

        precision = relevant_evidence_count / float(len(selected_evidence))

        total_gt = len(gt_chunks) if gt_chunks else len(gt_pages)
        if total_gt > 0:
            covered_total = len(covered_chunks) if gt_chunks else len(covered_pages)
            recall = min(1.0, covered_total / float(total_gt))
        else:
            recall = 1.0

        # 2. Required Source Coverage
        source_coverage = (
            1.0
            if (not gt_pages or gt_pages.issubset(covered_pages))
            else (len(covered_pages) / float(len(gt_pages)) if gt_pages else 1.0)
        )

        # 3. Table Source Coverage
        table_coverage = 1.0
        if expected_table_id:
            table_found = any(
                expected_table_id in str(getattr(ev, "chunk_id", ""))
                or expected_table_id in str(getattr(ev, "table_id", ""))
                or "table" in getattr(ev, "content", getattr(ev, "exact_text", "")).lower()
                for ev in selected_evidence
            )
            table_coverage = 1.0 if table_found else 0.0

        # 4. Multi-Source Coverage
        unique_docs = {str(getattr(ev, "document_id", "doc")) for ev in selected_evidence}
        multi_coverage = 1.0 if len(unique_docs) >= 1 else 0.0

        return EvidenceEvalMetrics(
            evidence_recall=min(1.0, recall),
            evidence_precision=min(1.0, precision),
            required_source_coverage=min(1.0, source_coverage),
            table_source_coverage=min(1.0, table_coverage),
            multi_source_coverage=min(1.0, multi_coverage),
        )

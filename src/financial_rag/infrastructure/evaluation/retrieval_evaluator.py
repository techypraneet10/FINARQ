"""Retrieval quality evaluation, metrics calculation, and ablation comparison."""

import math

from financial_rag.domain.entities.evaluation import RetrievalEvalMetrics
from financial_rag.domain.entities.models import RetrievalResult
from financial_rag.domain.interfaces.evaluation import RetrievalEvaluatorProtocol


class RetrievalEvaluator(RetrievalEvaluatorProtocol):
    """Evaluates retrieval quality across Recall@K, Precision@K, HitRate@K, MRR, and NDCG@K."""

    def evaluate_retrieval(
        self,
        retrieved_items: list[RetrievalResult],
        ground_truth_chunks: list[str],
        ground_truth_pages: list[int] | None = None,
        strategy: str = "hybrid",
        latency_ms: float = 0.0,
    ) -> RetrievalEvalMetrics:
        """Compute retrieval metrics for candidate list against target chunk/page ground truth."""
        retrieved_chunk_ids = [str(r.chunk.id) for r in retrieved_items]
        retrieved_page_numbers = [r.chunk.page_number for r in retrieved_items]

        # Consider an item relevant if chunk_id matches OR page_number matches when ground_truth_pages provided
        gt_chunks_set = set(ground_truth_chunks)
        gt_pages_set = set(ground_truth_pages or [])

        def is_relevant(idx: int) -> bool:
            if idx >= len(retrieved_items):
                return False
            c_id = retrieved_chunk_ids[idx]
            p_num = retrieved_page_numbers[idx]
            if c_id in gt_chunks_set:
                return True
            return bool(gt_pages_set and p_num in gt_pages_set)

        # Compute MRR
        mrr = 0.0
        for rank_idx in range(len(retrieved_items)):
            if is_relevant(rank_idx):
                mrr = 1.0 / float(rank_idx + 1)
                break

        # Compute Recall, Precision, HitRate at K in [1, 3, 5, 10]
        total_gt = max(1, len(gt_chunks_set) if gt_chunks_set else len(gt_pages_set))

        def calc_k_metrics(k: int) -> tuple[float, float, float]:
            if not retrieved_items or k <= 0:
                return 0.0, 0.0, 0.0
            top_k_indices = range(min(k, len(retrieved_items)))
            relevant_count = sum(1 for i in top_k_indices if is_relevant(i))
            recall = min(1.0, relevant_count / float(total_gt))
            precision = relevant_count / float(k)
            hit_rate = 1.0 if relevant_count > 0 else 0.0
            return recall, precision, hit_rate

        rec1, prec1, hit1 = calc_k_metrics(1)
        rec3, prec3, hit3 = calc_k_metrics(3)
        rec5, prec5, hit5 = calc_k_metrics(5)
        rec10, prec10, hit10 = calc_k_metrics(10)

        # Compute NDCG@K
        def calc_ndcg(k: int) -> float:
            if not retrieved_items or k <= 0:
                return 0.0
            dcg = 0.0
            for i in range(min(k, len(retrieved_items))):
                rel = 1.0 if is_relevant(i) else 0.0
                dcg += (math.pow(2, rel) - 1.0) / math.log2(i + 2.0)

            # Ideal DCG
            idcg = 0.0
            for i in range(min(k, total_gt)):
                idcg += (math.pow(2, 1.0) - 1.0) / math.log2(i + 2.0)

            return min(1.0, max(0.0, dcg / idcg)) if idcg > 0.0 else 0.0

        ndcg5 = calc_ndcg(5)
        ndcg10 = calc_ndcg(10)

        # Compute Average Precision (AP)
        running_relevant = 0
        ap_sum = 0.0
        for i in range(len(retrieved_items)):
            if is_relevant(i):
                running_relevant += 1
                ap_sum += running_relevant / float(i + 1)
        map_score = ap_sum / float(total_gt) if total_gt > 0 else 0.0

        return RetrievalEvalMetrics(
            recall_at_1=rec1,
            recall_at_3=rec3,
            recall_at_5=rec5,
            recall_at_10=rec10,
            precision_at_1=prec1,
            precision_at_3=prec3,
            precision_at_5=prec5,
            precision_at_10=prec10,
            hit_rate_at_1=hit1,
            hit_rate_at_3=hit3,
            hit_rate_at_5=hit5,
            hit_rate_at_10=hit10,
            mrr=mrr,
            map_score=map_score,
            ndcg_at_5=ndcg5,
            ndcg_at_10=ndcg10,
            strategy=strategy,
            mean_latency_ms=latency_ms,
        )

    def classify_retrieval_failure(
        self,
        retrieved_items: list[RetrievalResult],
        ground_truth_chunks: list[str],
        ground_truth_pages: list[int] | None = None,
    ) -> str:
        """Classify retrieval failure into standardized error taxonomy."""
        if not retrieved_items:
            return "EMPTY_RETRIEVAL_RESULTS"

        metrics = self.evaluate_retrieval(
            retrieved_items=retrieved_items,
            ground_truth_chunks=ground_truth_chunks,
            ground_truth_pages=ground_truth_pages,
            strategy="audit",
        )

        if metrics.hit_rate_at_10 == 0.0:
            return "NO_RELEVANT_CHUNK_IN_TOP_K"
        elif metrics.hit_rate_at_1 == 0.0 and metrics.hit_rate_at_10 > 0.0:
            return "LOW_RANK_RELEVANCE"
        elif metrics.recall_at_10 < 1.0:
            return "PARTIAL_RELEVANCE_RETRIEVED"
        return "NO_FAILURE"

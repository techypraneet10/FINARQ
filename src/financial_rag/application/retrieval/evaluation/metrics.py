"""Mathematical evaluation metrics for retrieval quality assessment."""

import math


def hit_rate_at_k(retrieved_ids: list[str], ground_truth_ids: set[str], k: int = 10) -> float:
    """Compute Hit Rate @ K (1.0 if at least one relevant item in top-k, else 0.0)."""
    if not retrieved_ids or not ground_truth_ids or k <= 0:
        return 0.0
    top_k_items = retrieved_ids[:k]
    return 1.0 if any(item_id in ground_truth_ids for item_id in top_k_items) else 0.0


def recall_at_k(retrieved_ids: list[str], ground_truth_ids: set[str], k: int = 10) -> float:
    """Compute Recall @ K: fraction of ground truth relevant items retrieved in top-k."""
    if not retrieved_ids or not ground_truth_ids or k <= 0:
        return 0.0
    top_k_items = set(retrieved_ids[:k])
    relevant_retrieved = top_k_items.intersection(ground_truth_ids)
    return len(relevant_retrieved) / float(len(ground_truth_ids))


def precision_at_k(retrieved_ids: list[str], ground_truth_ids: set[str], k: int = 10) -> float:
    """Compute Precision @ K: fraction of top-k retrieved items that are relevant."""
    if not retrieved_ids or not ground_truth_ids or k <= 0:
        return 0.0
    top_k_items = retrieved_ids[:k]
    relevant_retrieved = sum(1 for item in top_k_items if item in ground_truth_ids)
    return relevant_retrieved / float(k)


def mean_reciprocal_rank(retrieved_ids: list[str], ground_truth_ids: set[str]) -> float:
    """Compute Reciprocal Rank: 1.0 / rank of the first relevant retrieved item, or 0.0."""
    if not retrieved_ids or not ground_truth_ids:
        return 0.0
    for rank, item_id in enumerate(retrieved_ids, start=1):
        if item_id in ground_truth_ids:
            return 1.0 / float(rank)
    return 0.0


def ndcg_at_k(
    retrieved_ids: list[str],
    relevance_scores: dict[str, float],
    k: int = 10,
) -> float:
    """Compute Normalized Discounted Cumulative Gain @ K (NDCG@K)."""
    if not retrieved_ids or not relevance_scores or k <= 0:
        return 0.0

    top_k_items = retrieved_ids[:k]

    # Calculate Discounted Cumulative Gain (DCG)
    dcg = 0.0
    for i, item_id in enumerate(top_k_items):
        rel = relevance_scores.get(item_id, 0.0)
        # DCG formula with base 2 logarithm discounting
        dcg += (math.pow(2, rel) - 1.0) / math.log2(i + 2.0)

    # Calculate Ideal DCG (IDCG)
    ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_scores):
        idcg += (math.pow(2, rel) - 1.0) / math.log2(i + 2.0)

    if idcg <= 0.0:
        return 0.0

    return min(1.0, max(0.0, dcg / idcg))


def calculate_retrieval_metrics(
    retrieved_ids: list[str],
    ground_truth_ids: set[str],
    relevance_scores: dict[str, float] | None = None,
    k_list: list[int] | None = None,
) -> dict[str, float]:
    """Calculate comprehensive suite of retrieval metrics for a single query."""
    ks = k_list or [1, 3, 5, 10]
    rel_map = relevance_scores or dict.fromkeys(ground_truth_ids, 1.0)

    metrics: dict[str, float] = {
        "mrr": mean_reciprocal_rank(retrieved_ids, ground_truth_ids),
    }

    for k in ks:
        metrics[f"recall@{k}"] = recall_at_k(retrieved_ids, ground_truth_ids, k=k)
        metrics[f"precision@{k}"] = precision_at_k(retrieved_ids, ground_truth_ids, k=k)
        metrics[f"hit_rate@{k}"] = hit_rate_at_k(retrieved_ids, ground_truth_ids, k=k)
        metrics[f"ndcg@{k}"] = ndcg_at_k(retrieved_ids, rel_map, k=k)

    return metrics

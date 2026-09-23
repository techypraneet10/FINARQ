"""Ablation comparison evaluator measuring Dense, Sparse, Hybrid, and Reranked retrieval."""

from dataclasses import dataclass, field
from typing import Any

from financial_rag.application.retrieval.evaluation.dataset import (
    BenchmarkItem,
    get_benchmark_dataset,
    get_synthetic_financial_corpus,
)
from financial_rag.application.retrieval.evaluation.metrics import calculate_retrieval_metrics
from financial_rag.config.settings import QdrantSettings
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.domain.interfaces.retrieval import (
    DenseRetrieverProtocol,
    FusionStrategyProtocol,
    QueryAnalyzerProtocol,
    RerankerProtocol,
    SparseRetrieverProtocol,
)
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.retrieval.deduplicator import CandidateDeduplicator
from financial_rag.infrastructure.retrieval.dense_retriever import QdrantDenseRetriever
from financial_rag.infrastructure.retrieval.evidence_selector import EvidenceSelector
from financial_rag.infrastructure.retrieval.evidence_validator import EvidenceValidator
from financial_rag.infrastructure.retrieval.fusion import ReciprocalRankFusion
from financial_rag.infrastructure.retrieval.query_analyzer import FinancialQueryAnalyzer
from financial_rag.infrastructure.retrieval.reranker import MockReranker
from financial_rag.infrastructure.retrieval.sparse_retriever import BM25SparseRetriever
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter

logger = get_logger("financial_rag.application.retrieval.evaluation.evaluator")


@dataclass
class StrategyMetrics:
    """Aggregated evaluation metrics for a single retrieval strategy."""

    strategy_name: str
    mrr: float = 0.0
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_1: float = 0.0
    precision_at_3: float = 0.0
    precision_at_5: float = 0.0
    precision_at_10: float = 0.0
    ndcg_at_1: float = 0.0
    ndcg_at_3: float = 0.0
    ndcg_at_5: float = 0.0
    ndcg_at_10: float = 0.0
    hit_rate_at_1: float = 0.0
    hit_rate_at_3: float = 0.0
    hit_rate_at_5: float = 0.0
    hit_rate_at_10: float = 0.0
    per_query_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "strategy_name": self.strategy_name,
            "mrr": round(self.mrr, 4),
            "recall@1": round(self.recall_at_1, 4),
            "recall@3": round(self.recall_at_3, 4),
            "recall@5": round(self.recall_at_5, 4),
            "recall@10": round(self.recall_at_10, 4),
            "precision@1": round(self.precision_at_1, 4),
            "precision@3": round(self.precision_at_3, 4),
            "precision@5": round(self.precision_at_5, 4),
            "precision@10": round(self.precision_at_10, 4),
            "ndcg@1": round(self.ndcg_at_1, 4),
            "ndcg@3": round(self.ndcg_at_3, 4),
            "ndcg@5": round(self.ndcg_at_5, 4),
            "ndcg@10": round(self.ndcg_at_10, 4),
            "hit_rate@1": round(self.hit_rate_at_1, 4),
            "hit_rate@3": round(self.hit_rate_at_3, 4),
            "hit_rate@5": round(self.hit_rate_at_5, 4),
            "hit_rate@10": round(self.hit_rate_at_10, 4),
        }


class RetrievalBenchmarkEvaluator:
    """Orchestrates comparative retrieval evaluation across Dense, Sparse, Hybrid, and Reranked pipelines."""

    def __init__(
        self,
        query_analyzer: QueryAnalyzerProtocol | None = None,
        dense_retriever: DenseRetrieverProtocol | None = None,
        sparse_retriever: SparseRetrieverProtocol | None = None,
        fusion_strategy: FusionStrategyProtocol | None = None,
        reranker: RerankerProtocol | None = None,
        embedding_provider: EmbeddingProviderProtocol | None = None,
        vector_store: VectorStoreProtocol | None = None,
    ) -> None:
        self.analyzer = query_analyzer or FinancialQueryAnalyzer()
        self.embedder = embedding_provider or MockEmbeddingProvider(dimension=1536)
        self.vector_store = vector_store or QdrantVectorStoreAdapter(
            qdrant_settings=QdrantSettings(location=":memory:", collection_name="benchmark_chunks")
        )
        self.dense_retriever = dense_retriever or QdrantDenseRetriever(
            embedding_provider=self.embedder,
            vector_store=self.vector_store,
            expected_dimension=1536,
        )
        self.sparse_retriever = sparse_retriever or BM25SparseRetriever()
        self.fusion = fusion_strategy or ReciprocalRankFusion(default_k=60)
        self.deduplicator = CandidateDeduplicator()
        self.reranker = reranker or MockReranker()
        self.selector = EvidenceSelector()
        self.validator = EvidenceValidator()

    async def setup_corpus(self) -> int:
        """Seed synthetic financial benchmark corpus into dense and sparse stores."""
        corpus = get_synthetic_financial_corpus()

        # 1. Index in Sparse BM25
        await self.sparse_retriever.index_chunks(corpus)

        # 2. Embed and index in Dense Qdrant
        texts = [c.content for c in corpus]
        embeddings = await self.embedder.embed_batch(texts)
        await self.vector_store.upsert_chunks(chunks=corpus, embeddings=embeddings)

        logger.info(f"Initialized benchmark corpus with {len(corpus)} document chunks")
        return len(corpus)

    async def run_evaluation(
        self,
        dataset: list[BenchmarkItem] | None = None,
    ) -> dict[str, StrategyMetrics]:
        """Execute full ablation evaluation across all 4 retrieval strategies."""
        items = dataset or get_benchmark_dataset()
        num_queries = len(items)

        strategies = ["Dense Only", "Sparse Only", "Hybrid (RRF)", "Hybrid + Reranking"]
        results: dict[str, StrategyMetrics] = {
            s: StrategyMetrics(strategy_name=s) for s in strategies
        }

        for item in items:
            query = self.analyzer.analyze(raw_query=item.query_text, top_k=10)
            ground_truth = set(item.expected_chunk_ids)
            rel_grades = item.relevance_grades

            # 1. Dense Only Execution
            dense_cands = await self.dense_retriever.retrieve(query=query, top_k=10)
            dense_ids = [str(c.chunk.id) for c in dense_cands]
            dense_metrics = calculate_retrieval_metrics(dense_ids, ground_truth, rel_grades)
            self._accumulate_metrics(results["Dense Only"], dense_metrics, item.query_id)

            # 2. Sparse Only Execution
            sparse_cands = await self.sparse_retriever.retrieve(query=query, top_k=10)
            sparse_ids = [str(c.chunk.id) for c in sparse_cands]
            sparse_metrics = calculate_retrieval_metrics(sparse_ids, ground_truth, rel_grades)
            self._accumulate_metrics(results["Sparse Only"], sparse_metrics, item.query_id)

            # 3. Hybrid (Dense + Sparse with RRF)
            fused = self.fusion.fuse(dense_cands, sparse_cands, rrf_k=60)
            deduped_fused = self.deduplicator.deduplicate(fused)
            fused_evidence = self.selector.select(query=query, candidates=deduped_fused, top_k=10)
            fused_ids = [str(e.chunk_id) for e in fused_evidence]
            fused_metrics = calculate_retrieval_metrics(fused_ids, ground_truth, rel_grades)
            self._accumulate_metrics(results["Hybrid (RRF)"], fused_metrics, item.query_id)

            # 4. Hybrid + Reranking
            reranked = await self.reranker.rerank(query=query, candidates=deduped_fused, top_k=10)
            reranked_evidence = self.selector.select(query=query, candidates=reranked, top_k=10)
            reranked_ids = [str(e.chunk_id) for e in reranked_evidence]
            reranked_metrics = calculate_retrieval_metrics(reranked_ids, ground_truth, rel_grades)
            self._accumulate_metrics(results["Hybrid + Reranking"], reranked_metrics, item.query_id)

        # Average metrics across all queries
        for strat in results.values():
            strat.mrr /= num_queries
            strat.recall_at_1 /= num_queries
            strat.recall_at_3 /= num_queries
            strat.recall_at_5 /= num_queries
            strat.recall_at_10 /= num_queries
            strat.precision_at_1 /= num_queries
            strat.precision_at_3 /= num_queries
            strat.precision_at_5 /= num_queries
            strat.precision_at_10 /= num_queries
            strat.ndcg_at_1 /= num_queries
            strat.ndcg_at_3 /= num_queries
            strat.ndcg_at_5 /= num_queries
            strat.ndcg_at_10 /= num_queries
            strat.hit_rate_at_1 /= num_queries
            strat.hit_rate_at_3 /= num_queries
            strat.hit_rate_at_5 /= num_queries
            strat.hit_rate_at_10 /= num_queries

        return results

    def _accumulate_metrics(
        self,
        strat: StrategyMetrics,
        metrics: dict[str, float],
        query_id: str,
    ) -> None:
        """Accumulate per-query metrics into strategy totals."""
        strat.mrr += metrics.get("mrr", 0.0)
        strat.recall_at_1 += metrics.get("recall@1", 0.0)
        strat.recall_at_3 += metrics.get("recall@3", 0.0)
        strat.recall_at_5 += metrics.get("recall@5", 0.0)
        strat.recall_at_10 += metrics.get("recall@10", 0.0)
        strat.precision_at_1 += metrics.get("precision@1", 0.0)
        strat.precision_at_3 += metrics.get("precision@3", 0.0)
        strat.precision_at_5 += metrics.get("precision@5", 0.0)
        strat.precision_at_10 += metrics.get("precision@10", 0.0)
        strat.ndcg_at_1 += metrics.get("ndcg@1", 0.0)
        strat.ndcg_at_3 += metrics.get("ndcg@3", 0.0)
        strat.ndcg_at_5 += metrics.get("ndcg@5", 0.0)
        strat.ndcg_at_10 += metrics.get("ndcg@10", 0.0)
        strat.hit_rate_at_1 += metrics.get("hit_rate@1", 0.0)
        strat.hit_rate_at_3 += metrics.get("hit_rate@3", 0.0)
        strat.hit_rate_at_5 += metrics.get("hit_rate@5", 0.0)
        strat.hit_rate_at_10 += metrics.get("hit_rate@10", 0.0)
        strat.per_query_results.append({"query_id": query_id, **metrics})

    def format_ablation_markdown_table(self, results: dict[str, StrategyMetrics]) -> str:
        """Format ablation evaluation results into clean GitHub-flavored markdown table."""
        header = (
            "| Retrieval Strategy | MRR | Recall@1 | Recall@3 | Recall@5 | Recall@10 | NDCG@5 | NDCG@10 |\n"
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        )
        rows = []
        for name, m in results.items():
            row = (
                f"| **{name}** | {m.mrr:.4f} | {m.recall_at_1:.4f} | {m.recall_at_3:.4f} | "
                f"{m.recall_at_5:.4f} | {m.recall_at_10:.4f} | {m.ndcg_at_5:.4f} | {m.ndcg_at_10:.4f} |"
            )
            rows.append(row)
        return header + "\n".join(rows)

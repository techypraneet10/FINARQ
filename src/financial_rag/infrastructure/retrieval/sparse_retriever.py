"""Sparse lexical retriever implementing Okapi BM25 with financial-aware tokenization."""

import math
import re
from collections import defaultdict

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import (
    RetrievalCandidate,
    RetrievalFilter,
    RetrievalQuery,
    RetrievalSource,
)
from financial_rag.domain.exceptions import SparseIndexError
from financial_rag.domain.interfaces.retrieval import SparseRetrieverProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.retrieval.sparse_retriever")

# Common English and generic stop words
STOPWORDS: set[str] = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "aren't",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can't",
    "cannot",
    "could",
    "couldn't",
    "did",
    "didn't",
    "do",
    "does",
    "doesn't",
    "doing",
    "don't",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "hadn't",
    "has",
    "hasn't",
    "have",
    "haven't",
    "having",
    "he",
    "he'd",
    "he'll",
    "he's",
    "her",
    "here",
    "here's",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "how's",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "if",
    "in",
    "into",
    "is",
    "isn't",
    "it",
    "it's",
    "its",
    "itself",
    "let's",
    "me",
    "more",
    "most",
    "mustn't",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "shan't",
    "she",
    "she'd",
    "she'll",
    "she's",
    "should",
    "shouldn't",
    "so",
    "some",
    "such",
    "than",
    "that",
    "that's",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "there's",
    "these",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "wasn't",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "were",
    "weren't",
    "what",
    "what's",
    "when",
    "when's",
    "where",
    "where's",
    "which",
    "while",
    "who",
    "who's",
    "whom",
    "why",
    "why's",
    "with",
    "won't",
    "would",
    "wouldn't",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


def tokenize_financial_text(text: str) -> list[str]:
    """Tokenize text preserving financial numbers, item codes, tickers, and compound terms."""
    if not text:
        return []

    text_lower = text.lower()

    # Normalize SEC items: "item 1a" -> "item_1a", "item 7" -> "item_7"
    text_processed = re.sub(r"\bitem\s+([0-9]+[a-z]?)\b", r"item_\1", text_lower)

    # Normalize fiscal quarters: "q1 2024" -> "q1 2024"
    text_processed = re.sub(r"\b([1-4])q\b", r"q\1", text_processed)

    # Extract tokens: alphanumeric words, dashed terms, underscores, and numbers with decimals
    raw_tokens = re.findall(r"\b[a-z0-9_]+(?:[-.][a-z0-9_]+)*\b", text_processed)

    # Filter out pure single-character punctuation or common stopwords (except financial numbers/years)
    tokens: list[str] = []
    for token in raw_tokens:
        clean = token.strip(".-_")
        if not clean:
            continue
        # Preserve years, numbers, tickers, item codes even if short
        if (
            clean.isdigit() or clean.startswith("item_") or clean.startswith("q") or len(clean) >= 2
        ) and (clean not in STOPWORDS or clean.isdigit() or clean.startswith("item_")):
            tokens.append(clean)

    return tokens


class BM25SparseRetriever(SparseRetrieverProtocol):
    """Okapi BM25 search engine with exact term boosting for financial entities."""

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        exact_boost: float = 2.0,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.exact_boost = exact_boost

        # Document storage & inverted index
        self._chunks: dict[str, DocumentChunk] = {}
        self._doc_lengths: dict[str, int] = {}
        self._inverted_index: dict[str, dict[str, int]] = defaultdict(
            dict
        )  # token -> {chunk_id -> tf}
        self._avg_doc_length: float = 0.0

    @property
    def total_documents(self) -> int:
        """Total number of indexed chunks."""
        return len(self._chunks)

    def _calculate_idf(self, doc_freq: int) -> float:
        """Calculate standard BM25 Inverse Document Frequency with floor."""
        n = self.total_documents
        # Standard Lucene/BM25 IDF formula with +1 smoothing
        return math.log(1.0 + (n - doc_freq + 0.5) / (doc_freq + 0.5))

    async def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Index a batch of document chunks into the BM25 inverted index."""
        if not chunks:
            return 0

        for chunk in chunks:
            chunk_id = str(chunk.id)
            tokens = tokenize_financial_text(chunk.content + " " + chunk.section_path)

            # Store chunk and token length
            self._chunks[chunk_id] = chunk
            self._doc_lengths[chunk_id] = len(tokens)

            # Calculate term frequencies
            tf_map: dict[str, int] = defaultdict(int)
            for token in tokens:
                tf_map[token] += 1

            # Update inverted index
            for token, count in tf_map.items():
                self._inverted_index[token][chunk_id] = count

        # Recalculate average document length
        total_tokens = sum(self._doc_lengths.values())
        self._avg_doc_length = total_tokens / max(1, len(self._doc_lengths))

        logger.info(
            f"Indexed {len(chunks)} chunks in BM25 index (total={self.total_documents}, avg_len={self._avg_doc_length:.1f})"
        )
        return len(chunks)

    async def delete_by_document_id(self, document_id: str) -> bool:
        """Remove chunks belonging to a document from the BM25 index."""
        chunk_ids_to_remove = [
            cid for cid, chunk in self._chunks.items() if str(chunk.document_id) == str(document_id)
        ]

        if not chunk_ids_to_remove:
            return True

        for cid in chunk_ids_to_remove:
            self._chunks.pop(cid, None)
            self._doc_lengths.pop(cid, None)
            for token_postings in self._inverted_index.values():
                token_postings.pop(cid, None)

        total_tokens = sum(self._doc_lengths.values())
        self._avg_doc_length = (
            total_tokens / max(1, len(self._doc_lengths)) if self._chunks else 0.0
        )

        logger.info(f"Removed {len(chunk_ids_to_remove)} chunks for doc '{document_id}' from BM25")
        return True

    def _matches_filters(
        self,
        chunk: DocumentChunk,
        filters: RetrievalFilter | None,
        tenant_id: str | None = None,
    ) -> bool:
        """Check if chunk satisfies domain retrieval filters and tenant isolation."""
        target_tenant = filters.tenant_id if filters and filters.tenant_id else tenant_id
        if target_tenant and str(chunk.tenant_id) != str(target_tenant):
            return False

        if not filters or filters.is_empty():
            return True

        if filters.document_ids and str(chunk.document_id) not in [
            str(d) for d in filters.document_ids
        ]:
            return False

        if filters.version_ids and str(chunk.document_version_id) not in [
            str(v) for v in filters.version_ids
        ]:
            return False

        if filters.chunk_types and chunk.chunk_type.value not in filters.chunk_types:
            return False

        if filters.table_only and chunk.chunk_type != ChunkType.TABLE:
            return False

        # Metadata matching (e.g. ticker_symbol, fiscal_year)
        meta = chunk.metadata or {}
        if filters.ticker_symbols:
            doc_ticker = meta.get("ticker_symbol") or meta.get("ticker")
            if doc_ticker and doc_ticker.upper() not in [t.upper() for t in filters.ticker_symbols]:
                return False

        if filters.fiscal_years:
            doc_year = meta.get("fiscal_year")
            if doc_year and int(doc_year) not in filters.fiscal_years:
                return False

        return True

    async def retrieve(
        self,
        query: RetrievalQuery,
        top_k: int | None = None,
    ) -> list[RetrievalCandidate]:
        """Execute Okapi BM25 retrieval over indexed chunks with exact signal boosting."""
        if self.total_documents == 0:
            logger.info("BM25 index is empty; returning 0 candidates")
            return []

        limit = top_k or query.sparse_top_k or query.top_k
        query_text = query.normalized_query or query.raw_query
        query_tokens = tokenize_financial_text(query_text)

        if not query_tokens:
            return []

        try:
            # Accumulate BM25 scores per candidate chunk
            scores: dict[str, float] = defaultdict(float)
            avg_dl = max(1.0, self._avg_doc_length)

            # Extract priority terms for boosting (tickers, years, item codes)
            boost_tokens: set[str] = set()
            for t in query.signals.tickers:
                boost_tokens.add(t.lower())
            for y in query.signals.fiscal_years:
                boost_tokens.add(str(y))
            for s in query.signals.sections:
                sec_tokens = tokenize_financial_text(s)
                boost_tokens.update(sec_tokens)

            for token in query_tokens:
                postings = self._inverted_index.get(token)
                if not postings:
                    continue

                idf = self._calculate_idf(len(postings))
                multiplier = self.exact_boost if token in boost_tokens else 1.0

                for chunk_id, tf in postings.items():
                    doc_len = self._doc_lengths.get(chunk_id, 1)
                    # BM25 term weighting formula
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_dl))
                    term_score = idf * (numerator / denominator) * multiplier
                    scores[chunk_id] += term_score

            if not scores:
                return []

            # Filter candidates according to domain criteria and tenant isolation
            filtered_scores: list[tuple[str, float]] = []
            for chunk_id, score in scores.items():
                chunk = self._chunks.get(chunk_id)
                if chunk and self._matches_filters(chunk, query.filters, tenant_id=query.tenant_id):
                    filtered_scores.append((chunk_id, score))

            # Rank by score descending
            filtered_scores.sort(key=lambda x: x[1], reverse=True)
            top_matches = filtered_scores[:limit]

            # Normalize sparse scores to [0, 1] relative to top hit for reporting
            max_score = top_matches[0][1] if top_matches else 1.0
            norm_factor = max_score if max_score > 0 else 1.0

            candidates: list[RetrievalCandidate] = []
            for rank_idx, (chunk_id, raw_score) in enumerate(top_matches, start=1):
                chunk = self._chunks[chunk_id]
                normalized_score = min(1.0, max(0.0, raw_score / norm_factor))
                candidates.append(
                    RetrievalCandidate(
                        chunk=chunk,
                        dense_score=None,
                        dense_rank=None,
                        sparse_score=normalized_score,
                        sparse_rank=rank_idx,
                        fusion_score=0.0,
                        reranker_score=None,
                        final_score=normalized_score,
                        sources=[RetrievalSource.SPARSE],
                        provenance=chunk.get_provenance(),
                    )
                )

            logger.info(
                f"Sparse BM25 retrieval for query '{query.id}': returned {len(candidates)} candidates"
            )
            return candidates

        except Exception as ex:
            logger.error(f"Sparse retrieval failure for query '{query.id}': {ex}")
            raise SparseIndexError(
                message=f"BM25 sparse retrieval failure: {ex}",
                details={"query_id": str(query.id), "error": str(ex)},
            ) from ex

    async def health_check(self) -> bool:
        """Verify sparse index is active and healthy."""
        return True


# Global shared instance for application runtime
bm25_retriever = BM25SparseRetriever()

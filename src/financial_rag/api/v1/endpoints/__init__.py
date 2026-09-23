from financial_rag.api.v1.endpoints.answers import router as answers_router
from financial_rag.api.v1.endpoints.documents import router as documents_router
from financial_rag.api.v1.endpoints.health import router as health_router
from financial_rag.api.v1.endpoints.ingestion_jobs import router as ingestion_jobs_router
from financial_rag.api.v1.endpoints.ready import router as ready_router
from financial_rag.api.v1.endpoints.reasoning import router as reasoning_router
from financial_rag.api.v1.endpoints.retrieval import router as retrieval_router
from financial_rag.api.v1.endpoints.version import router as version_router

__all__ = [
    "answers_router",
    "documents_router",
    "health_router",
    "ingestion_jobs_router",
    "ready_router",
    "reasoning_router",
    "retrieval_router",
    "version_router",
]

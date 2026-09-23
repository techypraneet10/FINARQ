from fastapi import APIRouter

from financial_rag.api.v1.endpoints.answers import router as answers_router
from financial_rag.api.v1.endpoints.audit import router as audit_router
from financial_rag.api.v1.endpoints.auth import router as auth_router
from financial_rag.api.v1.endpoints.documents import router as documents_router
from financial_rag.api.v1.endpoints.health import router as health_router
from financial_rag.api.v1.endpoints.ingestion_jobs import router as ingestion_jobs_router
from financial_rag.api.v1.endpoints.metrics import router as metrics_router
from financial_rag.api.v1.endpoints.ready import router as ready_router
from financial_rag.api.v1.endpoints.reasoning import router as reasoning_router
from financial_rag.api.v1.endpoints.retrieval import (
    router as retrieval_router,
)
from financial_rag.api.v1.endpoints.retrieval import (
    search_router,
)
from financial_rag.api.v1.endpoints.users import router as users_router
from financial_rag.api.v1.endpoints.version import router as version_router

v1_router = APIRouter(prefix="/api/v1")

# Mount endpoints under /api/v1
v1_router.include_router(health_router)
v1_router.include_router(ready_router)
v1_router.include_router(version_router)
v1_router.include_router(metrics_router)
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(audit_router)
v1_router.include_router(documents_router)
v1_router.include_router(ingestion_jobs_router)
v1_router.include_router(retrieval_router)
v1_router.include_router(search_router)
v1_router.include_router(reasoning_router)
v1_router.include_router(answers_router)

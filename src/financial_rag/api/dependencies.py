"""FastAPI dependency injection providers."""

import logging
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from financial_rag.application.answer.service import AnswerOrchestrationService
from financial_rag.application.ingestion.pipelines import IngestionPipeline
from financial_rag.application.ingestion.service import DocumentIngestionService
from financial_rag.application.ingestion.validator import DocumentValidator
from financial_rag.application.reasoning.service import ReasoningService
from financial_rag.application.retrieval.service import RetrievalService
from financial_rag.config.settings import Settings, get_settings
from financial_rag.domain.entities.security import (
    ROLE_PERMISSIONS,
    Permission,
    PrincipalContext,
    TenantStatus,
    UserRole,
    UserStatus,
)
from financial_rag.domain.exceptions import SecurityError
from financial_rag.domain.interfaces.answer import (
    AnswerabilityGateProtocol,
    AnswerCacheProtocol,
    AnswerOrchestratorServiceProtocol,
    AnswerValidatorProtocol,
    ContextBuilderProtocol,
    PromptBuilderProtocol,
    ResponseRendererProtocol,
)
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.domain.interfaces.llm import LLMProviderProtocol
from financial_rag.domain.interfaces.reasoning import (
    AnswerabilityEvaluatorProtocol,
    CitationGeneratorProtocol,
    CitationValidatorProtocol,
    ClaimBuilderProtocol,
    ConflictDetectorProtocol,
    FactExtractorProtocol,
    FinancialCalculatorProtocol,
    FinancialValueParserProtocol,
    GroundingValidatorProtocol,
    PeriodNormalizerProtocol,
    ReasoningPlannerProtocol,
    ReasoningServiceProtocol,
)
from financial_rag.domain.interfaces.repository import (
    ChunkRepositoryProtocol,
    DocumentPageRepositoryProtocol,
    DocumentRepositoryProtocol,
    DocumentVersionRepositoryProtocol,
    IngestionJobRepositoryProtocol,
)
from financial_rag.domain.interfaces.retrieval import (
    CandidateDeduplicatorProtocol,
    DenseRetrieverProtocol,
    EvidenceSelectorProtocol,
    EvidenceValidatorProtocol,
    FusionStrategyProtocol,
    QueryAnalyzerProtocol,
    RerankerProtocol,
    RetrievalServiceProtocol,
    SparseRetrieverProtocol,
)
from financial_rag.domain.interfaces.security import (
    AuditEventRepositoryProtocol,
    AuditLoggerProtocol,
    AuthorizationServiceProtocol,
    PasswordHasherProtocol,
    RefreshTokenRepositoryProtocol,
    TenantRepositoryProtocol,
    TokenManagerProtocol,
    UserRepositoryProtocol,
)
from financial_rag.domain.interfaces.storage import ObjectStorageProtocol
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol
from financial_rag.infrastructure.chunking.structure_aware import StructureAwareChunker
from financial_rag.infrastructure.embeddings import get_embedding_provider
from financial_rag.infrastructure.llm import (
    DeterministicAnswerabilityGate,
    DeterministicAnswerValidator,
    DeterministicContextBuilder,
    DeterministicResponseRenderer,
    InMemoryAnswerCache,
    VersionedPromptBuilder,
    create_llm_provider,
)
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.normalization.document_normalizer import DocumentNormalizer
from financial_rag.infrastructure.parsing.pdf_parser import PyMuPDFParser
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager, db_manager
from financial_rag.infrastructure.persistence.repositories import (
    PostgresAuditEventRepository,
    PostgresDocumentChunkRepository,
    PostgresDocumentPageRepository,
    PostgresDocumentRepository,
    PostgresDocumentVersionRepository,
    PostgresIngestionJobRepository,
    PostgresRefreshTokenRepository,
    PostgresTenantRepository,
    PostgresUserRepository,
)
from financial_rag.infrastructure.reasoning import (
    DeterministicAnswerabilityEvaluator,
    DeterministicCitationGenerator,
    DeterministicCitationValidator,
    DeterministicClaimBuilder,
    DeterministicConflictDetector,
    DeterministicFactExtractor,
    DeterministicFinancialCalculator,
    DeterministicGroundingValidator,
    DeterministicReasoningPlanner,
    FinancialValueParser,
    FiscalPeriodNormalizer,
)
from financial_rag.infrastructure.retrieval import (
    CandidateDeduplicator,
    CrossEncoderReranker,
    EvidenceSelector,
    EvidenceValidator,
    FinancialQueryAnalyzer,
    MockReranker,
    QdrantDenseRetriever,
    ReciprocalRankFusion,
)
from financial_rag.infrastructure.retrieval.sparse_retriever import bm25_retriever
from financial_rag.infrastructure.security.audit import AuditService
from financial_rag.infrastructure.security.authorization import RbacAuthorizationService
from financial_rag.infrastructure.security.hasher import ScryptPasswordHasher
from financial_rag.infrastructure.security.jwt import JwtTokenManager
from financial_rag.infrastructure.storage import get_storage_adapter
from financial_rag.infrastructure.structure.detector import FinancialStructureDetector
from financial_rag.infrastructure.table.extractor import FinancialTableExtractor
from financial_rag.infrastructure.table.normalizer import FinancialTableNormalizer
from financial_rag.infrastructure.vector_store import get_vector_store


def get_current_settings(request: Request) -> Settings:
    """Dependency provider returning application settings from app state or fallback cache."""
    if hasattr(request.app.state, "settings"):
        settings = request.app.state.settings
        if isinstance(settings, Settings):
            return settings
    return get_settings()


def get_request_logger() -> logging.Logger:
    """Dependency provider returning namespaced API logger."""
    return get_logger("financial_rag.api")


# Reusable dependency aliases
SettingsDep = Annotated[Settings, Depends(get_current_settings)]
LoggerDep = Annotated[logging.Logger, Depends(get_request_logger)]


# Database and Repositories
def get_db_session_manager(settings: SettingsDep) -> DatabaseSessionManager:
    """Return database session manager singleton."""
    return db_manager


def get_document_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> DocumentRepositoryProtocol:
    return PostgresDocumentRepository(session_manager=manager)


def get_version_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> DocumentVersionRepositoryProtocol:
    return PostgresDocumentVersionRepository(session_manager=manager)


def get_page_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> DocumentPageRepositoryProtocol:
    return PostgresDocumentPageRepository(session_manager=manager)


def get_chunk_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> ChunkRepositoryProtocol:
    return PostgresDocumentChunkRepository(session_manager=manager)


def get_job_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> IngestionJobRepositoryProtocol:
    return PostgresIngestionJobRepository(session_manager=manager)


get_ingestion_job_repository = get_job_repository


# Security Repositories & Services
def get_tenant_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> TenantRepositoryProtocol:
    return PostgresTenantRepository(session_manager=manager)


def get_user_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> UserRepositoryProtocol:
    return PostgresUserRepository(session_manager=manager)


def get_refresh_token_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> RefreshTokenRepositoryProtocol:
    return PostgresRefreshTokenRepository(session_manager=manager)


def get_audit_repository(
    manager: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
) -> AuditEventRepositoryProtocol:
    return PostgresAuditEventRepository(session_manager=manager)


def get_audit_service(
    repo: Annotated[AuditEventRepositoryProtocol, Depends(get_audit_repository)],
) -> AuditLoggerProtocol:
    return AuditService(audit_repository=repo)


def get_password_hasher() -> PasswordHasherProtocol:
    return ScryptPasswordHasher()


def get_jwt_manager(settings: SettingsDep) -> TokenManagerProtocol:
    return JwtTokenManager(security_settings=settings.security)


def get_auth_service() -> AuthorizationServiceProtocol:
    return RbacAuthorizationService()


# Principal Authentication Dependency
async def get_current_principal(
    settings: SettingsDep,
    jwt_manager: Annotated[TokenManagerProtocol, Depends(get_jwt_manager)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
    tenant_repo: Annotated[TenantRepositoryProtocol, Depends(get_tenant_repository)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> PrincipalContext:
    """Validate bearer JWT token and derive authenticated principal context."""
    if not authorization or not authorization.startswith("Bearer "):
        if settings.security.auth_disabled_dev and not settings.is_production:
            # Safe development/testing-only bypass with OWNER role
            return PrincipalContext(
                user_id="dev-user-01",
                tenant_id="default_tenant",
                role=UserRole.OWNER,
                permissions=ROLE_PERMISSIONS[UserRole.OWNER],
                authentication_method="dev_mock",
                is_authenticated=True,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected format: 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = authorization[7:].strip()
    try:
        claims = jwt_manager.verify_access_token(raw_token)
    except SecurityError as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(ex.message),
            headers={"WWW-Authenticate": "Bearer"},
        ) from ex

    user_id = claims["sub"]
    tenant_id = claims["tid"]
    role_str = claims.get("role", "member")
    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.MEMBER

    # Validate active user status in database if user repository is available
    user = await user_repo.get_by_id(user_id=user_id, tenant_id=tenant_id)
    if user and user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suspended or disabled.",
        )

    # Validate active tenant status in database if tenant repository is available
    tenant = await tenant_repo.get_by_id(tenant_id=tenant_id)
    if tenant and tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant organization account is suspended or disabled.",
        )

    permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS[UserRole.VIEWER])
    return PrincipalContext(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
        permissions=permissions,
        authentication_method="bearer_jwt",
        is_authenticated=True,
    )


def require_permission(permission: Permission) -> Callable[..., PrincipalContext]:
    """Dependency factory enforcing that the authenticated principal possesses the required permission."""

    def _permission_guard(
        principal: Annotated[PrincipalContext, Depends(get_current_principal)],
        auth_service: Annotated[AuthorizationServiceProtocol, Depends(get_auth_service)],
    ) -> PrincipalContext:
        try:
            auth_service.check_permission(principal, permission)
            return principal
        except SecurityError as ex:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(ex.message),
            ) from ex

    return _permission_guard


# Security Dependency Aliases
PrincipalDep = Annotated[PrincipalContext, Depends(get_current_principal)]
TenantRepoDep = Annotated[TenantRepositoryProtocol, Depends(get_tenant_repository)]
UserRepoDep = Annotated[UserRepositoryProtocol, Depends(get_user_repository)]
RefreshTokenRepoDep = Annotated[
    RefreshTokenRepositoryProtocol, Depends(get_refresh_token_repository)
]
AuditRepoDep = Annotated[AuditEventRepositoryProtocol, Depends(get_audit_repository)]
AuditServiceDep = Annotated[AuditLoggerProtocol, Depends(get_audit_service)]
PasswordHasherDep = Annotated[PasswordHasherProtocol, Depends(get_password_hasher)]
JwtManagerDep = Annotated[TokenManagerProtocol, Depends(get_jwt_manager)]
AuthServiceDep = Annotated[AuthorizationServiceProtocol, Depends(get_auth_service)]


# Infrastructure Adapters
def get_storage(settings: SettingsDep) -> ObjectStorageProtocol:
    return get_storage_adapter(settings.storage)


def get_embedding(settings: SettingsDep) -> EmbeddingProviderProtocol:
    return get_embedding_provider(settings.embedding)


def get_vector_database(settings: SettingsDep) -> VectorStoreProtocol:
    return get_vector_store(settings.qdrant)


def get_sparse_retriever() -> SparseRetrieverProtocol:
    """Provide sparse BM25 retriever instance."""
    return bm25_retriever


def get_pipeline(
    settings: SettingsDep,
    embedding: Annotated[EmbeddingProviderProtocol, Depends(get_embedding)],
    vector_store: Annotated[VectorStoreProtocol, Depends(get_vector_database)],
    sparse_retriever: Annotated[SparseRetrieverProtocol, Depends(get_sparse_retriever)],
) -> IngestionPipeline:
    parser = PyMuPDFParser(parser_settings=settings.parser)
    table_normalizer = FinancialTableNormalizer()
    table_extractor = FinancialTableExtractor(normalizer=table_normalizer)
    normalizer = DocumentNormalizer()
    structure_detector = FinancialStructureDetector()
    chunker = StructureAwareChunker(chunking_settings=settings.chunking)

    return IngestionPipeline(
        parser=parser,
        table_extractor=table_extractor,
        table_normalizer=table_normalizer,
        normalizer=normalizer,
        structure_detector=structure_detector,
        chunker=chunker,
        embedding_provider=embedding,
        vector_store=vector_store,
        sparse_retriever=sparse_retriever,
    )


def get_ingestion_service(
    doc_repo: Annotated[DocumentRepositoryProtocol, Depends(get_document_repository)],
    ver_repo: Annotated[DocumentVersionRepositoryProtocol, Depends(get_version_repository)],
    page_repo: Annotated[DocumentPageRepositoryProtocol, Depends(get_page_repository)],
    chunk_repo: Annotated[ChunkRepositoryProtocol, Depends(get_chunk_repository)],
    job_repo: Annotated[IngestionJobRepositoryProtocol, Depends(get_job_repository)],
    storage: Annotated[ObjectStorageProtocol, Depends(get_storage)],
    pipeline: Annotated[IngestionPipeline, Depends(get_pipeline)],
    settings: SettingsDep,
) -> DocumentIngestionService:
    validator = DocumentValidator(settings=settings.ingestion)
    return DocumentIngestionService(
        document_repo=doc_repo,
        version_repo=ver_repo,
        page_repo=page_repo,
        chunk_repo=chunk_repo,
        job_repo=job_repo,
        storage=storage,
        pipeline=pipeline,
        validator=validator,
    )


# ==========================================
# Phase 2 Retrieval Dependencies
# ==========================================


def get_query_analyzer() -> QueryAnalyzerProtocol:
    """Provide query analyzer instance."""
    return FinancialQueryAnalyzer()


def get_dense_retriever(
    embedding: Annotated[EmbeddingProviderProtocol, Depends(get_embedding)],
    vector_store: Annotated[VectorStoreProtocol, Depends(get_vector_database)],
    settings: SettingsDep,
) -> DenseRetrieverProtocol:
    """Provide dense vector retriever adapter."""
    return QdrantDenseRetriever(
        embedding_provider=embedding,
        vector_store=vector_store,
        expected_dimension=settings.embedding.dimension,
    )


def get_fusion_strategy(settings: SettingsDep) -> FusionStrategyProtocol:
    """Provide Reciprocal Rank Fusion strategy."""
    return ReciprocalRankFusion(default_k=settings.retrieval.rrf_k)


def get_candidate_deduplicator() -> CandidateDeduplicatorProtocol:
    """Provide candidate deduplication engine."""
    return CandidateDeduplicator()


def get_reranker(settings: SettingsDep) -> RerankerProtocol:
    """Provide configured reranker adapter."""
    if settings.retrieval.reranker_provider == "cross_encoder":
        return CrossEncoderReranker(model_name=settings.retrieval.reranker_model_name)
    return MockReranker(model_name=settings.retrieval.reranker_model_name)


def get_evidence_selector() -> EvidenceSelectorProtocol:
    """Provide diversity and table-preserving evidence selector."""
    return EvidenceSelector()


def get_evidence_validator() -> EvidenceValidatorProtocol:
    """Provide evidence quality validation guardrail."""
    return EvidenceValidator()


def get_retrieval_service(
    analyzer: Annotated[QueryAnalyzerProtocol, Depends(get_query_analyzer)],
    dense_retriever: Annotated[DenseRetrieverProtocol, Depends(get_dense_retriever)],
    sparse_retriever: Annotated[SparseRetrieverProtocol, Depends(get_sparse_retriever)],
    fusion_strategy: Annotated[FusionStrategyProtocol, Depends(get_fusion_strategy)],
    deduplicator: Annotated[CandidateDeduplicatorProtocol, Depends(get_candidate_deduplicator)],
    reranker: Annotated[RerankerProtocol, Depends(get_reranker)],
    evidence_selector: Annotated[EvidenceSelectorProtocol, Depends(get_evidence_selector)],
    evidence_validator: Annotated[EvidenceValidatorProtocol, Depends(get_evidence_validator)],
    settings: SettingsDep,
) -> RetrievalServiceProtocol:
    """Provide end-to-end retrieval orchestrator service."""
    return RetrievalService(
        query_analyzer=analyzer,
        dense_retriever=dense_retriever,
        sparse_retriever=sparse_retriever,
        fusion_strategy=fusion_strategy,
        deduplicator=deduplicator,
        reranker=reranker,
        evidence_selector=evidence_selector,
        evidence_validator=evidence_validator,
        retrieval_settings=settings.retrieval,
    )


# ==========================================
# Phase 3 Reasoning Dependencies
# ==========================================


def get_financial_value_parser() -> FinancialValueParserProtocol:
    """Provide financial value parser."""
    return FinancialValueParser()


def get_period_normalizer() -> PeriodNormalizerProtocol:
    """Provide fiscal period normalizer."""
    return FiscalPeriodNormalizer()


def get_fact_extractor(
    value_parser: Annotated[FinancialValueParserProtocol, Depends(get_financial_value_parser)],
    period_normalizer: Annotated[PeriodNormalizerProtocol, Depends(get_period_normalizer)],
) -> FactExtractorProtocol:
    """Provide deterministic fact extractor."""
    return DeterministicFactExtractor(
        value_parser=value_parser, period_normalizer=period_normalizer
    )


def get_financial_calculator() -> FinancialCalculatorProtocol:
    """Provide deterministic Decimal calculator."""
    return DeterministicFinancialCalculator()


def get_conflict_detector() -> ConflictDetectorProtocol:
    """Provide conflict detection engine."""
    return DeterministicConflictDetector()


def get_reasoning_planner() -> ReasoningPlannerProtocol:
    """Provide reasoning planner."""
    return DeterministicReasoningPlanner()


def get_claim_builder() -> ClaimBuilderProtocol:
    """Provide claim builder."""
    return DeterministicClaimBuilder()


def get_citation_generator() -> CitationGeneratorProtocol:
    """Provide citation generator."""
    return DeterministicCitationGenerator()


def get_citation_validator() -> CitationValidatorProtocol:
    """Provide citation validator."""
    return DeterministicCitationValidator()


def get_grounding_validator() -> GroundingValidatorProtocol:
    """Provide grounding validator."""
    return DeterministicGroundingValidator()


def get_answerability_evaluator() -> AnswerabilityEvaluatorProtocol:
    """Provide answerability evaluator."""
    return DeterministicAnswerabilityEvaluator()


def get_reasoning_service(
    retrieval_service: Annotated[RetrievalServiceProtocol, Depends(get_retrieval_service)],
    planner: Annotated[ReasoningPlannerProtocol, Depends(get_reasoning_planner)],
    fact_extractor: Annotated[FactExtractorProtocol, Depends(get_fact_extractor)],
    calculator: Annotated[FinancialCalculatorProtocol, Depends(get_financial_calculator)],
    conflict_detector: Annotated[ConflictDetectorProtocol, Depends(get_conflict_detector)],
    claim_builder: Annotated[ClaimBuilderProtocol, Depends(get_claim_builder)],
    citation_generator: Annotated[CitationGeneratorProtocol, Depends(get_citation_generator)],
    citation_validator: Annotated[CitationValidatorProtocol, Depends(get_citation_validator)],
    grounding_validator: Annotated[GroundingValidatorProtocol, Depends(get_grounding_validator)],
    answerability_evaluator: Annotated[
        AnswerabilityEvaluatorProtocol, Depends(get_answerability_evaluator)
    ],
) -> ReasoningServiceProtocol:
    """Provide end-to-end reasoning and grounding service."""
    return ReasoningService(
        retrieval_service=retrieval_service,
        planner=planner,
        fact_extractor=fact_extractor,
        calculator=calculator,
        conflict_detector=conflict_detector,
        claim_builder=claim_builder,
        citation_generator=citation_generator,
        citation_validator=citation_validator,
        grounding_validator=grounding_validator,
        answerability_evaluator=answerability_evaluator,
    )


IngestionServiceDep = Annotated[DocumentIngestionService, Depends(get_ingestion_service)]
RetrievalServiceDep = Annotated[RetrievalServiceProtocol, Depends(get_retrieval_service)]
ReasoningServiceDep = Annotated[ReasoningServiceProtocol, Depends(get_reasoning_service)]


# ==========================================
# Phase 4 Answer Orchestration Dependencies
# ==========================================

_shared_answer_cache = InMemoryAnswerCache()


def get_llm_provider(settings: SettingsDep) -> LLMProviderProtocol:
    """Provide configured LLM provider adapter."""
    return create_llm_provider(settings.llm)


def get_context_builder() -> ContextBuilderProtocol:
    """Provide deterministic context builder."""
    return DeterministicContextBuilder()


def get_prompt_builder() -> PromptBuilderProtocol:
    """Provide versioned prompt builder."""
    return VersionedPromptBuilder()


def get_answerability_gate() -> AnswerabilityGateProtocol:
    """Provide deterministic answerability gate."""
    return DeterministicAnswerabilityGate()


def get_answer_validator() -> AnswerValidatorProtocol:
    """Provide 8-stage answer validator."""
    return DeterministicAnswerValidator()


def get_response_renderer() -> ResponseRendererProtocol:
    """Provide deterministic response renderer."""
    return DeterministicResponseRenderer()


def get_answer_cache() -> AnswerCacheProtocol:
    """Provide answer cache."""
    return _shared_answer_cache


def get_answer_orchestrator_service(
    reasoning_service: Annotated[ReasoningServiceProtocol, Depends(get_reasoning_service)],
    llm_provider: Annotated[LLMProviderProtocol, Depends(get_llm_provider)],
    context_builder: Annotated[ContextBuilderProtocol, Depends(get_context_builder)],
    prompt_builder: Annotated[PromptBuilderProtocol, Depends(get_prompt_builder)],
    answerability_gate: Annotated[AnswerabilityGateProtocol, Depends(get_answerability_gate)],
    validator: Annotated[AnswerValidatorProtocol, Depends(get_answer_validator)],
    renderer: Annotated[ResponseRendererProtocol, Depends(get_response_renderer)],
    cache: Annotated[AnswerCacheProtocol, Depends(get_answer_cache)],
    settings: SettingsDep,
) -> AnswerOrchestratorServiceProtocol:
    """Provide complete AnswerOrchestrationService."""
    return AnswerOrchestrationService(
        reasoning_service=reasoning_service,
        llm_provider=llm_provider,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        answerability_gate=answerability_gate,
        validator=validator,
        renderer=renderer,
        cache=cache,
        max_retries=1,
        model_name=settings.llm.model_name,
    )


AnswerOrchestratorServiceDep = Annotated[
    AnswerOrchestratorServiceProtocol, Depends(get_answer_orchestrator_service)
]

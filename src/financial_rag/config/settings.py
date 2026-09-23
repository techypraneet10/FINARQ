"""Centralized application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from financial_rag.common.types import Environment


class AppSettings(BaseSettings):
    """Core application server configuration."""

    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Runtime environment (development, testing, staging, production)",
    )
    name: str = Field(
        default="FINARQ",
        description="Application service name",
    )
    version: str = Field(default="0.1.0", description="Semantic service version")
    git_sha: str = Field(default="dev-local", description="Immutable Git SHA release identifier")
    build_timestamp: str = Field(
        default="2026-08-24T00:00:00Z", description="UTC build and packaging timestamp"
    )
    shutdown_timeout_seconds: float = Field(
        default=15.0, ge=1.0, description="Graceful shutdown timeout in seconds"
    )
    debug: bool = Field(default=False, description="Debug mode flag")
    host: str = Field(default="0.0.0.0", description="API bind host")
    port: int = Field(default=8000, ge=1, le=65535, description="API bind port")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://localhost:8501",
        ],
        description="Allowed CORS origin URLs",
    )

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LoggingSettings(BaseSettings):
    """Logging infrastructure configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Root logging verbosity level",
    )
    format: Literal["json", "text"] = Field(
        default="text",
        description="Log emission format (json for prod/staging, text for local dev)",
    )

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    """PostgreSQL relational database configuration."""

    url: str | None = Field(
        default=None, description="Explicit database connection URL (overrides individual params)"
    )
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    name: str = Field(default="financial_rag_db", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: SecretStr = Field(
        default=SecretStr("postgres_local_password"),
        description="Database user password",
    )
    pool_min_size: int = Field(default=5, ge=1, description="Connection pool min size")
    pool_max_size: int = Field(default=20, ge=1, description="Connection pool max size")
    timeout_seconds: float = Field(
        default=30.0, ge=1.0, description="Database connection timeout in seconds"
    )
    statement_timeout_ms: int = Field(
        default=30000, ge=1000, description="SQL statement execution timeout in milliseconds"
    )
    echo: bool = Field(default=False, description="Echo raw SQL queries in logs")

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def connection_url(self) -> str:
        """Construct database async connection URL."""
        if self.url:
            return self.url
        pwd = self.password.get_secret_value()
        return f"postgresql+asyncpg://{self.user}:{pwd}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis cache and task queue configuration."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    db: int = Field(default=0, ge=0, description="Redis database index")
    password: SecretStr = Field(default=SecretStr(""), description="Redis password")
    ssl: bool = Field(default=False, description="Enable TLS/SSL for Redis")
    timeout_seconds: float = Field(
        default=5.0, ge=0.5, description="Redis socket timeout in seconds"
    )
    default_ttl_seconds: int = Field(default=3600, ge=0, description="Default cache time to live")

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class StorageSettings(BaseSettings):
    """Object storage configuration."""

    adapter: Literal["filesystem", "s3"] = Field(
        default="filesystem",
        description="Storage backend adapter ('filesystem' for local dev/tests, 's3' for MinIO/AWS S3)",
    )
    local_dir: str = Field(
        default="./data/storage",
        description="Base directory for local filesystem object storage",
    )
    endpoint_url: str = Field(
        default="http://localhost:9000",
        description="Object storage endpoint URL (MinIO/S3)",
    )
    region: str = Field(default="us-east-1", description="Object storage region")
    bucket_documents: str = Field(
        default="financial-documents",
        description="Bucket name for storing raw financial documents",
    )
    access_key: SecretStr = Field(default=SecretStr("minioadmin"), description="Storage access key")
    secret_key: SecretStr = Field(default=SecretStr("minioadmin"), description="Storage secret key")
    use_ssl: bool = Field(default=False, description="Use SSL for storage access")
    timeout_seconds: float = Field(
        default=30.0, ge=1.0, description="Object storage request timeout in seconds"
    )

    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class QdrantSettings(BaseSettings):
    """Qdrant vector database configuration."""

    host: str = Field(default="localhost", description="Qdrant host")
    port: int = Field(default=6333, ge=1, le=65535, description="Qdrant port")
    api_key: SecretStr = Field(default=SecretStr(""), description="Qdrant API key")
    collection_name: str = Field(
        default="financial_chunks",
        description="Target Qdrant vector collection name",
    )
    use_https: bool = Field(default=False, description="Connect to Qdrant over HTTPS")
    timeout_seconds: float = Field(
        default=10.0, ge=0.5, description="Qdrant request timeout in seconds"
    )
    location: str | None = Field(
        default=None,
        description="Local path or ':memory:' for in-memory Qdrant instance (used in tests/dev)",
    )

    model_config = SettingsConfigDict(
        env_prefix="QDRANT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LLMSettings(BaseSettings):
    """Provider-agnostic LLM client configuration."""

    provider: str = Field(
        default="mock",
        description="Target LLM provider (openai, anthropic, gemini, ollama, mock)",
    )
    model_name: str = Field(default="mock-financial-llm", description="Model identifier name")
    api_key: SecretStr = Field(default=SecretStr(""), description="API Key for LLM provider")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=4096, ge=1, description="Maximum completion tokens")
    request_timeout_seconds: int = Field(default=60, ge=1, description="HTTP timeout for LLM calls")
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum retry count for transient LLM errors"
    )
    retry_backoff_factor: float = Field(
        default=1.5, ge=1.0, description="Exponential backoff factor for LLM retries"
    )
    circuit_breaker_enabled: bool = Field(
        default=True, description="Enable circuit breaker protection for LLM provider"
    )
    circuit_breaker_failure_threshold: int = Field(
        default=5, ge=1, description="Failures before tripping circuit breaker"
    )
    circuit_breaker_recovery_timeout_seconds: float = Field(
        default=30.0, ge=1.0, description="Cool-off period before half-open state"
    )

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class EmbeddingSettings(BaseSettings):
    """Provider-agnostic text embedding configuration."""

    provider: str = Field(
        default="mock",
        description="Target embedding provider (openai, gemini, huggingface, mock)",
    )
    model_name: str = Field(default="mock-text-embedding", description="Embedding model identifier")
    api_key: SecretStr = Field(default=SecretStr(""), description="API Key for embedding provider")
    dimension: int = Field(default=1536, ge=1, description="Expected embedding vector dimension")
    batch_size: int = Field(default=32, ge=1, description="Batch size for generating embeddings")
    request_timeout_seconds: float = Field(
        default=30.0, ge=1.0, description="HTTP timeout for embedding generation"
    )
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum retry count for embedding calls"
    )
    circuit_breaker_enabled: bool = Field(
        default=True, description="Enable circuit breaker protection for embedding provider"
    )

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class WorkerSettings(BaseSettings):
    """Background asynchronous ingestion worker configuration."""

    concurrency: int = Field(
        default=4, ge=1, le=64, description="Worker concurrent task concurrency limit"
    )
    poll_interval_seconds: float = Field(
        default=2.0, ge=0.001, le=60.0, description="Poll interval for pending ingestion jobs"
    )
    job_timeout_seconds: int = Field(
        default=600, ge=1, description="Maximum execution timeout for a single ingestion job"
    )
    batch_size: int = Field(
        default=5, ge=1, le=50, description="Batch size when claiming pending jobs from repository"
    )
    shutdown_timeout_seconds: float = Field(
        default=30.0, ge=0.1, description="Worker graceful shutdown timeout in seconds"
    )

    model_config = SettingsConfigDict(
        env_prefix="WORKER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ParserSettings(BaseSettings):
    """PDF parsing and layout configuration."""

    ocr_enabled: bool = Field(default=True, description="Enable OCR fallback for scanned pages")
    ocr_provider: Literal["tesseract", "mock"] = Field(
        default="mock",
        description="OCR adapter engine ('tesseract' or 'mock')",
    )
    ocr_char_threshold: int = Field(
        default=50,
        ge=0,
        description="Minimum character count per page below which OCR fallback is evaluated",
    )
    ocr_image_area_ratio_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Image area ratio threshold triggering OCR inspection",
    )

    model_config = SettingsConfigDict(
        env_prefix="PARSER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ChunkingSettings(BaseSettings):
    """Structure-aware chunking configuration."""

    max_chunk_size: int = Field(
        default=1000,
        ge=100,
        le=8000,
        description="Maximum target character count per text chunk",
    )
    chunk_overlap: int = Field(
        default=150,
        ge=0,
        le=1000,
        description="Overlap character count between consecutive chunks in the same section",
    )
    preserve_tables: bool = Field(
        default=True,
        description="Keep financial tables intact as dedicated table chunks",
    )
    max_table_tokens: int = Field(
        default=2000,
        ge=200,
        description="Maximum token budget for single table chunks before header-repeating split",
    )

    model_config = SettingsConfigDict(
        env_prefix="CHUNKING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class IngestionSettings(BaseSettings):
    """Document upload and ingestion pipeline configuration."""

    max_file_size_bytes: int = Field(
        default=50 * 1024 * 1024,  # 50 MB
        ge=1024,
        description="Maximum allowed uploaded file size in bytes",
    )
    allowed_content_types: list[str] = Field(
        default_factory=lambda: ["application/pdf"],
        description="Permitted document MIME content types",
    )
    allowed_extensions: list[str] = Field(
        default_factory=lambda: [".pdf"],
        description="Permitted document file extensions",
    )
    max_workers: int = Field(
        default=4,
        ge=1,
        description="Maximum concurrent async ingestion task workers",
    )

    model_config = SettingsConfigDict(
        env_prefix="INGESTION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class RetrievalSettings(BaseSettings):
    """Hybrid retrieval, reranking, and evidence selection configuration."""

    dense_top_k: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of top candidates to fetch from dense vector search",
    )
    sparse_top_k: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of top candidates to fetch from sparse lexical search",
    )
    candidate_pool_size: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum candidate pool size sent to reranker after fusion",
    )
    rerank_top_k: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Number of top reranked candidates to select",
    )
    final_top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Default number of final evidence items returned to client",
    )
    rrf_k: int = Field(
        default=60,
        ge=1,
        description="Reciprocal Rank Fusion smoothing parameter constant k",
    )
    dense_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Weight multiplier for dense vector retrieval in RRF fusion",
    )
    sparse_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Weight multiplier for sparse BM25 retrieval in RRF fusion",
    )
    reranker_provider: Literal["mock", "cross_encoder", "cohere"] = Field(
        default="mock",
        description="Reranker adapter implementation engine ('mock', 'cross_encoder', 'cohere')",
    )
    reranker_model_name: str = Field(
        default="mock-financial-reranker",
        description="Model name/path for cross-encoder reranker",
    )
    diversity_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Diversity selection threshold to avoid redundant evidence",
    )
    max_chunks_per_document: int = Field(
        default=5,
        ge=1,
        description="Maximum evidence chunks allowed from a single document",
    )
    cache_enabled: bool = Field(
        default=False,
        description="Enable retrieval caching for deterministic queries",
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=0,
        description="Cache TTL in seconds for retrieval result sets",
    )
    enable_sparse_fallback: bool = Field(
        default=True,
        description="Fall back to dense-only if sparse retriever fails",
    )
    enable_dense_fallback: bool = Field(
        default=True,
        description="Fall back to sparse-only if dense retriever fails",
    )
    timeout_seconds: float = Field(
        default=10.0,
        ge=0.5,
        le=120.0,
        description="Maximum execution timeout for retrieval pipeline in seconds",
    )

    model_config = SettingsConfigDict(
        env_prefix="RETRIEVAL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class SecuritySettings(BaseSettings):
    """Authentication, JWT, RBAC, and rate limiting security configuration."""

    jwt_secret_key: SecretStr = Field(
        default=SecretStr("financial-rag-dev-secret-key-32-chars-min-len-xyz123"),
        description="HMAC-SHA256 signing secret for JWT tokens",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Allowed JWT signing algorithm (allowlist: HS256)",
    )
    jwt_issuer: str = Field(
        default="financial-rag-platform",
        description="Expected JWT issuer (iss) claim",
    )
    jwt_audience: str = Field(
        default="financial-rag-api",
        description="Expected JWT audience (aud) claim",
    )
    access_token_ttl_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        description="Lifetime of access tokens in minutes",
    )
    refresh_token_ttl_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Lifetime of refresh tokens in days",
    )
    password_min_length: int = Field(
        default=8,
        ge=6,
        description="Minimum permitted length for user passwords",
    )
    auth_disabled_dev: bool = Field(
        default=False,
        description="Development authentication bypass flag (strictly forbidden in production)",
    )
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable API rate limiting",
    )
    rate_limit_auth_per_minute: int = Field(
        default=10,
        ge=1,
        description="Rate limit for authentication endpoints per minute",
    )
    rate_limit_upload_per_minute: int = Field(
        default=20,
        ge=1,
        description="Rate limit for document uploads per minute",
    )
    rate_limit_answers_per_minute: int = Field(
        default=30,
        ge=1,
        description="Rate limit for answer generation per minute",
    )
    rate_limit_retrieval_per_minute: int = Field(
        default=60,
        ge=1,
        description="Rate limit for vector/hybrid retrieval per minute",
    )
    rate_limit_default_per_minute: int = Field(
        default=120,
        ge=1,
        description="Default rate limit for API endpoints per minute",
    )
    max_failed_logins: int = Field(
        default=5,
        ge=1,
        description="Maximum failed login attempts before temporary lockout",
    )
    lockout_duration_seconds: int = Field(
        default=300,
        ge=10,
        description="Temporary lockout duration in seconds after excessive failed logins",
    )

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Unified application settings container."""

    app: AppSettings = Field(default_factory=AppSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    parser: ParserSettings = Field(default_factory=ParserSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    ingestion: IngestionSettings = Field(default_factory=IngestionSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    worker: WorkerSettings = Field(default_factory=WorkerSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("logging")
    @classmethod
    def align_logging_with_environment(
        cls, logging_val: LoggingSettings, info: object
    ) -> LoggingSettings:
        """Validate logging configuration."""
        return logging_val

    @property
    def is_production(self) -> bool:
        """Check if executing in production environment."""
        return self.app.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if executing in development environment."""
        return self.app.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Check if executing in testing environment."""
        return self.app.environment == Environment.TESTING


def validate_security_configuration(
    settings: Settings | None = None,
    security_settings: SecuritySettings | None = None,
) -> None:
    """Enforce strict production security invariants and fail fast on insecure configuration."""
    app_settings = settings or get_settings()
    sec = security_settings or app_settings.security
    if app_settings.is_production:
        if sec.auth_disabled_dev:
            raise ValueError(
                "CRITICAL SECURITY ERROR: auth_disabled_dev cannot be True in PRODUCTION environment."
            )

        secret = sec.jwt_secret_key.get_secret_value()
        if "dev-secret" in secret or len(secret) < 32:
            raise ValueError(
                "CRITICAL SECURITY ERROR: Production JWT secret key must be strong and at least 32 characters long."
            )

        if "*" in app_settings.app.cors_origins:
            raise ValueError(
                "CRITICAL SECURITY ERROR: Wildcard CORS origin ('*') is forbidden in PRODUCTION environment."
            )

        if app_settings.app.debug:
            raise ValueError(
                "CRITICAL SECURITY ERROR: Debug mode cannot be enabled in PRODUCTION environment."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton instance of application settings."""
    return Settings()

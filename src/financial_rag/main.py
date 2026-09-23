from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from financial_rag.api.exceptions import register_exception_handlers
from financial_rag.api.middleware import register_middlewares
from financial_rag.api.v1.endpoints.health import router as root_health_router
from financial_rag.api.v1.endpoints.metrics import router as root_metrics_router
from financial_rag.api.v1.endpoints.ready import router as root_ready_router
from financial_rag.api.v1.endpoints.version import router as root_version_router
from financial_rag.api.v1.router import v1_router
from financial_rag.common.types import Environment
from financial_rag.config.settings import (
    Settings,
    get_settings,
    validate_security_configuration,
)
from financial_rag.infrastructure.logging import get_logger, setup_logging
from financial_rag.infrastructure.persistence.database import db_manager

logger = get_logger("financial_rag.main")


async def _seed_dev_identities(db_mgr: Any) -> None:
    """Seed default developer test identities and tenants in local dev mode."""
    from financial_rag.domain.entities.security import (
        Tenant,
        TenantStatus,
        User,
        UserRole,
        UserStatus,
    )
    from financial_rag.infrastructure.persistence.repositories import (
        PostgresTenantRepository,
        PostgresUserRepository,
    )
    from financial_rag.infrastructure.security.hasher import ScryptPasswordHasher

    hasher = ScryptPasswordHasher()
    tenant_repo = PostgresTenantRepository(session_manager=db_mgr)
    user_repo = PostgresUserRepository(session_manager=db_mgr)

    dev_personas = [
        {
            "tenant_id": "tenant-alpha",
            "tenant_name": "Tenant Alpha (Alpha Capital)",
            "user_id": "user-tenant-a",
            "email": "tenant_a@financial.org",
            "password": "Password123!",
            "role": UserRole.OWNER,
        },
        {
            "tenant_id": "tenant-beta",
            "tenant_name": "Tenant Beta (Beta Partners)",
            "user_id": "user-tenant-b",
            "email": "tenant_b@financial.org",
            "password": "Password123!",
            "role": UserRole.OWNER,
        },
    ]

    for p in dev_personas:
        existing_user = await user_repo.get_by_email(p["email"])
        if not existing_user:
            existing_tenant = await tenant_repo.get_by_id(p["tenant_id"])
            if not existing_tenant:
                tenant = Tenant(
                    id=p["tenant_id"],
                    name=p["tenant_name"],
                    status=TenantStatus.ACTIVE,
                )
                await tenant_repo.save(tenant)

            hashed_pwd = hasher.hash_password(p["password"])
            user = User(
                id=str(p["user_id"]),
                tenant_id=str(p["tenant_id"]),
                email=str(p["email"]),
                hashed_password=hashed_pwd,
                role=p["role"] if isinstance(p["role"], UserRole) else UserRole(str(p["role"])),
                status=UserStatus.ACTIVE,
            )
            await user_repo.save(user)
            logger.info(f"Seeded dev identity: {p['email']} (Tenant: {p['tenant_id']})")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager handling startup and shutdown hooks."""
    settings = getattr(app.state, "settings", get_settings())
    setup_logging(level=settings.logging.level, format_type=settings.logging.format)
    # Fail-fast security invariant verification
    validate_security_configuration(settings=settings)
    logger.info(
        f"Starting {settings.app.name} v{settings.app.version} (commit: {settings.app.git_sha}) in [{settings.app.environment.value}] mode"
    )
    if (
        settings.app.environment == Environment.DEVELOPMENT
        and "sqlite" in settings.database.connection_url
    ):
        try:
            await db_manager.create_all_tables()
            await _seed_dev_identities(db_manager)
            try:
                from financial_rag.infrastructure.vector_store import get_vector_store

                vstore = get_vector_store(settings.qdrant)
                await vstore.initialize_collection(dimension=settings.embedding.dimension)
            except Exception as v_ex:
                logger.debug(f"Dev vector collection initialization note: {v_ex}")
            logger.info("Local SQLite database tables and seed identities verified successfully")
        except Exception as ex:
            logger.warning(f"Note on creating local dev tables: {ex}")
    yield
    logger.info("Gracefully shutting down Financial RAG application")
    try:
        await db_manager.close()
    except Exception as ex:
        logger.warning(f"Error disposing database connections during shutdown: {ex}")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure an instance of the FastAPI application.

    Args:
        settings: Optional explicit Settings instance (useful for unit testing).
    """
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.app.name,
        version=app_settings.app.version,
        description=(
            "Financial Document Intelligence & Verified Reasoning Platform. "
            "Grounded, fact-checked RAG with deterministic numerical reasoning."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Store settings in application state
    app.state.settings = app_settings

    # 1. Register CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.app.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register Custom Middleware (Correlation ID, Request Timing)
    register_middlewares(app)

    # 3. Register Custom Exception Handlers
    register_exception_handlers(app)

    # 4. Include Root Health / Ready / Version / Metrics Endpoints
    app.include_router(root_health_router)
    app.include_router(root_ready_router)
    app.include_router(root_version_router)
    app.include_router(root_metrics_router)

    # 5. Include Versioned API Router (/api/v1)
    app.include_router(v1_router)

    # 6. Configure OpenAPI Security Schemes
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT Bearer token in the format: Bearer <token>",
            }
        }
        public_prefixes = (
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/health",
            "/api/v1/ready",
            "/api/v1/version",
            "/api/v1/metrics",
            "/health",
            "/ready",
            "/version",
            "/metrics",
        )
        for path, path_item in openapi_schema.get("paths", {}).items():
            if path.startswith("/api/v1") and not any(path.startswith(p) for p in public_prefixes):
                for method in path_item:
                    if (
                        method in ["get", "post", "put", "delete", "patch"]
                        and "security" not in path_item[method]
                    ):
                        path_item[method]["security"] = [{"bearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    return app


# Default ASGI application instance
app = create_app()


def main() -> None:
    """Entrypoint function for CLI and local development running."""
    settings = get_settings()
    uvicorn.run(
        "financial_rag.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.logging.level.lower(),
    )


if __name__ == "__main__":
    main()

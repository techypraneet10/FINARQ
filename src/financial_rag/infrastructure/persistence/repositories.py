"""PostgreSQL repository implementations using SQLAlchemy 2.0 Async."""

from sqlalchemy import delete, desc, select

from financial_rag.common.types import (
    BlockType,
    ChunkType,
    DocumentId,
    DocumentType,
    ExtractionMethod,
    IngestionStage,
    IngestionStatus,
    JobId,
    VersionId,
)
from financial_rag.domain.entities.models import (
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentVersion,
    FinancialTable,
    IngestionJob,
    LayoutBlock,
)
from financial_rag.domain.entities.security import (
    AuditEvent,
    AuditEventType,
    RefreshToken,
    Tenant,
    TenantStatus,
    User,
    UserRole,
    UserStatus,
)
from financial_rag.domain.entities.value_objects import BoundingBox, TableCell
from financial_rag.domain.interfaces.repository import (
    ChunkRepositoryProtocol,
    DocumentPageRepositoryProtocol,
    DocumentRepositoryProtocol,
    DocumentVersionRepositoryProtocol,
    IngestionJobRepositoryProtocol,
)
from financial_rag.domain.interfaces.security import (
    AuditEventRepositoryProtocol,
    RefreshTokenRepositoryProtocol,
    TenantRepositoryProtocol,
    UserRepositoryProtocol,
)
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager, db_manager
from financial_rag.infrastructure.persistence.models import (
    AuditEventORM,
    DocumentChunkORM,
    DocumentORM,
    DocumentPageORM,
    DocumentVersionORM,
    IngestionJobORM,
    RefreshTokenORM,
    TenantORM,
    UserORM,
)

logger = get_logger("financial_rag.infrastructure.persistence.repositories")


class PostgresTenantRepository(TenantRepositoryProtocol):
    """PostgreSQL repository for Tenant organizations."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: TenantORM) -> Tenant:
        return Tenant(
            id=orm.id,
            name=orm.name,
            status=TenantStatus(orm.status),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            metadata=orm.metadata_json or {},
        )

    async def save(self, tenant: Tenant) -> Tenant:
        async with self._session_manager.session() as session:
            existing = await session.get(TenantORM, str(tenant.id))
            if existing:
                existing.name = tenant.name
                existing.status = tenant.status.value
                existing.updated_at = tenant.updated_at
                existing.metadata_json = tenant.metadata
                await session.flush()
                return self._to_domain(existing)
            else:
                orm = TenantORM(
                    id=str(tenant.id),
                    name=tenant.name,
                    status=tenant.status.value,
                    created_at=tenant.created_at,
                    updated_at=tenant.updated_at,
                    metadata_json=tenant.metadata,
                )
                session.add(orm)
                await session.flush()
                return self._to_domain(orm)

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        async with self._session_manager.session() as session:
            orm = await session.get(TenantORM, str(tenant_id))
            return self._to_domain(orm) if orm else None

    async def list_tenants(self, limit: int = 50, offset: int = 0) -> list[Tenant]:
        async with self._session_manager.session() as session:
            stmt = (
                select(TenantORM).order_by(desc(TenantORM.created_at)).limit(limit).offset(offset)
            )
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]


class PostgresUserRepository(UserRepositoryProtocol):
    """PostgreSQL repository for User identities."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: UserORM) -> User:
        return User(
            id=orm.id,
            tenant_id=orm.tenant_id,
            email=orm.email,
            hashed_password=orm.hashed_password,
            role=UserRole(orm.role),
            status=UserStatus(orm.status),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            last_login_at=orm.last_login_at,
            metadata=orm.metadata_json or {},
        )

    async def save(self, user: User) -> User:
        async with self._session_manager.session() as session:
            existing = await session.get(UserORM, str(user.id))
            if existing:
                existing.tenant_id = str(user.tenant_id)
                existing.email = user.email.lower().strip()
                existing.hashed_password = user.hashed_password
                existing.role = user.role.value
                existing.status = user.status.value
                existing.updated_at = user.updated_at
                existing.last_login_at = user.last_login_at
                existing.metadata_json = user.metadata
                await session.flush()
                return self._to_domain(existing)
            else:
                orm = UserORM(
                    id=str(user.id),
                    tenant_id=str(user.tenant_id),
                    email=user.email.lower().strip(),
                    hashed_password=user.hashed_password,
                    role=user.role.value,
                    status=user.status.value,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    last_login_at=user.last_login_at,
                    metadata_json=user.metadata,
                )
                session.add(orm)
                await session.flush()
                return self._to_domain(orm)

    async def get_by_id(self, user_id: str, tenant_id: str | None = None) -> User | None:
        async with self._session_manager.session() as session:
            if tenant_id:
                stmt = select(UserORM).where(
                    UserORM.id == str(user_id), UserORM.tenant_id == str(tenant_id)
                )
                result = await session.execute(stmt)
                orm = result.scalars().first()
            else:
                orm = await session.get(UserORM, str(user_id))
            return self._to_domain(orm) if orm else None

    async def get_by_email(self, email: str) -> User | None:
        async with self._session_manager.session() as session:
            stmt = select(UserORM).where(UserORM.email == email.lower().strip())
            result = await session.execute(stmt)
            orm = result.scalars().first()
            return self._to_domain(orm) if orm else None

    async def list_by_tenant(self, tenant_id: str, limit: int = 50, offset: int = 0) -> list[User]:
        async with self._session_manager.session() as session:
            stmt = (
                select(UserORM)
                .where(UserORM.tenant_id == str(tenant_id))
                .order_by(desc(UserORM.created_at))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]


class PostgresRefreshTokenRepository(RefreshTokenRepositoryProtocol):
    """PostgreSQL repository for RefreshToken tracking and revocation."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: RefreshTokenORM) -> RefreshToken:
        return RefreshToken(
            token_id=orm.token_id,
            user_id=orm.user_id,
            tenant_id=orm.tenant_id,
            token_hash=orm.token_hash,
            expires_at=orm.expires_at,
            revoked=orm.revoked,
            created_at=orm.created_at,
            rotated_to_token_id=orm.rotated_to_token_id,
        )

    async def save(self, token: RefreshToken) -> RefreshToken:
        async with self._session_manager.session() as session:
            existing = await session.get(RefreshTokenORM, str(token.token_id))
            if existing:
                existing.revoked = token.revoked
                existing.rotated_to_token_id = token.rotated_to_token_id
                await session.flush()
                return self._to_domain(existing)
            else:
                orm = RefreshTokenORM(
                    token_id=str(token.token_id),
                    user_id=str(token.user_id),
                    tenant_id=str(token.tenant_id),
                    token_hash=token.token_hash,
                    expires_at=token.expires_at,
                    revoked=token.revoked,
                    created_at=token.created_at,
                    rotated_to_token_id=token.rotated_to_token_id,
                )
                session.add(orm)
                await session.flush()
                return self._to_domain(orm)

    async def get_by_id(self, token_id: str) -> RefreshToken | None:
        async with self._session_manager.session() as session:
            orm = await session.get(RefreshTokenORM, str(token_id))
            return self._to_domain(orm) if orm else None

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        async with self._session_manager.session() as session:
            stmt = select(RefreshTokenORM).where(RefreshTokenORM.token_hash == token_hash)
            result = await session.execute(stmt)
            orm = result.scalars().first()
            return self._to_domain(orm) if orm else None

    async def revoke_token(self, token_id: str, rotated_to_id: str | None = None) -> bool:
        async with self._session_manager.session() as session:
            orm = await session.get(RefreshTokenORM, str(token_id))
            if orm:
                orm.revoked = True
                if rotated_to_id:
                    orm.rotated_to_token_id = rotated_to_id
                await session.flush()
                return True
            return False

    async def revoke_all_for_user(self, user_id: str) -> int:
        async with self._session_manager.session() as session:
            stmt = select(RefreshTokenORM).where(
                RefreshTokenORM.user_id == str(user_id), RefreshTokenORM.revoked.is_(False)
            )
            result = await session.execute(stmt)
            tokens = result.scalars().all()
            count = 0
            for t in tokens:
                t.revoked = True
                count += 1
            await session.flush()
            return count


class PostgresAuditEventRepository(AuditEventRepositoryProtocol):
    """PostgreSQL repository for immutable security AuditEvent persistence."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: AuditEventORM) -> AuditEvent:
        return AuditEvent(
            event_id=orm.event_id,
            timestamp=orm.timestamp,
            tenant_id=orm.tenant_id,
            actor_user_id=orm.actor_user_id,
            event_type=AuditEventType(orm.event_type),
            resource_type=orm.resource_type,
            resource_id=orm.resource_id,
            action=orm.action,
            outcome=orm.outcome,
            request_id=orm.request_id,
            trace_id=orm.trace_id,
            source_ip=orm.source_ip,
            user_agent=orm.user_agent,
            metadata=orm.metadata_json or {},
        )

    async def save(self, event: AuditEvent) -> AuditEvent:
        async with self._session_manager.session() as session:
            orm = AuditEventORM(
                event_id=str(event.event_id),
                timestamp=event.timestamp,
                tenant_id=str(event.tenant_id) if event.tenant_id else None,
                actor_user_id=str(event.actor_user_id) if event.actor_user_id else None,
                event_type=event.event_type.value,
                resource_type=event.resource_type,
                resource_id=str(event.resource_id) if event.resource_id else None,
                action=event.action,
                outcome=event.outcome,
                request_id=event.request_id,
                trace_id=event.trace_id,
                source_ip=event.source_ip,
                user_agent=event.user_agent,
                metadata_json=event.metadata,
            )
            session.add(orm)
            await session.flush()
            return self._to_domain(orm)

    async def list_by_tenant(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEvent]:
        async with self._session_manager.session() as session:
            stmt = (
                select(AuditEventORM)
                .where(AuditEventORM.tenant_id == str(tenant_id))
                .order_by(desc(AuditEventORM.timestamp))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]


class PostgresDocumentRepository(DocumentRepositoryProtocol):
    """PostgreSQL repository for Document entity with tenant boundary scoping."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: DocumentORM) -> Document:
        return Document(
            id=orm.id,
            title=orm.title,
            document_type=DocumentType(orm.document_type),
            tenant_id=orm.tenant_id,
            ticker_symbol=orm.ticker_symbol,
            fiscal_year=orm.fiscal_year,
            fiscal_period=orm.fiscal_period,
            storage_uri=orm.storage_uri,
            file_hash_sha256=orm.file_hash_sha256,
            pages_count=orm.pages_count,
            current_version_id=orm.current_version_id,
            user_id=orm.user_id,
            metadata=orm.metadata_json or {},
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def save(self, document: Document) -> Document:
        async with self._session_manager.session() as session:
            existing = await session.get(DocumentORM, str(document.id))
            if existing:
                existing.title = document.title
                existing.document_type = document.document_type.value
                existing.tenant_id = str(document.tenant_id)
                existing.ticker_symbol = document.ticker_symbol
                existing.fiscal_year = document.fiscal_year
                existing.fiscal_period = document.fiscal_period
                existing.storage_uri = document.storage_uri
                existing.file_hash_sha256 = document.file_hash_sha256
                existing.pages_count = document.pages_count
                existing.current_version_id = (
                    str(document.current_version_id) if document.current_version_id else None
                )
                existing.user_id = str(document.user_id) if document.user_id else None
                existing.metadata_json = document.metadata
                existing.updated_at = document.updated_at
                await session.flush()
                return self._to_domain(existing)
            else:
                orm = DocumentORM(
                    id=str(document.id),
                    title=document.title,
                    document_type=document.document_type.value,
                    tenant_id=str(document.tenant_id),
                    ticker_symbol=document.ticker_symbol,
                    fiscal_year=document.fiscal_year,
                    fiscal_period=document.fiscal_period,
                    storage_uri=document.storage_uri,
                    file_hash_sha256=document.file_hash_sha256,
                    pages_count=document.pages_count,
                    current_version_id=(
                        str(document.current_version_id) if document.current_version_id else None
                    ),
                    user_id=str(document.user_id) if document.user_id else None,
                    metadata_json=document.metadata,
                    created_at=document.created_at,
                    updated_at=document.updated_at,
                )
                session.add(orm)
                await session.flush()
                return self._to_domain(orm)

    async def get_by_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> Document | None:
        async with self._session_manager.session() as session:
            if tenant_id:
                stmt = select(DocumentORM).where(
                    DocumentORM.id == str(document_id), DocumentORM.tenant_id == str(tenant_id)
                )
                result = await session.execute(stmt)
                orm = result.scalars().first()
            else:
                orm = await session.get(DocumentORM, str(document_id))
            return self._to_domain(orm) if orm else None

    async def get_by_hash(
        self, file_hash_sha256: str, tenant_id: str | None = None
    ) -> Document | None:
        async with self._session_manager.session() as session:
            stmt = select(DocumentORM).where(DocumentORM.file_hash_sha256 == file_hash_sha256)
            if tenant_id:
                stmt = stmt.where(DocumentORM.tenant_id == str(tenant_id))
            result = await session.execute(stmt)
            orm = result.scalars().first()
            return self._to_domain(orm) if orm else None

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        ticker_symbol: str | None = None,
        tenant_id: str | None = None,
    ) -> list[Document]:
        async with self._session_manager.session() as session:
            stmt = select(DocumentORM)
            if tenant_id:
                stmt = stmt.where(DocumentORM.tenant_id == str(tenant_id))
            if ticker_symbol:
                stmt = stmt.where(DocumentORM.ticker_symbol == ticker_symbol.upper())
            stmt = stmt.order_by(desc(DocumentORM.created_at)).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

    async def delete(self, document_id: DocumentId, tenant_id: str | None = None) -> bool:
        async with self._session_manager.session() as session:
            if tenant_id:
                stmt = select(DocumentORM).where(
                    DocumentORM.id == str(document_id), DocumentORM.tenant_id == str(tenant_id)
                )
                result = await session.execute(stmt)
                orm = result.scalars().first()
            else:
                orm = await session.get(DocumentORM, str(document_id))
            if orm:
                await session.delete(orm)
                await session.flush()
                return True
            return False

    async def health_check(self) -> bool:
        return await self._session_manager.health_check()


class PostgresDocumentVersionRepository(DocumentVersionRepositoryProtocol):
    """PostgreSQL repository for DocumentVersion entity."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: DocumentVersionORM) -> DocumentVersion:
        return DocumentVersion(
            id=orm.id,
            document_id=orm.document_id,
            version_number=orm.version_number,
            tenant_id=orm.tenant_id,
            storage_uri=orm.storage_uri,
            file_hash_sha256=orm.file_hash_sha256,
            filename=orm.filename,
            file_size_bytes=orm.file_size_bytes,
            mime_type=orm.mime_type,
            pages_count=orm.pages_count,
            created_at=orm.created_at,
            metadata=orm.metadata_json or {},
        )

    async def save(self, version: DocumentVersion) -> DocumentVersion:
        async with self._session_manager.session() as session:
            existing = await session.get(DocumentVersionORM, str(version.id))
            if existing:
                existing.version_number = version.version_number
                existing.tenant_id = str(version.tenant_id)
                existing.storage_uri = version.storage_uri
                existing.file_hash_sha256 = version.file_hash_sha256
                existing.filename = version.filename
                existing.file_size_bytes = version.file_size_bytes
                existing.mime_type = version.mime_type
                existing.pages_count = version.pages_count
                existing.metadata_json = version.metadata
                await session.flush()
                return self._to_domain(existing)
            else:
                orm = DocumentVersionORM(
                    id=str(version.id),
                    document_id=str(version.document_id),
                    version_number=version.version_number,
                    tenant_id=str(version.tenant_id),
                    storage_uri=version.storage_uri,
                    file_hash_sha256=version.file_hash_sha256,
                    filename=version.filename,
                    file_size_bytes=version.file_size_bytes,
                    mime_type=version.mime_type,
                    pages_count=version.pages_count,
                    created_at=version.created_at,
                    metadata_json=version.metadata,
                )
                session.add(orm)
                await session.flush()
                return self._to_domain(orm)

    async def get_by_id(
        self, version_id: VersionId, tenant_id: str | None = None
    ) -> DocumentVersion | None:
        async with self._session_manager.session() as session:
            if tenant_id:
                stmt = select(DocumentVersionORM).where(
                    DocumentVersionORM.id == str(version_id),
                    DocumentVersionORM.tenant_id == str(tenant_id),
                )
                result = await session.execute(stmt)
                orm = result.scalars().first()
            else:
                orm = await session.get(DocumentVersionORM, str(version_id))
            return self._to_domain(orm) if orm else None

    async def get_by_hash(
        self, file_hash_sha256: str, tenant_id: str | None = None
    ) -> DocumentVersion | None:
        async with self._session_manager.session() as session:
            stmt = select(DocumentVersionORM).where(
                DocumentVersionORM.file_hash_sha256 == file_hash_sha256
            )
            if tenant_id:
                stmt = stmt.where(DocumentVersionORM.tenant_id == str(tenant_id))
            result = await session.execute(stmt)
            orm = result.scalars().first()
            return self._to_domain(orm) if orm else None

    async def get_by_document_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> list[DocumentVersion]:
        async with self._session_manager.session() as session:
            stmt = select(DocumentVersionORM).where(
                DocumentVersionORM.document_id == str(document_id)
            )
            if tenant_id:
                stmt = stmt.where(DocumentVersionORM.tenant_id == str(tenant_id))
            stmt = stmt.order_by(DocumentVersionORM.version_number.asc())
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

    async def get_latest_version(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> DocumentVersion | None:
        async with self._session_manager.session() as session:
            stmt = select(DocumentVersionORM).where(
                DocumentVersionORM.document_id == str(document_id)
            )
            if tenant_id:
                stmt = stmt.where(DocumentVersionORM.tenant_id == str(tenant_id))
            stmt = stmt.order_by(desc(DocumentVersionORM.version_number)).limit(1)
            result = await session.execute(stmt)
            orm = result.scalars().first()
            return self._to_domain(orm) if orm else None


class PostgresDocumentPageRepository(DocumentPageRepositoryProtocol):
    """PostgreSQL repository for DocumentPage storage."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: DocumentPageORM) -> DocumentPage:
        blocks = [
            LayoutBlock(
                id=b["id"],
                page_number=b["page_number"],
                block_type=BlockType(b["block_type"]),
                content=b["content"],
                reading_order=b.get("reading_order", 0),
                bounding_box=BoundingBox(**b["bounding_box"]) if b.get("bounding_box") else None,
                confidence=b.get("confidence", 1.0),
                section_path=b.get("section_path", ""),
                font_size=b.get("font_size"),
                is_bold=b.get("is_bold", False),
                source_method=ExtractionMethod(b.get("source_method", "native")),
                metadata=b.get("metadata", {}),
            )
            for b in (orm.blocks_json or [])
        ]
        tables = [
            FinancialTable(
                id=t["id"],
                page_number=t["page_number"],
                title=t.get("title", ""),
                headers=t.get("headers", []),
                rows=t.get("rows", []),
                cells=[TableCell(**c) for c in t.get("cells", [])],
                units=t.get("units", ""),
                currency=t.get("currency", "USD"),
                scale=t.get("scale", 1.0),
                footnotes=t.get("footnotes", []),
                bounding_box=BoundingBox(**t["bounding_box"]) if t.get("bounding_box") else None,
                markdown_repr=t.get("markdown_repr", ""),
                csv_repr=t.get("csv_repr", ""),
                metadata=t.get("metadata", {}),
            )
            for t in (orm.tables_json or [])
        ]
        return DocumentPage(
            page_number=orm.page_number,
            text_content=orm.text_content,
            id=orm.id,
            document_id=orm.document_id,
            version_id=orm.version_id,
            tenant_id=orm.tenant_id,
            blocks=blocks,
            tables=tables,
            extraction_method=ExtractionMethod(orm.extraction_method),
            has_images=orm.has_images,
            confidence=orm.confidence,
            width=orm.width,
            height=orm.height,
            metadata=orm.metadata_json or {},
        )

    async def save_batch(self, pages: list[DocumentPage]) -> int:
        if not pages:
            return 0
        async with self._session_manager.session() as session:
            count = 0
            for page in pages:
                orm = DocumentPageORM(
                    id=str(page.id),
                    document_id=str(page.document_id),
                    version_id=str(page.version_id),
                    tenant_id=str(page.tenant_id),
                    page_number=page.page_number,
                    text_content=page.text_content,
                    extraction_method=page.extraction_method.value,
                    has_images=page.has_images,
                    confidence=page.confidence,
                    width=page.width,
                    height=page.height,
                    blocks_json=[b.to_dict() for b in page.blocks],
                    tables_json=[t.to_dict() for t in page.tables],
                    metadata_json=page.metadata,
                )
                session.add(orm)
                count += 1
            await session.flush()
            return count

    async def get_by_version_id(
        self, version_id: VersionId, tenant_id: str | None = None
    ) -> list[DocumentPage]:
        async with self._session_manager.session() as session:
            stmt = select(DocumentPageORM).where(DocumentPageORM.version_id == str(version_id))
            if tenant_id:
                stmt = stmt.where(DocumentPageORM.tenant_id == str(tenant_id))
            stmt = stmt.order_by(DocumentPageORM.page_number.asc())
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

    async def get_by_document_and_page(
        self, document_id: DocumentId, page_number: int, tenant_id: str | None = None
    ) -> DocumentPage | None:
        async with self._session_manager.session() as session:
            stmt = select(DocumentPageORM).where(
                DocumentPageORM.document_id == str(document_id),
                DocumentPageORM.page_number == page_number,
            )
            if tenant_id:
                stmt = stmt.where(DocumentPageORM.tenant_id == str(tenant_id))
            result = await session.execute(stmt)
            orm = result.scalars().first()
            return self._to_domain(orm) if orm else None


class PostgresDocumentChunkRepository(ChunkRepositoryProtocol):
    """PostgreSQL repository for DocumentChunk storage with tenant isolation."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: DocumentChunkORM) -> DocumentChunk:
        return DocumentChunk(
            id=orm.id,
            document_id=orm.document_id,
            page_number=orm.page_number,
            content=orm.content,
            chunk_index=orm.chunk_index,
            document_version_id=orm.version_id,
            tenant_id=orm.tenant_id,
            page_numbers=orm.page_numbers_json or [orm.page_number],
            chunk_type=ChunkType(orm.chunk_type),
            source_block_ids=orm.source_block_ids_json or [],
            section_path=orm.section_path,
            table_id=orm.table_id,
            token_count=orm.token_count,
            char_count=orm.char_count,
            metadata=orm.metadata_json or {},
            created_at=orm.created_at,
        )

    async def save(self, chunk: DocumentChunk) -> DocumentChunk:
        await self.save_batch([chunk])
        return chunk

    async def save_batch(self, chunks: list[DocumentChunk]) -> int:
        if not chunks:
            return 0
        async with self._session_manager.session() as session:
            count = 0
            for chunk in chunks:
                orm = DocumentChunkORM(
                    id=str(chunk.id),
                    document_id=str(chunk.document_id),
                    version_id=str(chunk.document_version_id),
                    tenant_id=str(chunk.tenant_id),
                    page_number=chunk.page_number,
                    page_numbers_json=chunk.page_numbers or [chunk.page_number],
                    chunk_index=chunk.chunk_index,
                    chunk_type=chunk.chunk_type.value,
                    content=chunk.content,
                    source_block_ids_json=[str(bid) for bid in chunk.source_block_ids],
                    section_path=chunk.section_path,
                    table_id=str(chunk.table_id) if chunk.table_id else None,
                    token_count=chunk.token_count,
                    char_count=chunk.char_count,
                    metadata_json=chunk.metadata,
                    created_at=chunk.created_at,
                )
                session.add(orm)
                count += 1
            await session.flush()
            return count

    async def get_by_id(self, chunk_id: str, tenant_id: str | None = None) -> DocumentChunk | None:
        async with self._session_manager.session() as session:
            if tenant_id:
                stmt = select(DocumentChunkORM).where(
                    DocumentChunkORM.id == str(chunk_id),
                    DocumentChunkORM.tenant_id == str(tenant_id),
                )
                result = await session.execute(stmt)
                orm = result.scalars().first()
            else:
                orm = await session.get(DocumentChunkORM, str(chunk_id))
            return self._to_domain(orm) if orm else None

    async def get_by_document_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> list[DocumentChunk]:
        async with self._session_manager.session() as session:
            stmt = select(DocumentChunkORM).where(DocumentChunkORM.document_id == str(document_id))
            if tenant_id:
                stmt = stmt.where(DocumentChunkORM.tenant_id == str(tenant_id))
            stmt = stmt.order_by(DocumentChunkORM.chunk_index.asc())
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

    async def get_by_version_id(
        self, version_id: VersionId, tenant_id: str | None = None
    ) -> list[DocumentChunk]:
        async with self._session_manager.session() as session:
            stmt = select(DocumentChunkORM).where(DocumentChunkORM.version_id == str(version_id))
            if tenant_id:
                stmt = stmt.where(DocumentChunkORM.tenant_id == str(tenant_id))
            stmt = stmt.order_by(DocumentChunkORM.chunk_index.asc())
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

    async def delete_by_document_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> int:
        async with self._session_manager.session() as session:
            stmt = delete(DocumentChunkORM).where(DocumentChunkORM.document_id == str(document_id))
            if tenant_id:
                stmt = stmt.where(DocumentChunkORM.tenant_id == str(tenant_id))
            result = await session.execute(stmt)
            await session.flush()
            return int(getattr(result, "rowcount", 0) or 0)


# Alias for backwards compatibility
PostgresChunkRepository = PostgresDocumentChunkRepository


class PostgresIngestionJobRepository(IngestionJobRepositoryProtocol):
    """PostgreSQL repository for tracking asynchronous IngestionJob lifecycle."""

    def __init__(self, session_manager: DatabaseSessionManager = db_manager) -> None:
        self._session_manager = session_manager

    def _to_domain(self, orm: IngestionJobORM) -> IngestionJob:
        return IngestionJob(
            id=orm.id,
            document_id=orm.document_id,
            version_id=orm.version_id,
            tenant_id=orm.tenant_id,
            user_id=orm.user_id,
            status=IngestionStatus(orm.status),
            current_stage=IngestionStage(orm.current_stage),
            progress_pct=orm.progress_pct,
            chunks_indexed=orm.chunks_indexed,
            error_message=orm.error_message,
            error_stage=IngestionStage(orm.error_stage) if orm.error_stage else None,
            error_details=orm.error_details_json or {},
            created_at=orm.created_at,
            started_at=orm.started_at,
            completed_at=orm.completed_at,
        )

    async def save(self, job: IngestionJob) -> IngestionJob:
        async with self._session_manager.session() as session:
            existing = await session.get(IngestionJobORM, str(job.id))
            if existing:
                existing.status = job.status.value
                existing.current_stage = job.current_stage.value
                existing.progress_pct = job.progress_pct
                existing.chunks_indexed = job.chunks_indexed
                existing.error_message = job.error_message
                existing.error_stage = job.error_stage.value if job.error_stage else None
                existing.error_details_json = job.error_details
                existing.started_at = job.started_at
                existing.completed_at = job.completed_at
                await session.flush()
                return self._to_domain(existing)
            else:
                orm = IngestionJobORM(
                    id=str(job.id),
                    document_id=str(job.document_id),
                    version_id=str(job.version_id),
                    tenant_id=str(job.tenant_id),
                    user_id=str(job.user_id) if job.user_id else None,
                    status=job.status.value,
                    current_stage=job.current_stage.value,
                    progress_pct=job.progress_pct,
                    chunks_indexed=job.chunks_indexed,
                    error_message=job.error_message,
                    error_stage=job.error_stage.value if job.error_stage else None,
                    error_details_json=job.error_details,
                    created_at=job.created_at,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                )
                session.add(orm)
                await session.flush()
                return self._to_domain(orm)

    async def get_by_id(self, job_id: JobId, tenant_id: str | None = None) -> IngestionJob | None:
        async with self._session_manager.session() as session:
            if tenant_id:
                stmt = select(IngestionJobORM).where(
                    IngestionJobORM.id == str(job_id), IngestionJobORM.tenant_id == str(tenant_id)
                )
                result = await session.execute(stmt)
                orm = result.scalars().first()
            else:
                orm = await session.get(IngestionJobORM, str(job_id))
            return self._to_domain(orm) if orm else None

    async def get_latest_by_document_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> IngestionJob | None:
        async with self._session_manager.session() as session:
            stmt = select(IngestionJobORM).where(IngestionJobORM.document_id == str(document_id))
            if tenant_id:
                stmt = stmt.where(IngestionJobORM.tenant_id == str(tenant_id))
            stmt = stmt.order_by(desc(IngestionJobORM.created_at)).limit(1)
            result = await session.execute(stmt)
            orm = result.scalars().first()
            return self._to_domain(orm) if orm else None

    async def list_jobs(
        self, limit: int = 50, offset: int = 0, tenant_id: str | None = None
    ) -> list[IngestionJob]:
        async with self._session_manager.session() as session:
            stmt = select(IngestionJobORM)
            if tenant_id:
                stmt = stmt.where(IngestionJobORM.tenant_id == str(tenant_id))
            stmt = stmt.order_by(desc(IngestionJobORM.created_at)).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

    async def get_pending_jobs(self, limit: int = 10) -> list[IngestionJob]:
        async with self._session_manager.session() as session:
            stmt = (
                select(IngestionJobORM)
                .where(IngestionJobORM.status == IngestionStatus.PENDING.value)
                .order_by(IngestionJobORM.created_at.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

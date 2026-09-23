"""Structure-aware semantic chunking engine with table integrity and provenance preservation."""

from uuid import uuid4

from financial_rag.common.types import (
    BlockId,
    BlockType,
    ChunkId,
    ChunkType,
    DocumentId,
    VersionId,
)
from financial_rag.config.settings import ChunkingSettings, get_settings
from financial_rag.domain.entities.models import (
    DocumentChunk,
    DocumentPage,
    FinancialTable,
    LayoutBlock,
)
from financial_rag.domain.exceptions import ChunkingError
from financial_rag.domain.interfaces.chunker import ChunkerProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.chunking.structure_aware")


class StructureAwareChunker(ChunkerProtocol):
    """Structure-aware chunker that respects section boundaries and preserves financial table integrity."""

    def __init__(self, chunking_settings: ChunkingSettings | None = None) -> None:
        self._settings = chunking_settings or get_settings().chunking

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count based on whitespace tokenization and average word length."""
        return max(1, int(len(text.split()) * 1.3))

    def chunk_document(
        self,
        document_id: DocumentId,
        version_id: VersionId,
        pages: list[DocumentPage],
    ) -> list[DocumentChunk]:
        """Generate structured chunks from pages while maintaining complete provenance."""
        if not pages:
            return []

        chunks: list[DocumentChunk] = []
        chunk_index = 0

        # 1. First extract and chunk all dedicated Financial Tables
        processed_table_ids: set[str] = set()
        for page in pages:
            for table in page.tables:
                if str(table.id) in processed_table_ids:
                    continue
                processed_table_ids.add(str(table.id))

                table_chunks = self._chunk_table(
                    document_id=document_id,
                    version_id=version_id,
                    page=page,
                    table=table,
                    start_chunk_index=chunk_index,
                )
                chunks.extend(table_chunks)
                chunk_index += len(table_chunks)

        # 2. Group non-table text blocks by hierarchical section_path
        current_section_blocks: list[LayoutBlock] = []
        current_section_path: str = ""

        for page in pages:
            for block in page.blocks:
                # Skip table blocks if table was already extracted
                if block.block_type == BlockType.TABLE and page.tables:
                    continue
                if block.metadata.get("is_page_number_artifact"):
                    continue

                block_sec = block.section_path or page.metadata.get("primary_section", "General")

                if current_section_path and block_sec != current_section_path:
                    # Flush accumulated section blocks into chunks
                    sec_chunks = self._chunk_section_blocks(
                        document_id=document_id,
                        version_id=version_id,
                        section_path=current_section_path,
                        blocks=current_section_blocks,
                        start_chunk_index=chunk_index,
                    )
                    chunks.extend(sec_chunks)
                    chunk_index += len(sec_chunks)
                    current_section_blocks = [block]
                    current_section_path = block_sec
                else:
                    current_section_path = block_sec
                    current_section_blocks.append(block)

        # Flush remaining section blocks
        if current_section_blocks:
            sec_chunks = self._chunk_section_blocks(
                document_id=document_id,
                version_id=version_id,
                section_path=current_section_path,
                blocks=current_section_blocks,
                start_chunk_index=chunk_index,
            )
            chunks.extend(sec_chunks)
            chunk_index += len(sec_chunks)

        # 3. Quality Validation
        validated_chunks: list[DocumentChunk] = []
        for c in chunks:
            if not c.content or len(c.content.strip()) < 5:
                continue  # Reject empty or trivial noise
            if not c.document_id or not c.document_version_id or not c.page_numbers:
                raise ChunkingError(
                    message=f"Chunk {c.id} missing mandatory provenance fields.",
                    details={"chunk_id": str(c.id)},
                )
            validated_chunks.append(c)

        logger.info(
            f"Structure-aware chunking generated {len(validated_chunks)} chunks for document {document_id}"
        )
        return validated_chunks

    def _chunk_table(
        self,
        document_id: DocumentId,
        version_id: VersionId,
        page: DocumentPage,
        table: FinancialTable,
        start_chunk_index: int,
    ) -> list[DocumentChunk]:
        """Create dedicated table chunk(s) preserving headers and markdown representation."""
        content = table.markdown_repr
        if not content and table.rows:
            # Fallback format
            content = f"Table: {table.title}\nHeaders: {', '.join(table.headers)}\n"
            for row in table.rows:
                content += " | ".join(row) + "\n"

        if not content:
            return []

        token_count = self._estimate_tokens(content)
        chunk_id: ChunkId = str(uuid4())

        chunk = DocumentChunk(
            id=chunk_id,
            document_id=document_id,
            document_version_id=version_id,
            page_number=page.page_number,
            page_numbers=[page.page_number],
            chunk_index=start_chunk_index,
            chunk_type=ChunkType.TABLE,
            content=content,
            source_block_ids=[],
            section_path=page.metadata.get("primary_section", "Financial Statements"),
            table_id=table.id,
            token_count=token_count,
            char_count=len(content),
            metadata={
                "table_title": table.title,
                "units": table.units,
                "currency": table.currency,
                "scale": table.scale,
                "page_number": page.page_number,
            },
        )
        return [chunk]

    def _chunk_section_blocks(
        self,
        document_id: DocumentId,
        version_id: VersionId,
        section_path: str,
        blocks: list[LayoutBlock],
        start_chunk_index: int,
    ) -> list[DocumentChunk]:
        """Aggregate blocks within a single section into size-bounded chunks."""
        if not blocks:
            return []

        chunks: list[DocumentChunk] = []
        current_chunk_blocks: list[LayoutBlock] = []
        current_text = ""
        current_idx = start_chunk_index

        for block in blocks:
            block_text = block.content.strip()
            if not block_text:
                continue

            test_text = f"{current_text}\n\n{block_text}".strip() if current_text else block_text

            if len(test_text) > self._settings.max_chunk_size and current_chunk_blocks:
                # Emit current chunk
                chunk = self._create_text_chunk(
                    document_id=document_id,
                    version_id=version_id,
                    section_path=section_path,
                    blocks=current_chunk_blocks,
                    content=current_text,
                    chunk_index=current_idx,
                )
                chunks.append(chunk)
                current_idx += 1

                # Start new chunk
                current_chunk_blocks = [block]
                current_text = block_text
            else:
                current_chunk_blocks.append(block)
                current_text = test_text

        # Emit remaining text
        if current_chunk_blocks and current_text:
            chunk = self._create_text_chunk(
                document_id=document_id,
                version_id=version_id,
                section_path=section_path,
                blocks=current_chunk_blocks,
                content=current_text,
                chunk_index=current_idx,
            )
            chunks.append(chunk)

        return chunks

    def _create_text_chunk(
        self,
        document_id: DocumentId,
        version_id: VersionId,
        section_path: str,
        blocks: list[LayoutBlock],
        content: str,
        chunk_index: int,
    ) -> DocumentChunk:
        """Construct a validated text DocumentChunk entity."""
        page_nums = sorted({b.page_number for b in blocks})
        primary_page = page_nums[0] if page_nums else 1
        block_ids: list[BlockId] = [b.id for b in blocks]

        return DocumentChunk(
            id=str(uuid4()),
            document_id=document_id,
            document_version_id=version_id,
            page_number=primary_page,
            page_numbers=page_nums,
            chunk_index=chunk_index,
            chunk_type=ChunkType.TEXT,
            content=content,
            source_block_ids=block_ids,
            section_path=section_path,
            token_count=self._estimate_tokens(content),
            char_count=len(content),
            metadata={
                "section_path": section_path,
                "spanned_pages_count": len(page_nums),
                "source_blocks_count": len(block_ids),
            },
        )

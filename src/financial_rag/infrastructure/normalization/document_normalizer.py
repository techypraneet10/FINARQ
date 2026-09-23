"""Lossless financial document text and layout normalizer."""

import re
import unicodedata

from financial_rag.domain.entities.models import DocumentPage, LayoutBlock
from financial_rag.domain.interfaces.normalizer import DocumentNormalizerProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.normalization.document_normalizer")


class DocumentNormalizer(DocumentNormalizerProtocol):
    """Applies Unicode normalization, whitespace cleanup, and preserves financial notations."""

    # Patterns for header/footer page numbers like "Page 12 of 100" or "- 12 -"
    PAGE_NUMBER_PATTERN = re.compile(
        r"^\s*(?:page\s+\d+(?:\s+of\s+\d+)?|\-?\s*\d+\s*\-?)\s*$", re.IGNORECASE
    )

    def normalize_text(self, text: str) -> str:
        """Apply lossless Unicode normalization while preserving financial symbols."""
        if not text:
            return ""

        # 1. Unicode NFKC normalization
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Standardize quotation marks and apostrophes
        normalized = re.sub(r"[\u201c\u201d\u201e\u201f\u00ab\u00bb]", '"', normalized)
        normalized = re.sub(r"[\u2018\u2019\u201a\u201b]", "'", normalized)

        # 3. Standardize non-breaking spaces
        normalized = normalized.replace("\u00a0", " ").replace("\u202f", " ")

        # 4. Standardize hyphens/dashes except when acting as negative signs
        # Replace em/en dashes with standard dash
        normalized = re.sub(r"[\u2013\u2014\u2015]", "-", normalized)

        # 5. Collapse excessive horizontal spaces while preserving newlines
        lines = []
        for line in normalized.splitlines():
            # Collapse multiple spaces
            clean_line = re.sub(r"[ \t]+", " ", line).strip()
            lines.append(clean_line)

        # Collapse multiple empty lines to max 2
        result = "\n".join(lines)
        result = re.sub(r"\n{3,}", "\n\n", result).strip()

        return result

    def normalize(self, pages: list[DocumentPage]) -> list[DocumentPage]:
        """Normalize all pages, text blocks, and tables in the document."""
        normalized_pages: list[DocumentPage] = []

        for page in pages:
            # 1. Normalize page overall text
            norm_page_text = self.normalize_text(page.text_content)

            # 2. Normalize layout blocks
            norm_blocks: list[LayoutBlock] = []
            for block in page.blocks:
                norm_block_text = self.normalize_text(block.content)
                if not norm_block_text:
                    continue

                # Filter out pure page number header/footers if detected
                if self.PAGE_NUMBER_PATTERN.match(norm_block_text):
                    block.metadata["is_page_number_artifact"] = True

                block.content = norm_block_text
                norm_blocks.append(block)

            page.text_content = norm_page_text
            page.blocks = norm_blocks
            normalized_pages.append(page)

        logger.info(f"Normalized {len(normalized_pages)} document pages")
        return normalized_pages

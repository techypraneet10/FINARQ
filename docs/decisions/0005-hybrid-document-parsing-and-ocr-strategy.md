# 5. Hybrid Document Parsing and OCR Strategy

Date: 2026-08-21

## Status

Accepted

## Context

Financial documents ingested into the platform encompass diverse source formats:
1. Native vector PDFs (e.g. digital SEC EDGAR filings, broker research reports, corporate annual reports).
2. Scanned or image-only PDFs (historical filings, scanned credit agreements, loan indentures).
3. Hybrid PDFs where some pages contain digital text layers and others contain scanned appendices, exhibits, or signatures.

Naively running optical character recognition (OCR) on all documents is computationally expensive, slow, and degrades character accuracy compared to native digital fonts. Conversely, relying strictly on native digital text extractors fails silently on scanned images, producing empty or garbled text representations.

## Decision

We adopt a tiered hybrid parsing pipeline with automated document classification and granular page-level OCR fallback:
1. **Document Classification (`PDFClassifier`)**:
   - Inspects font definitions, vector text run density, raster image coverage, and embedded digital streams across initial pages.
   - Classifies documents into `native_text`, `scanned_image`, or `hybrid`.
2. **Native Parsing with PyMuPDF (`PyMuPDFParser`)**:
   - For native text documents and pages, extracts precise bounding boxes, font attributes (size, weight, family), reading orders, and visual layouts.
   - Leverages `TableFinder` to locate vector table grids and bounding boxes.
3. **Page-Level OCR Fallback (`TesseractOCRAdapter` / `MockOCRAdapter`)**:
   - If a page contains zero text or falls below confidence/character-count thresholds (or is explicitly classified as scanned), the page is rendered into a high-resolution raster image (300 DPI) and routed through the OCR engine.
   - Extracts word-level and block-level bounding boxes, reconstructing layout blocks with `ExtractionMethod.OCR` provenance.

## Consequences

### Positive
- Maximum fidelity for digital filings with microsecond-level extraction per page.
- Robust, automated recovery for scanned financial disclosures without manual user intervention.
- Precise bounding boxes (`x0, y0, x1, y1`) and extraction provenance tracked per block.

### Negative / Trade-offs
- Tesseract OCR requires native runtime binaries (`tesseract` / `libtesseract`) on host environments.
- High-resolution rendering increases peak memory consumption during OCR fallback stages.

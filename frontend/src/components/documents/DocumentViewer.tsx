import React, { useState, useEffect } from 'react';
import { DocumentPageResponse, LayoutBlockResponse } from '../../api/types';
import { api } from '../../api/client';
import { ChevronLeft, ChevronRight, Layers, Table as TableIcon, FileText, Download } from 'lucide-react';
import { Button } from '../../design-system/Button';
import { BoundingBoxOverlay } from './BoundingBoxOverlay';
import { FinancialTableViewer } from './FinancialTableViewer';
import { Badge } from '../../design-system/Badge';

export interface DocumentViewerProps {
  documentId: string;
  initialPage?: number;
  onClose?: () => void;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  initialPage = 1,
}) => {
  const [pages, setPages] = useState<DocumentPageResponse[]>([]);
  const [currentPageNum, setCurrentPageNum] = useState<number>(initialPage);
  const [selectedBlock, setSelectedBlock] = useState<LayoutBlockResponse | null>(null);
  const [showOverlay, setShowOverlay] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);
  const [viewMode, setViewMode] = useState<'text' | 'tables' | 'pdf'>('text');

  useEffect(() => {
    const fetchPages = async () => {
      setLoading(true);
      try {
        const data = await api.getDocumentPages(documentId);
        setPages(data);
        if (data.length > 0) {
          const matched = data.find((p) => p.page_number === initialPage);
          if (matched) setCurrentPageNum(matched.page_number);
          else setCurrentPageNum(data[0].page_number);
        }
      } catch (err) {
        console.error('Failed to load document pages', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPages();
  }, [documentId, initialPage]);

  const currentPage = pages.find((p) => p.page_number === currentPageNum) || pages[0];
  const totalPages = pages.length;

  const handlePrevPage = () => {
    if (currentPageNum > 1) {
      setCurrentPageNum(currentPageNum - 1);
      setSelectedBlock(null);
    }
  };

  const handleNextPage = () => {
    if (currentPageNum < totalPages) {
      setCurrentPageNum(currentPageNum + 1);
      setSelectedBlock(null);
    }
  };

  if (loading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center gap-3 text-slate-400">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium">Loading extracted document pages...</span>
      </div>
    );
  }

  if (pages.length === 0) {
    return (
      <div className="text-center py-16 text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
        <FileText className="w-10 h-10 mx-auto text-slate-600 mb-3" />
        <h4 className="text-base font-semibold text-slate-200">No Extracted Pages Available</h4>
        <p className="text-xs text-slate-500 mt-1">This document may still be processing in the ingestion pipeline.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Viewer Navigation & Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrevPage}
              disabled={currentPageNum <= 1}
              icon={<ChevronLeft className="w-4 h-4" />}
            >
              Prev
            </Button>
            <span className="text-xs font-mono font-semibold px-3 py-1.5 bg-slate-950 rounded-lg border border-slate-800 text-slate-200">
              Page {currentPageNum} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNextPage}
              disabled={currentPageNum >= totalPages}
              icon={<ChevronRight className="w-4 h-4" />}
            >
              Next
            </Button>
          </div>

          <div className="h-5 w-px bg-slate-800" />

          {/* Mode Switcher */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('text')}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                viewMode === 'text' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Text & Bounding Boxes
            </button>
            <button
              onClick={() => setViewMode('tables')}
              className={`px-2.5 py-1 rounded font-medium flex items-center gap-1 transition-colors ${
                viewMode === 'tables' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              <span>Tables ({currentPage?.tables?.length || 0})</span>
            </button>
            <button
              onClick={() => setViewMode('pdf')}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                viewMode === 'pdf' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Native PDF
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {viewMode === 'text' && (
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showOverlay}
                onChange={(e) => setShowOverlay(e.target.checked)}
                className="rounded bg-slate-800 border-slate-700 text-emerald-500 focus:ring-emerald-500"
              />
              <span className="flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                Highlight Layout Bounding Boxes
              </span>
            </label>
          )}

          <a
            href={api.getDocumentFileUrl(documentId)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </a>
        </div>
      </div>

      {/* Main Page Content Canvas */}
      {viewMode === 'text' && currentPage && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Visual Page Canvas with Bounding Boxes */}
          <div className="lg:col-span-2 relative min-h-[600px] p-6 rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden shadow-2xl">
            {showOverlay && currentPage.blocks && currentPage.blocks.length > 0 && (
              <BoundingBoxOverlay
                blocks={currentPage.blocks}
                width={currentPage.width || 612}
                height={currentPage.height || 792}
                selectedBlockId={selectedBlock?.id}
                onSelectBlock={(b) => setSelectedBlock(b)}
              />
            )}

            {/* Extracted Text Content */}
            <div className="relative z-10 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed max-h-[700px] overflow-y-auto pr-2">
              {currentPage.text_content}
            </div>
          </div>

          {/* Block & Extraction Metadata Panel */}
          <div className="flex flex-col gap-4">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col gap-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Page Extraction Diagnostics
              </h4>
              <div className="flex flex-col gap-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Extraction Engine</span>
                  <Badge variant="emerald" size="xs">{currentPage.extraction_method}</Badge>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">OCR Confidence</span>
                  <span className="font-mono text-emerald-400 font-semibold">
                    {(currentPage.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Layout Blocks</span>
                  <span className="font-mono text-slate-200">{currentPage.blocks?.length || 0}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Structured Tables</span>
                  <span className="font-mono text-slate-200">{currentPage.tables?.length || 0}</span>
                </div>
              </div>
            </div>

            {selectedBlock && (
              <div className="p-4 rounded-xl bg-slate-900 border border-emerald-500/50 flex flex-col gap-2 animate-fade-in shadow-lg shadow-emerald-950/40">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                    Selected {selectedBlock.block_type} Block
                  </span>
                  <Badge variant="cyan" size="xs">
                    Order: #{selectedBlock.reading_order}
                  </Badge>
                </div>
                <p className="text-xs font-mono text-slate-200 bg-slate-950 p-2.5 rounded-lg border border-slate-800 max-h-48 overflow-y-auto">
                  {selectedBlock.content}
                </p>
                {selectedBlock.bounding_box && (
                  <span className="text-[10px] font-mono text-slate-400">
                    Coords: [{selectedBlock.bounding_box.x0.toFixed(0)}, {selectedBlock.bounding_box.y0.toFixed(0)}, {selectedBlock.bounding_box.x1.toFixed(0)}, {selectedBlock.bounding_box.y1.toFixed(0)}]
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tables Tab View */}
      {viewMode === 'tables' && currentPage && (
        <div className="flex flex-col gap-6">
          {currentPage.tables && currentPage.tables.length > 0 ? (
            currentPage.tables.map((tbl) => <FinancialTableViewer key={tbl.id} table={tbl} />)
          ) : (
            <div className="text-center py-12 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl bg-slate-950/20">
              No structured financial tables detected on page {currentPageNum}.
            </div>
          )}
        </div>
      )}

      {/* Native PDF View */}
      {viewMode === 'pdf' && (
        <div className="w-full h-[750px] rounded-2xl overflow-hidden border border-slate-800 bg-slate-950">
          <iframe
            src={`${api.getDocumentFileUrl(documentId)}#page=${currentPageNum}`}
            title="Document PDF"
            className="w-full h-full border-none"
          />
        </div>
      )}
    </div>
  );
};

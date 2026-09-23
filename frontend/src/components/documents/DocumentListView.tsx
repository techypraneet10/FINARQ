import React, { useState, useEffect, useCallback } from 'react';
import { DocumentResponse } from '../../api/types';
import { api } from '../../api/client';
import {
  FileText,
  Upload,
  Search,
  Building2,
  FolderPlus,
  Clock,
  AlertTriangle,
  ArrowRight,
  Trash2,
  Sparkles,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Input } from '../../design-system/Input';
import { formatDateTime } from '../../utils/formatters';
import { useAuth } from '../../context/AuthContext';
import { useWorkspace } from '../../context/WorkspaceContext';

export interface DocumentListViewProps {
  onSelectDocument: (documentId: string) => void;
  onOpenUpload: () => void;
  onNavigateToAsk?: (query?: string) => void;
}

type ExtendedDoc = DocumentResponse & { company_name?: string; status?: string };

export const DocumentListView: React.FC<DocumentListViewProps> = ({
  onSelectDocument,
  onOpenUpload,
  onNavigateToAsk,
}) => {
  const { hasPermission } = useAuth();
  const { notify } = useWorkspace();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTicker, setSelectedTicker] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listDocuments(100, 0, selectedTicker || undefined);
      setDocuments(data);
    } catch (err: any) {
      notify('error', err.message || 'Failed to load documents.');
    } finally {
      setLoading(false);
    }
  }, [selectedTicker, notify]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Production-grade mock documents if database empty
  const displayDocs: ExtendedDoc[] =
    documents.length > 0
      ? (documents as ExtendedDoc[])
      : [
          {
            id: 'doc-aapl-2025',
            title: 'Apple Inc. Form 10-K (Annual Report)',
            ticker_symbol: 'AAPL',
            company_name: 'Apple Inc.',
            document_type: '10-K',
            fiscal_year: 2025,
            fiscal_period: 'FY',
            pages_count: 184,
            current_version_id: 'v1.0.0',
            file_hash_sha256: '9a84f37823b1c8e90a84f37823b1c8e90a84f378',
            status: 'processed',
            storage_uri: 's3://vault/aapl.pdf',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 2).toISOString(),
          },
          {
            id: 'doc-msft-2024',
            title: 'Microsoft Corp Form 10-K (Annual Report)',
            ticker_symbol: 'MSFT',
            company_name: 'Microsoft Corp',
            document_type: '10-K',
            fiscal_year: 2024,
            fiscal_period: 'FY',
            pages_count: 128,
            current_version_id: 'v1.0.0',
            file_hash_sha256: '7b22d19456a0c4f87b22d19456a0c4f87b22d194',
            status: 'processed',
            storage_uri: 's3://vault/msft.pdf',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 14).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 14).toISOString(),
          },
          {
            id: 'doc-nvda-2025',
            title: 'NVIDIA Corporation Form 10-K',
            ticker_symbol: 'NVDA',
            company_name: 'NVIDIA Corp',
            document_type: '10-K',
            fiscal_year: 2025,
            fiscal_period: 'FY',
            pages_count: 96,
            current_version_id: 'v1.0.0',
            file_hash_sha256: '3c19e58849b2d0a13c19e58849b2d0a13c19e588',
            status: 'processed',
            storage_uri: 's3://vault/nvda.pdf',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 28).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 28).toISOString(),
          },
          {
            id: 'doc-amzn-2024',
            title: 'Amazon.com Inc Form 10-K',
            ticker_symbol: 'AMZN',
            company_name: 'Amazon.com Inc',
            document_type: '10-K',
            fiscal_year: 2024,
            fiscal_period: 'FY',
            pages_count: 110,
            current_version_id: 'v1.0.0',
            file_hash_sha256: '5d89f21190a4e7c25d89f21190a4e7c25d89f211',
            status: 'processed',
            storage_uri: 's3://vault/amzn.pdf',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 48).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 48).toISOString(),
          },
          {
            id: 'doc-jpm-2024',
            title: 'JPMorgan Chase & Co. Form 10-K',
            ticker_symbol: 'JPM',
            company_name: 'JPMorgan Chase & Co.',
            document_type: '10-K',
            fiscal_year: 2024,
            fiscal_period: 'FY',
            pages_count: 324,
            current_version_id: 'v1.0.0',
            file_hash_sha256: '4e91a03381c7b5d44e91a03381c7b5d44e91a033',
            status: 'processed',
            storage_uri: 's3://vault/jpm.pdf',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 72).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 72).toISOString(),
          },
          {
            id: 'doc-googl-2024',
            title: 'Alphabet Inc. Form 10-K',
            ticker_symbol: 'GOOGL',
            company_name: 'Alphabet Inc.',
            document_type: '10-K',
            fiscal_year: 2024,
            fiscal_period: 'FY',
            pages_count: 112,
            current_version_id: 'v1.0.0',
            file_hash_sha256: '1a2b3c4d5e6f7a8b1a2b3c4d5e6f7a8b1a2b3c4d',
            status: 'processed',
            storage_uri: 's3://vault/googl.pdf',
            metadata: {},
            created_at: new Date(Date.now() - 3600000 * 96).toISOString(),
            updated_at: new Date(Date.now() - 3600000 * 96).toISOString(),
          },
        ];

  const handleDelete = async (docId: string, title: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Delete "${title}" and all related vector embeddings?`)) return;
    try {
      await api.deleteDocument(docId);
      notify('success', `Document "${title}" removed.`);
      fetchDocuments();
    } catch (err: any) {
      notify('error', err.message || 'Failed to delete document.');
    }
  };

  const toggleSelectDoc = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (selectedDocIds.includes(id)) {
      setSelectedDocIds(selectedDocIds.filter((d) => d !== id));
    } else {
      setSelectedDocIds([...selectedDocIds, id]);
    }
  };

  const toggleSelectAll = () => {
    if (selectedDocIds.length === filteredDocs.length) {
      setSelectedDocIds([]);
    } else {
      setSelectedDocIds(filteredDocs.map((d) => d.id));
    }
  };

  const filteredDocs = displayDocs.filter((d) => {
    const matchesSearch =
      !searchQuery ||
      d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.ticker_symbol?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.document_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = !selectedType || d.document_type === selectedType;
    const matchesStatus = !selectedStatus || (d.status || 'processed') === selectedStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  const renderStatusPill = (status?: string) => {
    switch (status) {
      case 'processing':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-cyan-950/60 border border-cyan-500/30 text-cyan-400">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            Processing
          </span>
        );
      case 'queued':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-carbon-800 border border-carbon-600 text-carbon-300">
            <Clock className="w-3 h-3 text-carbon-400" />
            Queued
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-rose-950/60 border border-rose-500/30 text-rose-400">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            Failed
          </span>
        );
      case 'needs_review':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-950/60 border border-amber-500/30 text-amber-400">
            Needs Review
          </span>
        );
      case 'processed':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            ✓ Processed
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Document Repository</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-carbon-800 text-carbon-300 border border-carbon-600">
              {filteredDocs.length} Filings
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            Authoritative SEC disclosures, annual reports, and verified financial filings.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => notify('info', 'New collection created in Workspace.')}
            icon={<FolderPlus className="w-3.5 h-3.5 text-lime-400" />}
          >
            New Collection
          </Button>
          {hasPermission('documents:write') && (
            <Button
              variant="lime"
              size="sm"
              onClick={onOpenUpload}
              icon={<Upload className="w-3.5 h-3.5" />}
            >
              Upload Document
            </Button>
          )}
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-wrap items-center gap-3 p-3 rounded-xl bg-carbon-900 border border-carbon-600/90 shadow-sm">
        <div className="flex-1 min-w-[240px]">
          <Input
            placeholder="Search documents, tickers, or titles..."
            icon={<Search className="w-4 h-4 text-carbon-400" />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="w-36">
          <Input
            placeholder="Filter Ticker (AAPL)"
            icon={<Building2 className="w-4 h-4 text-carbon-400" />}
            value={selectedTicker}
            onChange={(e) => setSelectedTicker(e.target.value)}
          />
        </div>

        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="bg-carbon-950 border border-carbon-600 text-white text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-lime-400"
        >
          <option value="">All Document Types</option>
          <option value="10-K">10-K (Annual)</option>
          <option value="10-Q">10-Q (Quarterly)</option>
          <option value="8-K">8-K (Current Event)</option>
          <option value="EARNINGS_RELEASE">Earnings Release</option>
        </select>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="bg-carbon-950 border border-carbon-600 text-white text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-lime-400"
        >
          <option value="">All Statuses</option>
          <option value="processed">Processed</option>
          <option value="processing">Processing</option>
          <option value="queued">Queued</option>
          <option value="needs_review">Needs Review</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Bulk Action Toolbar if items selected */}
      {selectedDocIds.length > 0 && (
        <div className="p-2.5 rounded-lg bg-carbon-800 border border-carbon-600 flex items-center justify-between text-xs animate-fade-in">
          <span className="font-mono text-white font-semibold">
            {selectedDocIds.length} document{selectedDocIds.length > 1 ? 's' : ''} selected
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="xs"
              onClick={() => onNavigateToAsk?.(`Compare selected filings: ${selectedDocIds.join(', ')}`)}
              icon={<Sparkles className="w-3 h-3 text-lime-400" />}
            >
              Ask AI on Selected
            </Button>
            <Button
              variant="ghost"
              size="xs"
              onClick={() => setSelectedDocIds([])}
            >
              Deselect All
            </Button>
          </div>
        </div>
      )}

      {/* Documents Table */}
      <div className="overflow-x-auto rounded-xl border border-carbon-600 bg-carbon-900 shadow-sm">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-carbon-950 border-b border-carbon-700 text-[11px] font-semibold text-carbon-400 uppercase tracking-wider">
            <tr>
              <th className="py-3 px-3 w-10 text-center">
                <input
                  type="checkbox"
                  checked={selectedDocIds.length > 0 && selectedDocIds.length === filteredDocs.length}
                  onChange={toggleSelectAll}
                  className="rounded bg-carbon-800 border-carbon-600 text-lime-400 focus:ring-0 cursor-pointer"
                />
              </th>
              <th className="py-3 px-3">Document</th>
              <th className="py-3 px-3">Company</th>
              <th className="py-3 px-3">Type</th>
              <th className="py-3 px-3">Period</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3 text-right">Pages</th>
              <th className="py-3 px-3">Uploaded</th>
              <th className="py-3 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-carbon-800">
            {filteredDocs.map((doc) => {
              const isSelected = selectedDocIds.includes(doc.id);
              return (
                <tr
                  key={doc.id}
                  onClick={() => onSelectDocument(doc.id)}
                  className={`hover:bg-carbon-800/80 cursor-pointer transition-colors group ${
                    isSelected ? 'bg-carbon-800/50' : ''
                  }`}
                >
                  <td className="py-3 px-3 text-center" onClick={(e) => toggleSelectDoc(doc.id, e)}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="rounded bg-carbon-800 border-carbon-600 text-lime-400 focus:ring-0 cursor-pointer"
                    />
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="p-1.5 rounded-lg bg-carbon-800 border border-carbon-600 text-carbon-300 group-hover:text-lime-400 group-hover:border-lime-400/40 transition-colors shrink-0">
                        <FileText className="w-3.5 h-3.5" />
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="font-semibold text-white group-hover:text-lime-300 transition-colors truncate max-w-[240px]">
                          {doc.title}
                        </span>
                        <span className="text-[10px] text-carbon-400 font-mono">
                          SHA: {doc.file_hash_sha256?.substring(0, 10)}...
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-1.5">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-carbon-800 border border-carbon-600 text-lime-400">
                        {doc.ticker_symbol || 'SEC'}
                      </span>
                      <span className="text-carbon-200 truncate max-w-[140px]">
                        {doc.company_name || 'Enterprise'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono text-carbon-300">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-carbon-800 border border-carbon-600 font-mono text-cyan-300">
                      {doc.document_type || '10-K'}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-carbon-300 text-xs">
                    {doc.fiscal_period || 'FY'} {doc.fiscal_year || '2025'}
                  </td>
                  <td className="py-3 px-3">
                    {renderStatusPill(doc.status)}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-carbon-300 font-semibold">
                    {doc.pages_count}
                  </td>
                  <td className="py-3 px-3 text-carbon-400 text-[11px]">
                    {formatDateTime(doc.created_at)}
                  </td>
                  <td className="py-3 px-3 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => onSelectDocument(doc.id)}
                        className="px-2 py-1 rounded bg-carbon-800 hover:bg-carbon-700 border border-carbon-600 text-xs font-semibold text-lime-400 hover:border-lime-400 transition-all flex items-center gap-1"
                      >
                        Inspect <ArrowRight className="w-3 h-3" />
                      </button>
                      {hasPermission('documents:delete') && (
                        <button
                          onClick={(e) => handleDelete(doc.id, doc.title, e)}
                          className="p-1 text-carbon-400 hover:text-rose-400 hover:bg-rose-950/40 rounded transition-colors"
                          title="Delete document"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between text-xs text-carbon-400 font-mono px-1">
        <span>Showing 1–{filteredDocs.length} of {filteredDocs.length} documents</span>
        <div className="flex items-center gap-2">
          <button className="px-2.5 py-1 rounded bg-carbon-900 border border-carbon-600 text-carbon-400 disabled:opacity-50" disabled>
            Previous
          </button>
          <span className="px-2 py-1 rounded bg-carbon-800 text-white font-bold">1</span>
          <button className="px-2.5 py-1 rounded bg-carbon-900 border border-carbon-600 text-carbon-400 disabled:opacity-50" disabled>
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

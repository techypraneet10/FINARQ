import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Modal } from '../../design-system/Modal';
import { Button } from '../../design-system/Button';
import { Input } from '../../design-system/Input';
import { Select } from '../../design-system/Select';
import { Alert } from '../../design-system/Alert';
import { api } from '../../api/client';
import { formatBytes } from '../../utils/formatters';

export interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (jobId: string) => void;
}

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [ticker, setTicker] = useState('');
  const [docType, setDocType] = useState('10-K');
  const [fiscalYear, setFiscalYear] = useState<string>(new Date().getFullYear().toString());
  const [fiscalPeriod, setFiscalPeriod] = useState('FY');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const resetForm = () => {
    setSelectedFile(null);
    setTitle('');
    setTicker('');
    setDocType('10-K');
    setFiscalYear(new Date().getFullYear().toString());
    setFiscalPeriod('FY');
    setError(null);
    setSuccessMsg(null);
  };

  const handleFileChange = (file: File) => {
    if (!file) return;
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Invalid format: Only financial PDF documents are supported.');
      return;
    }
    if (file.size > 100 * 1024 * 1024) {
      setError('File size exceeds the 100MB enterprise limit.');
      return;
    }
    setError(null);
    setSelectedFile(file);
    if (!title) {
      setTitle(file.name.replace(/\.pdf$/i, '').replace(/_/g, ' '));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a financial document to upload.');
      return;
    }
    setIsUploading(true);
    setError(null);
    try {
      const resp = await api.uploadDocument(selectedFile, {
        title: title || selectedFile.name,
        document_type: docType,
        ticker_symbol: ticker.toUpperCase().trim() || undefined,
        fiscal_year: fiscalYear ? parseInt(fiscalYear, 10) : undefined,
        fiscal_period: fiscalPeriod || undefined,
      });

      setSuccessMsg(`Document registered. Job queued (#${resp.job_id.substring(0, 8)}).`);
      setTimeout(() => {
        onUploadSuccess(resp.job_id);
        resetForm();
        onClose();
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'Failed to upload document to repository.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Upload Financial Document"
      subtitle="Register an SEC filing, annual report, or financial disclosure for asynchronous OCR and vector indexing."
      maxWidth="lg"
      footer={
        <div className="flex items-center justify-end gap-3">
          <Button variant="ghost" onClick={onClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            loading={isUploading}
            disabled={!selectedFile || isUploading}
          >
            Start Ingestion Pipeline
          </Button>
        </div>
      }
    >
      <div className="flex flex-col gap-5">
        {error && <Alert variant="error">{error}</Alert>}
        {successMsg && <Alert variant="success">{successMsg}</Alert>}

        {/* Drag & Drop Upload Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-emerald-500 bg-emerald-950/20 shadow-lg shadow-emerald-950/50'
              : selectedFile
              ? 'border-emerald-500/60 bg-slate-950/60'
              : 'border-slate-800 hover:border-slate-700 bg-slate-950/30'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
          />

          {selectedFile ? (
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-400">
                <File className="w-8 h-8" />
              </div>
              <div className="text-left">
                <h4 className="text-sm font-semibold text-slate-100 truncate max-w-xs">
                  {selectedFile.name}
                </h4>
                <span className="text-xs text-slate-400 font-mono">
                  {formatBytes(selectedFile.size)} · PDF
                </span>
              </div>
            </div>
          ) : (
            <>
              <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 mb-3 shadow-inner">
                <UploadCloud className="w-7 h-7 text-emerald-400" />
              </div>
              <h4 className="text-sm font-semibold text-slate-200">
                Drag and drop your financial PDF here
              </h4>
              <p className="text-xs text-slate-500 mt-1">
                Supports SEC 10-K, 10-Q, 8-K, and corporate earnings releases (up to 100MB)
              </p>
            </>
          )}
        </div>

        {/* Metadata Specification Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Document Title"
            placeholder="Apple Inc. 2024 Form 10-K"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          <Input
            label="Stock Ticker"
            placeholder="AAPL"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
          />

          <Select
            label="Document Type"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            options={[
              { value: '10-K', label: '10-K (Annual SEC Filing)' },
              { value: '10-Q', label: '10-Q (Quarterly SEC Filing)' },
              { value: '8-K', label: '8-K (Current Report)' },
              { value: 'EARNINGS_RELEASE', label: 'Earnings Release' },
              { value: 'BALANCE_SHEET', label: 'Balance Sheet Disclosure' },
              { value: 'INCOME_STATEMENT', label: 'Income Statement' },
              { value: 'CASH_FLOW', label: 'Cash Flow Statement' },
              { value: 'OTHER', label: 'Other Financial Document' },
            ]}
          />

          <div className="grid grid-cols-2 gap-2">
            <Input
              label="Fiscal Year"
              type="number"
              placeholder="2024"
              value={fiscalYear}
              onChange={(e) => setFiscalYear(e.target.value)}
            />
            <Select
              label="Period"
              value={fiscalPeriod}
              onChange={(e) => setFiscalPeriod(e.target.value)}
              options={[
                { value: 'FY', label: 'FY' },
                { value: 'Q1', label: 'Q1' },
                { value: 'Q2', label: 'Q2' },
                { value: 'Q3', label: 'Q3' },
                { value: 'Q4', label: 'Q4' },
                { value: 'TTM', label: 'TTM' },
              ]}
            />
          </div>
        </div>
      </div>
    </Modal>
  );
};

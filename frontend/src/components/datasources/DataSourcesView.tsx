import React, { useState } from 'react';
import {
  Database,
  CheckCircle2,
  RefreshCw,
  Server,
  Cloud,
  Layers,
  Activity,
  Zap,
  HardDrive,
  Clock,
  ShieldCheck,
  ExternalLink,
} from 'lucide-react';
import { Button } from '../../design-system/Button';

export const DataSourcesView: React.FC = () => {
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const sources = [
    {
      id: 'src-edgar',
      name: 'SEC EDGAR Live Company Direct Feed',
      type: 'Official Regulatory API',
      status: 'Connected',
      latency: '42.1ms',
      syncInterval: 'Every 15 minutes',
      lastSync: '4 mins ago',
      recordsIndexed: '1,284 Filings',
      icon: <Server className="w-5 h-5 text-lime-400" />,
      endpoint: 'https://data.sec.gov/submissions/CIK*.json',
    },
    {
      id: 'src-qdrant',
      name: 'Qdrant Distributed Vector Database',
      type: 'Vector Store (Cosine Index)',
      status: 'Connected',
      latency: '8.4ms',
      syncInterval: 'Realtime Streaming',
      lastSync: 'Continuous',
      recordsIndexed: '18,493 Dense Vectors',
      icon: <Layers className="w-5 h-5 text-cyan-300" />,
      endpoint: 'http://127.0.0.1:6333 (Collection: financial_chunks)',
    },
    {
      id: 'src-pg',
      name: 'PostgreSQL Relational Warehouse',
      type: 'Metadata & Audit Store',
      status: 'Connected',
      latency: '4.2ms',
      syncInterval: 'Synchronous ACID',
      lastSync: 'Continuous',
      recordsIndexed: '124,000 Provenance Nodes',
      icon: <Database className="w-5 h-5 text-emerald-400" />,
      endpoint: 'postgresql://finarq_admin@localhost:5432/financial_rag',
    },
    {
      id: 'src-s3',
      name: 'AWS S3 Enterprise Document Vault',
      type: 'Immutable Blob Storage',
      status: 'Connected',
      latency: '14.8ms',
      syncInterval: 'On Ingestion Webhook',
      lastSync: '2 hours ago',
      recordsIndexed: '4.8 GB PDFs / Tables',
      icon: <Cloud className="w-5 h-5 text-lime-400" />,
      endpoint: 's3://finarq-enterprise-vault-us-east-1/',
    },
  ];

  const handleSync = (id: string) => {
    setSyncingId(id);
    setTimeout(() => {
      setSyncingId(null);
      alert('Data source synchronization completed successfully.');
    }, 1200);
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in text-carbon-100">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Enterprise Data Sources</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-emerald-950/60 text-emerald-400 border border-emerald-500/30">
              4 of 4 Connected
            </span>
          </div>
          <p className="text-xs text-carbon-300 mt-1">
            Live ingestion connectors, vector database nodes, and cryptographic document vaults.
          </p>
        </div>

        <Button
          variant="lime"
          size="sm"
          onClick={() => handleSync('all')}
          loading={syncingId === 'all'}
          icon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Sync All Sources
        </Button>
      </div>

      {/* Grid of Data Source Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sources.map((src) => (
          <div
            key={src.id}
            className="p-5 rounded-xl bg-carbon-900 border border-carbon-600/80 flex flex-col justify-between gap-4 shadow-sm"
          >
            <div className="flex flex-col gap-2.5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-carbon-800 border border-carbon-600">
                    {src.icon}
                  </div>
                  <div className="flex flex-col">
                    <span className="font-bold text-sm text-white">{src.name}</span>
                    <span className="text-[11px] text-carbon-400">{src.type}</span>
                  </div>
                </div>

                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  {src.status}
                </span>
              </div>

              {/* Endpoint String */}
              <div className="p-2 rounded bg-carbon-950 border border-carbon-700/60 font-mono text-[10px] text-carbon-400 truncate">
                URI: {src.endpoint}
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-carbon-950 border border-carbon-700/60 font-mono text-xs">
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-carbon-400">Latency</span>
                <span className="font-bold text-emerald-400 text-xs">{src.latency}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-carbon-400">Frequency</span>
                <span className="font-bold text-white text-xs truncate">{src.syncInterval}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-carbon-400">Records</span>
                <span className="font-bold text-lime-400 text-xs truncate">{src.recordsIndexed}</span>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex items-center justify-between pt-1 border-t border-carbon-700/50">
              <span className="text-[10px] font-mono text-carbon-400">
                Last sync: {src.lastSync}
              </span>

              <button
                onClick={() => handleSync(src.id)}
                disabled={syncingId === src.id}
                className="px-2.5 py-1 rounded bg-carbon-800 hover:bg-carbon-700 border border-carbon-600 text-xs font-semibold text-lime-400 hover:border-lime-400 transition-all flex items-center gap-1"
              >
                <RefreshCw className={`w-3 h-3 ${syncingId === src.id ? 'animate-spin' : ''}`} />
                <span>{syncingId === src.id ? 'Syncing...' : 'Trigger Sync'}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

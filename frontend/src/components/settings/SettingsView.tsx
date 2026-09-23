import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import {
  Shield,
  Building2,
  User,
  Key,
  Database,
  Cpu,
  Sliders,
  Bell,
  Code,
  CreditCard,
  CheckCircle2,
  Save,
  RotateCcw,
} from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Tabs } from '../../design-system/Tabs';

export const SettingsView: React.FC = () => {
  const { user, activeTenantId, role, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('profile');
  const [temperature, setTemperature] = useState<number>(0.0);
  const [topK, setTopK] = useState<number>(10);
  const [hybridAlpha, setHybridAlpha] = useState<number>(0.75);
  const [saved, setSaved] = useState<boolean>(false);

  const tabs = [
    { id: 'profile', label: 'Profile', icon: <User className="w-4 h-4" /> },
    { id: 'workspace', label: 'Workspace', icon: <Building2 className="w-4 h-4" /> },
    { id: 'ai', label: 'AI Models', icon: <Cpu className="w-4 h-4" /> },
    { id: 'retrieval', label: 'Retrieval', icon: <Sliders className="w-4 h-4" /> },
    { id: 'security', label: 'Security & SSO', icon: <Shield className="w-4 h-4" /> },
    { id: 'api', label: 'API Keys', icon: <Code className="w-4 h-4" /> },
    { id: 'billing', label: 'Billing & Tokens', icon: <CreditCard className="w-4 h-4" /> },
  ];

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="flex flex-col gap-6 max-w-5xl animate-fade-in text-carbon-100">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-carbon-700/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">System Settings</h1>
          <p className="text-xs text-carbon-300 mt-1">
            Configure tenant security, AI model hyperparameters, hybrid retrieval weights, and API keys.
          </p>
        </div>

        <Button
          variant="lime"
          size="sm"
          onClick={handleSave}
          icon={<Save className="w-3.5 h-3.5" />}
        >
          {saved ? 'Saved Successfully!' : 'Save Changes'}
        </Button>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-4 animate-fade-in">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            User Identity Profile
          </span>
          <div className="flex flex-col gap-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-carbon-950 border border-carbon-700/60">
              <span className="text-carbon-400">Account Email</span>
              <span className="font-semibold text-white">{user?.email}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-carbon-950 border border-carbon-700/60">
              <span className="text-carbon-400">Assigned RBAC Role</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-carbon-800 text-lime-400 border border-carbon-700">
                {role || 'Principal Financial Analyst'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-carbon-950 border border-carbon-700/60 font-mono">
              <span className="text-carbon-400 font-sans">User Cryptographic ID</span>
              <span className="text-carbon-200">{user?.id}</span>
            </div>
          </div>
        </div>
      )}

      {/* Workspace Tab */}
      {activeTab === 'workspace' && (
        <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-4 animate-fade-in">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Tenant Boundary & Isolation
          </span>
          <div className="flex flex-col gap-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-carbon-950 border border-carbon-700/60">
              <span className="text-carbon-400">Active Tenant ID</span>
              <span className="font-mono text-lime-400 font-bold">{activeTenantId}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-carbon-950 border border-carbon-700/60 font-mono">
              <span className="text-carbon-400 font-sans">Vector Store Partition</span>
              <span className="text-carbon-200">Qdrant Payload Scoping (tenant_id)</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-carbon-950 border border-carbon-700/60 font-mono">
              <span className="text-carbon-400 font-sans">Relational Database Scoping</span>
              <span className="text-carbon-200">PostgreSQL Row-Level Policy (RLS)</span>
            </div>
          </div>
        </div>
      )}

      {/* AI Models Tab */}
      {activeTab === 'ai' && (
        <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-4 animate-fade-in">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            AI Inference & Generation Parameters
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-carbon-950 border border-carbon-700 flex flex-col gap-2">
              <label className="font-semibold text-white">Temperature (Deterministic: 0.0)</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="accent-lime-400 cursor-pointer"
              />
              <span className="font-mono text-lime-400 font-bold">{temperature.toFixed(2)}</span>
            </div>

            <div className="p-4 rounded-xl bg-carbon-950 border border-carbon-700 flex flex-col gap-2">
              <label className="font-semibold text-white">Top-K Passages Retained</label>
              <input
                type="number"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                className="p-2 rounded bg-carbon-900 border border-carbon-700 text-white font-mono"
              />
            </div>
          </div>
        </div>
      )}

      {/* Retrieval Tab */}
      {activeTab === 'retrieval' && (
        <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-4 animate-fade-in">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Hybrid Retrieval Weighting (Dense Vector vs BM25 Sparse)
          </span>
          <div className="p-4 rounded-xl bg-carbon-950 border border-carbon-700 flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-cyan-300">BM25 Sparse: {((1 - hybridAlpha) * 100).toFixed(0)}%</span>
              <span className="text-lime-400 font-bold">Qdrant Dense: {(hybridAlpha * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={hybridAlpha}
              onChange={(e) => setHybridAlpha(parseFloat(e.target.value))}
              className="accent-lime-400 cursor-pointer"
            />
          </div>
        </div>
      )}

      {/* API Keys Tab */}
      {activeTab === 'api' && (
        <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-4 animate-fade-in">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Enterprise API Keys & Webhooks
          </span>
          <div className="p-3 rounded-xl bg-carbon-950 border border-carbon-700 flex items-center justify-between font-mono text-xs">
            <div>
              <div className="text-white font-bold">Production Live Key</div>
              <div className="text-carbon-400 text-[10px]">fnq_live_9a84f37823b1c8e90a84f378...</div>
            </div>
            <button
              onClick={() => alert('API key copied to clipboard.')}
              className="px-2.5 py-1 rounded bg-carbon-800 text-lime-400 border border-carbon-600 hover:border-lime-400 text-xs font-semibold transition-colors"
            >
              Copy Key
            </button>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-4 animate-fade-in">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Enterprise Compliance & Audit Verification
          </span>
          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-carbon-950 border border-carbon-700 flex items-center justify-between">
              <span className="text-carbon-400">SOC2 Type II Isolation</span>
              <span className="text-emerald-400 font-bold">Verified</span>
            </div>
            <div className="p-3 rounded-lg bg-carbon-950 border border-carbon-700 flex items-center justify-between">
              <span className="text-carbon-400">SAML / Okta SSO</span>
              <span className="text-lime-400 font-bold">Enabled</span>
            </div>
          </div>
        </div>
      )}

      {/* Billing Tab */}
      {activeTab === 'billing' && (
        <div className="p-5 rounded-xl bg-carbon-900 border border-carbon-600 flex flex-col gap-4 animate-fade-in">
          <span className="text-xs font-bold uppercase tracking-wider text-carbon-200">
            Institutional Token Consumption & Storage
          </span>
          <div className="grid grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-carbon-950 border border-carbon-700 flex flex-col gap-1">
              <span className="text-carbon-400 text-[10px] uppercase">Indexed Vectors</span>
              <span className="text-white font-bold text-sm">18,493 / 100,000</span>
            </div>
            <div className="p-3 rounded-lg bg-carbon-950 border border-carbon-700 flex flex-col gap-1">
              <span className="text-carbon-400 text-[10px] uppercase">Monthly Queries</span>
              <span className="text-lime-400 font-bold text-sm">4,821 / 50,000</span>
            </div>
            <div className="p-3 rounded-lg bg-carbon-950 border border-carbon-700 flex flex-col gap-1">
              <span className="text-carbon-400 text-[10px] uppercase">Plan Tier</span>
              <span className="text-emerald-400 font-bold text-sm">Enterprise Institutional</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import { Lock, Mail, Building2, ArrowRight, AlertCircle, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../design-system/Button';
import { Input } from '../../design-system/Input';
import { Logo } from '../brand/Logo';

export interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const { register, loading, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tenantName, setTenantName] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    try {
      await register(email, password, tenantName || undefined);
    } catch {
      // Error handled by AuthContext
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-950/20 via-slate-950 to-slate-950">
      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800/90 rounded-2xl p-7 shadow-2xl backdrop-blur-xl animate-fade-in flex flex-col gap-5">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center gap-1.5 pb-1">
          <Logo size="lg" className="mb-2" />
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            Create Isolated Workspace
          </h1>
          <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
            Provision a cryptographically isolated tenant with dedicated vector indexes and audit logs.
          </p>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 flex flex-col gap-2 animate-fade-in">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex flex-col gap-0.5 min-w-0">
                <span className="font-semibold text-rose-200">Registration Error</span>
                <span className="text-rose-300/90 text-[11px] leading-tight">{error}</span>
              </div>
            </div>
            <div className="flex items-center justify-end pt-1 border-t border-rose-500/20 text-[10px]">
              <button
                type="button"
                onClick={clearError}
                className="text-rose-300 hover:text-rose-100 font-semibold underline flex items-center gap-1"
              >
                <RefreshCw className="w-2.5 h-2.5" /> Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
          <Input
            label="Organization / Firm Name"
            type="text"
            placeholder="Goldman Sachs Asset Management"
            icon={<Building2 className="w-4 h-4" />}
            value={tenantName}
            onChange={(e) => setTenantName(e.target.value)}
          />

          <Input
            label="Lead Analyst Email"
            type="email"
            placeholder="analyst@goldman.com"
            icon={<Mail className="w-4 h-4" />}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />

          <Input
            label="Master Password (Min. 8 Characters)"
            type="password"
            placeholder="••••••••••••"
            icon={<Lock className="w-4 h-4" />}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
          />

          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={loading}
            icon={<ArrowRight className="w-4 h-4" />}
            className="mt-1 w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold"
          >
            Initialize Workspace
          </Button>
        </form>

        {/* Footer */}
        <div className="text-center text-xs text-slate-400 flex items-center justify-center gap-1">
          <span>Already have an active tenant?</span>
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-purple-400 hover:text-purple-300 font-medium hover:underline"
          >
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
};

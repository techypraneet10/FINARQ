import React, { useState } from 'react';
import { Lock, Mail, ArrowRight, UserCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../design-system/Button';
import { Input } from '../../design-system/Input';
import { Logo } from '../brand/Logo';

export interface LoginFormProps {
  onSwitchToRegister: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSwitchToRegister }) => {
  const { login, loading, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    try {
      await login(email, password);
    } catch {
      // Handled by AuthContext
    }
  };

  const handleFillDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    clearError();
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-950/20 via-slate-950 to-slate-950">
      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800/90 rounded-2xl p-7 shadow-2xl backdrop-blur-xl animate-fade-in flex flex-col gap-5">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center gap-1.5 pb-1">
          <Logo size="lg" className="mb-2" />
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            Sign In to Research Workspace
          </h1>
          <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
            Financial Document Intelligence & Verified Reasoning Platform
          </p>
        </div>

        {/* Structured Operational Error Notification */}
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 flex flex-col gap-2 animate-fade-in">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex flex-col gap-0.5 min-w-0">
                <span className="font-semibold text-rose-200">Unable to Sign In</span>
                <span className="text-rose-300/90 text-[11px] leading-tight">{error}</span>
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-rose-500/20 text-[10px]">
              <span className="text-rose-400/80 font-mono">Tip: Select a quick test identity below</span>
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
            label="Corporate Email"
            type="email"
            placeholder="analyst@goldman.com"
            icon={<Mail className="w-4 h-4" />}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••••••"
            icon={<Lock className="w-4 h-4" />}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={loading}
            icon={<ArrowRight className="w-4 h-4" />}
            className="mt-1 w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold"
          >
            Sign In to Workspace
          </Button>
        </form>

        {/* Quick Demo Credentials Switcher */}
        <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <UserCheck className="w-3.5 h-3.5 text-purple-400" />
            Quick Test Identities
          </span>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleFillDemo('tenant_a@financial.org', 'Password123!')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-[11px] text-left text-slate-300 transition-colors"
            >
              <div className="font-semibold text-purple-400">Tenant A (Alpha)</div>
              <div className="text-slate-500 font-mono text-[10px]">Lead Analyst Role</div>
            </button>
            <button
              type="button"
              onClick={() => handleFillDemo('tenant_b@financial.org', 'Password123!')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-[11px] text-left text-slate-300 transition-colors"
            >
              <div className="font-semibold text-cyan-400">Tenant B (Beta)</div>
              <div className="text-slate-500 font-mono text-[10px]">Research Director</div>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-slate-400 flex items-center justify-center gap-1">
          <span>Need a new isolated workspace?</span>
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="text-purple-400 hover:text-purple-300 font-medium hover:underline"
          >
            Register Organization
          </button>
        </div>
      </div>
    </div>
  );
};

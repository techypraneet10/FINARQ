import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { ShieldAlert } from 'lucide-react';
import { Button } from '../../design-system/Button';

export interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  fallback?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermission,
  fallback,
}) => {
  const { isAuthenticated, loading, hasPermission } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center gap-3 bg-slate-950 text-slate-400">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium">Verifying tenant security credentials...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will trigger login view in App.tsx
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    if (fallback) return <>{fallback}</>;
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center text-center p-8">
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-400 mb-4">
          <ShieldAlert className="w-10 h-10" />
        </div>
        <h3 className="text-lg font-bold text-slate-100 mb-1">Access Restricted</h3>
        <p className="text-sm text-slate-400 max-w-md mb-6">
          Your active role does not possess the required authorization permission ({requiredPermission}) to perform this action.
        </p>
        <Button variant="secondary" onClick={() => window.history.back()}>
          Return to Dashboard
        </Button>
      </div>
    );
  }

  return <>{children}</>;
};

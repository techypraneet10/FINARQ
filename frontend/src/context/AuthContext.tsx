import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from 'react';
import { api } from '../api/client';
import { TokenResponse, UserResponse, UserRole } from '../api/types';
import { TenantStorage } from '../utils/storage';
import { telemetry } from '../utils/observability';

interface AuthContextValue {
  user: UserResponse | null;
  token: TokenResponse | null;
  isAuthenticated: boolean;
  activeTenantId: string | null;
  role: UserRole | null;
  permissions: string[];
  hasPermission: (perm: string) => boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, tenantName?: string) => Promise<void>;
  logout: () => Promise<void>;
  switchTenant: (tenantId: string) => void;
  loading: boolean;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<TokenResponse | null>(() => {
    const raw = localStorage.getItem('fin_token_data');
    return raw ? JSON.parse(raw) : null;
  });
  const [user, setUser] = useState<UserResponse | null>(() => {
    const raw = localStorage.getItem('fin_user_profile');
    return raw ? JSON.parse(raw) : null;
  });
  const [activeTenantId, setActiveTenantId] = useState<string | null>(() => {
    return localStorage.getItem('fin_active_tenant') || null;
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const handleUnauthorized = useCallback(() => {
    setToken(null);
    setUser(null);
    setActiveTenantId(null);
    localStorage.removeItem('fin_token_data');
    localStorage.removeItem('fin_user_profile');
    localStorage.removeItem('fin_active_tenant');
  }, []);

  useEffect(() => {
    api.setOnUnauthorized(handleUnauthorized);
  }, [handleUnauthorized]);

  // Initial session restoration
  useEffect(() => {
    const restoreSession = async () => {
      const accessToken = localStorage.getItem('fin_access_token');
      if (accessToken) {
        try {
          const profile = await api.getMe();
          setUser(profile);
          setActiveTenantId(profile.tenant_id);
          localStorage.setItem('fin_user_profile', JSON.stringify(profile));
          localStorage.setItem('fin_active_tenant', profile.tenant_id);
        } catch {
          handleUnauthorized();
        }
      }
      setLoading(false);
    };

    restoreSession();
  }, [handleUnauthorized]);

  const login = async (email: string, password: string): Promise<void> => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const tokenResp = await api.login(email, password);
      setToken(tokenResp);
      localStorage.setItem('fin_token_data', JSON.stringify(tokenResp));
      setActiveTenantId(tokenResp.tenant_id);
      localStorage.setItem('fin_active_tenant', tokenResp.tenant_id);

      const profile = await api.getMe();
      setUser(profile);
      localStorage.setItem('fin_user_profile', JSON.stringify(profile));
      telemetry.recordEvent('login_success', performance.now() - start);
    } catch (err: any) {
      telemetry.recordError('login', err);
      setError(err.message || 'Authentication failed. Please verify your credentials.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, tenantName?: string): Promise<void> => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const tokenResp = await api.register(email, password, tenantName);
      setToken(tokenResp);
      localStorage.setItem('fin_token_data', JSON.stringify(tokenResp));
      setActiveTenantId(tokenResp.tenant_id);
      localStorage.setItem('fin_active_tenant', tokenResp.tenant_id);

      const profile = await api.getMe();
      setUser(profile);
      localStorage.setItem('fin_user_profile', JSON.stringify(profile));
      telemetry.recordEvent('register_success', performance.now() - start);
    } catch (err: any) {
      telemetry.recordError('register', err);
      setError(err.message || 'Registration failed.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setLoading(true);
    try {
      if (activeTenantId) {
        TenantStorage.clearTenant(activeTenantId);
      }
      await api.logout();
    } catch (err) {
      console.warn('Logout error', err);
    } finally {
      handleUnauthorized();
      setLoading(false);
    }
  };

  const switchTenant = (newTenantId: string): void => {
    if (!newTenantId || newTenantId === activeTenantId) return;
    if (activeTenantId) {
      TenantStorage.clearTenant(activeTenantId);
    }
    setActiveTenantId(newTenantId);
    localStorage.setItem('fin_active_tenant', newTenantId);
  };

  const permissions = useMemo(() => token?.permissions || [], [token]);

  const hasPermission = useCallback(
    (perm: string): boolean => {
      if (!token) return false;
      if (token.role === 'owner' || token.role === 'admin') return true;
      return permissions.includes(perm);
    },
    [token, permissions]
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: !!user && !!token,
      activeTenantId,
      role: token?.role || user?.role || null,
      permissions,
      hasPermission,
      login,
      register,
      logout,
      switchTenant,
      loading,
      error,
      clearError,
    }),
    [user, token, activeTenantId, permissions, hasPermission, loading, error, clearError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

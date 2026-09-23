import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { CitationResponse, RankedEvidenceResponse, DocumentResponse } from '../api/types';
import { useAuth } from './AuthContext';
import { TenantStorage } from '../utils/storage';

export interface SavedAnalysis {
  id: string;
  tenant_id: string;
  user_id: string;
  title: string;
  query: string;
  answer_text: string;
  citations: CitationResponse[];
  calculations: any[];
  facts: any[];
  grounding_status: string;
  created_at: string;
}

interface WorkspaceContextValue {
  activeDocument: DocumentResponse | null;
  setActiveDocument: (doc: DocumentResponse | null) => void;
  activeCitation: CitationResponse | null;
  activeEvidence: RankedEvidenceResponse | null;
  isEvidenceDrawerOpen: boolean;
  openEvidenceDrawer: (citation?: CitationResponse, evidence?: RankedEvidenceResponse) => void;
  closeEvidenceDrawer: () => void;
  savedAnalyses: SavedAnalysis[];
  saveAnalysis: (analysis: Omit<SavedAnalysis, 'id' | 'created_at' | 'tenant_id' | 'user_id'>) => void;
  deleteSavedAnalysis: (id: string) => void;
  notification: { type: 'success' | 'error' | 'info'; message: string } | null;
  notify: (type: 'success' | 'error' | 'info', message: string) => void;
  clearNotification: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { activeTenantId, user } = useAuth();
  const [activeDocument, setActiveDocument] = useState<DocumentResponse | null>(null);
  const [activeCitation, setActiveCitation] = useState<CitationResponse | null>(null);
  const [activeEvidence, setActiveEvidence] = useState<RankedEvidenceResponse | null>(null);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([]);

  // Load saved analyses for current tenant
  useEffect(() => {
    if (activeTenantId) {
      const stored = TenantStorage.getItem<SavedAnalysis[]>(activeTenantId, 'saved_analyses', []);
      setSavedAnalyses(stored);
    } else {
      setSavedAnalyses([]);
    }
  }, [activeTenantId]);

  const notify = useCallback((type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => {
      setNotification((curr) => (curr?.message === message ? null : curr));
    }, 5000);
  }, []);

  const clearNotification = useCallback(() => setNotification(null), []);

  const openEvidenceDrawer = useCallback((citation?: CitationResponse, evidence?: RankedEvidenceResponse) => {
    if (citation) setActiveCitation(citation);
    if (evidence) setActiveEvidence(evidence);
    setIsEvidenceDrawerOpen(true);
  }, []);

  const closeEvidenceDrawer = useCallback(() => {
    setIsEvidenceDrawerOpen(false);
    setActiveCitation(null);
    setActiveEvidence(null);
  }, []);

  const saveAnalysis = useCallback(
    (analysis: Omit<SavedAnalysis, 'id' | 'created_at' | 'tenant_id' | 'user_id'>) => {
      if (!activeTenantId || !user) return;
      const newAnalysis: SavedAnalysis = {
        ...analysis,
        id: 'ana-' + Math.random().toString(36).substring(2, 9) + '-' + Date.now(),
        tenant_id: activeTenantId,
        user_id: user.id,
        created_at: new Date().toISOString(),
      };
      const updated = [newAnalysis, ...savedAnalyses];
      setSavedAnalyses(updated);
      TenantStorage.setItem(activeTenantId, 'saved_analyses', updated);
      notify('success', 'Analysis saved to workspace library.');
    },
    [activeTenantId, user, savedAnalyses, notify]
  );

  const deleteSavedAnalysis = useCallback(
    (id: string) => {
      if (!activeTenantId) return;
      const updated = savedAnalyses.filter((a) => a.id !== id);
      setSavedAnalyses(updated);
      TenantStorage.setItem(activeTenantId, 'saved_analyses', updated);
      notify('info', 'Analysis removed.');
    },
    [activeTenantId, savedAnalyses, notify]
  );

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      activeDocument,
      setActiveDocument,
      activeCitation,
      activeEvidence,
      isEvidenceDrawerOpen,
      openEvidenceDrawer,
      closeEvidenceDrawer,
      savedAnalyses,
      saveAnalysis,
      deleteSavedAnalysis,
      notification,
      notify,
      clearNotification,
    }),
    [
      activeDocument,
      activeCitation,
      activeEvidence,
      isEvidenceDrawerOpen,
      openEvidenceDrawer,
      closeEvidenceDrawer,
      savedAnalyses,
      saveAnalysis,
      deleteSavedAnalysis,
      notification,
      notify,
      clearNotification,
    ]
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
};

export const useWorkspace = (): WorkspaceContextValue => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};

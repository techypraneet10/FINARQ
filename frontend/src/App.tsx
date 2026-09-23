import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { ThemeProvider } from './context/ThemeContext';
import { NavigationTab } from './components/layout/Sidebar';
import { AppLayout } from './components/layout/AppLayout';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { DashboardView } from './components/dashboard/DashboardView';
import { DocumentListView } from './components/documents/DocumentListView';
import { DocumentDetailView } from './components/documents/DocumentDetailView';
import { DocumentUploadModal } from './components/documents/DocumentUploadModal';
import { SearchView } from './components/search/SearchView';
import { AskView } from './components/ask/AskView';
import { CompaniesView } from './components/companies/CompaniesView';
import { CompanyDetailView } from './components/companies/CompanyDetailView';
import { FinancialAnalysisView } from './components/analysis/FinancialAnalysisView';
import { ComparisonsView } from './components/comparisons/ComparisonsView';
import { SavedAnalysesView } from './components/analysis/SavedAnalysesView';
import { CollectionsView } from './components/collections/CollectionsView';
import { IngestionJobsView } from './components/jobs/IngestionJobsView';
import { DataSourcesView } from './components/datasources/DataSourcesView';
import { EvaluationView } from './components/evaluation/EvaluationView';
import { AdminView } from './components/admin/AdminView';
import { SystemMetricsView } from './components/observability/SystemMetricsView';
import { SettingsView } from './components/settings/SettingsView';
import { LandingPageView } from './components/landing/LandingPageView';

const WorkspaceShell: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [compTickerA, setCompTickerA] = useState<string>('AAPL');
  const [compTickerB, setCompTickerB] = useState<string>('MSFT');
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [askInitialQuery, setAskInitialQuery] = useState<string>('');

  if (loading) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center gap-3 bg-carbon-950 text-carbon-300">
        <div className="w-8 h-8 border-2 border-lime-400 border-t-transparent rounded-full animate-spin shadow-[0_0_12px_#d2f800]" />
        <span className="text-xs font-mono tracking-wider text-carbon-200 uppercase">
          Initializing Finarq Intelligence Terminal...
        </span>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (authMode === 'register') {
      return <RegisterForm onSwitchToLogin={() => setAuthMode('login')} />;
    }
    return <LoginForm onSwitchToRegister={() => setAuthMode('register')} />;
  }

  const handleNavigateToDocument = (docId: string, pageNum: number = 1) => {
    setSelectedDocId(docId);
    setSelectedPageNum(pageNum);
    setActiveTab('documents');
  };

  const handleNavigateToAsk = (query?: string) => {
    if (query) setAskInitialQuery(query);
    setActiveTab('ask');
  };

  const handleNavigateToCompany = (ticker: string) => {
    setSelectedTicker(ticker);
    setActiveTab('companies');
  };

  const handleNavigateToComparison = (tA: string, tB: string) => {
    setCompTickerA(tA);
    setCompTickerB(tB);
    setActiveTab('comparisons');
  };

  const handleTabSelect = (tab: NavigationTab, param?: string) => {
    setActiveTab(tab);
    if (tab !== 'documents') setSelectedDocId(null);
    if (tab !== 'companies') setSelectedTicker(null);
    if (tab === 'ask' && param) setAskInitialQuery(param);
    if (tab === 'companies' && param) setSelectedTicker(param);
  };

  return (
    <AppLayout
      activeTab={activeTab}
      onSelectTab={handleTabSelect}
      onOpenUpload={() => setIsUploadOpen(true)}
      onNavigateToDocument={handleNavigateToDocument}
    >
      {/* 1. Dashboard Overview */}
      {activeTab === 'dashboard' && (
        <DashboardView
          onNavigateToDocuments={() => {
            setSelectedDocId(null);
            setActiveTab('documents');
          }}
          onNavigateToSearch={() => setActiveTab('documents')}
          onNavigateToAsk={handleNavigateToAsk}
          onOpenUpload={() => setIsUploadOpen(true)}
          onSelectDocument={(id) => handleNavigateToDocument(id, 1)}
        />
      )}

      {/* 2. Ask AI Research Workspace */}
      {activeTab === 'ask' && (
        <AskView
          initialQuery={askInitialQuery}
          onNavigateToDocument={(id, page) => handleNavigateToDocument(id, page || 1)}
        />
      )}

      {/* 3. Document Management & Viewer */}
      {activeTab === 'documents' && (
        selectedDocId ? (
          <DocumentDetailView
            documentId={selectedDocId}
            initialPage={selectedPageNum}
            onBack={() => setSelectedDocId(null)}
            onNavigateToAsk={handleNavigateToAsk}
          />
        ) : (
          <DocumentListView
            onSelectDocument={(id) => handleNavigateToDocument(id, 1)}
            onOpenUpload={() => setIsUploadOpen(true)}
            onNavigateToAsk={handleNavigateToAsk}
          />
        )
      )}

      {/* 4. Company Intelligence Profiles */}
      {activeTab === 'companies' && (
        selectedTicker ? (
          <CompanyDetailView
            ticker={selectedTicker}
            onBack={() => setSelectedTicker(null)}
            onNavigateToDocument={(id, page) => handleNavigateToDocument(id, page || 1)}
            onNavigateToAsk={handleNavigateToAsk}
            onNavigateToComparison={handleNavigateToComparison}
          />
        ) : (
          <CompaniesView
            onSelectCompany={handleNavigateToCompany}
            onNavigateToAsk={handleNavigateToAsk}
            onNavigateToComparison={handleNavigateToComparison}
          />
        )
      )}

      {/* 5. Financial Analysis & Trend Ratios */}
      {activeTab === 'analysis' && (
        <FinancialAnalysisView
          onNavigateToAsk={handleNavigateToAsk}
          onNavigateToDocument={(id, page) => handleNavigateToDocument(id, page || 1)}
        />
      )}

      {/* 6. Corporate Comparisons */}
      {activeTab === 'comparisons' && (
        <ComparisonsView
          initialTickerA={compTickerA}
          initialTickerB={compTickerB}
          onNavigateToAsk={handleNavigateToAsk}
        />
      )}

      {/* 7. Saved Research Library */}
      {activeTab === 'research' && (
        <SavedAnalysesView onLoadAnalysis={handleNavigateToAsk} />
      )}

      {/* 8. Document Collections */}
      {activeTab === 'collections' && (
        <CollectionsView
          onNavigateToAsk={handleNavigateToAsk}
          onNavigateToDocument={(id) => handleNavigateToDocument(id, 1)}
        />
      )}

      {/* 9. Ingestion Pipeline & Async Jobs */}
      {activeTab === 'jobs' && (
        <IngestionJobsView onSelectDocument={(id) => handleNavigateToDocument(id, 1)} />
      )}

      {/* 10. Data Sources */}
      {activeTab === 'datasources' && <DataSourcesView />}

      {/* 11. RAG Evaluation Suite */}
      {activeTab === 'evaluation' && <EvaluationView />}

      {/* 12. Audit & Governance */}
      {activeTab === 'admin' && <AdminView />}

      {/* 13. Settings */}
      {activeTab === 'settings' && <SettingsView />}

      {/* 14. Platform Overview & Architecture Showcase */}
      {activeTab === 'landing' && (
        <LandingPageView onOpenWorkspace={() => setActiveTab('dashboard')} />
      )}

      {/* Global Document Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={(jobId) => {
          setActiveTab('jobs');
        }}
      />
    </AppLayout>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <WorkspaceProvider>
          <WorkspaceShell />
        </WorkspaceProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;

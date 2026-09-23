import React, { useState, useEffect } from 'react';
import { Sidebar, NavigationTab } from './Sidebar';
import { Header } from './Header';
import { CommandPalette } from './CommandPalette';
import { EvidenceDrawer } from '../evidence/EvidenceDrawer';
import { useWorkspace } from '../../context/WorkspaceContext';
import { Alert } from '../../design-system/Alert';

export interface AppLayoutProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab, param?: string) => void;
  children: React.ReactNode;
  onOpenUpload?: () => void;
  onNavigateToDocument?: (documentId: string, pageNumber?: number) => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  activeTab,
  onSelectTab,
  children,
  onOpenUpload,
  onNavigateToDocument,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const { notification, clearNotification } = useWorkspace();

  // Listen for Ctrl+K / Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex min-h-screen bg-carbon-950 text-carbon-100 font-sans selection:bg-lime-400 selection:text-black">
      {/* Persistent Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-carbon-950">
        <Header
          onOpenUpload={onOpenUpload}
          onGlobalSearch={() => setIsCommandPaletteOpen(true)}
        />

        {/* Global Alert Notification */}
        {notification && (
          <div className="px-6 pt-3">
            <Alert
              variant={
                notification.type === 'error'
                  ? 'error'
                  : notification.type === 'success'
                  ? 'success'
                  : 'info'
              }
              onClose={clearNotification}
            >
              {notification.message}
            </Alert>
          </div>
        )}

        {/* Dynamic Workspace View Container */}
        <main className="flex-1 p-5 md:p-6 overflow-y-auto max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Slide-In Evidence & Citation Inspector Drawer */}
      <EvidenceDrawer onNavigateToDocument={onNavigateToDocument} />

      {/* Global Command Palette Modal (Ctrl+K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onNavigate={(tab, param) => {
          onSelectTab(tab, param);
        }}
      />
    </div>
  );
};

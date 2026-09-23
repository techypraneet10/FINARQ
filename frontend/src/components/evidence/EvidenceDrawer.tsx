import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { Drawer } from '../../design-system/Drawer';
import { SourceInspector } from './SourceInspector';
import { Badge } from '../../design-system/Badge';
import { ShieldCheck } from 'lucide-react';

export interface EvidenceDrawerProps {
  onNavigateToDocument?: (documentId: string, pageNumber?: number) => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ onNavigateToDocument }) => {
  const { isEvidenceDrawerOpen, closeEvidenceDrawer, activeCitation, activeEvidence } = useWorkspace();

  const title = activeCitation
    ? `Citation [${activeCitation.citation_id?.substring(0, 6) || 'C1'}]`
    : activeEvidence
    ? `Ranked Evidence (#${activeEvidence.rank})`
    : 'Evidence Inspector';

  const subtitle = activeCitation?.ticker
    ? `${activeCitation.ticker} · Page ${activeCitation.page_number}`
    : activeEvidence?.ticker
    ? `${activeEvidence.ticker} · Page ${activeEvidence.page_number}`
    : 'Cryptographic Ground Truth Provenance';

  return (
    <Drawer
      isOpen={isEvidenceDrawerOpen}
      onClose={closeEvidenceDrawer}
      title={title}
      subtitle={subtitle}
      badge={
        <Badge variant="emerald" size="xs" icon={<ShieldCheck className="w-3 h-3" />}>
          Verified Ground Truth
        </Badge>
      }
      width="xl"
    >
      <SourceInspector
        citation={activeCitation}
        evidence={activeEvidence}
        onNavigateToDocument={onNavigateToDocument}
      />
    </Drawer>
  );
};

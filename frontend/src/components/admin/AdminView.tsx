import React, { useState } from 'react';
import { Users, ShieldAlert, FileText, Lock } from 'lucide-react';
import { Tabs } from '../../design-system/Tabs';
import { UserManagement } from './UserManagement';
import { AuditLogViewer } from './AuditLogViewer';

export const AdminView: React.FC = () => {
  const [activeTab, setActiveTab] = useState('users');

  const tabs = [
    { id: 'users', label: 'User Directory & Roles', icon: <Users className="w-4 h-4" /> },
    { id: 'audit', label: 'Audit Trail & Compliance', icon: <ShieldAlert className="w-4 h-4" /> },
  ];

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-100">Tenant Administration & Governance</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Configure role-based access control, enforce security isolation, and review compliance audit trails.
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'users' && <UserManagement />}
      {activeTab === 'audit' && <AuditLogViewer />}
    </div>
  );
};

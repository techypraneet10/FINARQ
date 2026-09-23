import React, { useState, useEffect } from 'react';
import { UserResponse, UserRole } from '../../api/types';
import { api } from '../../api/client';
import { Users, UserPlus, Shield, UserCheck, UserX } from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Badge } from '../../design-system/Badge';
import { Modal } from '../../design-system/Modal';
import { Input } from '../../design-system/Input';
import { Select } from '../../design-system/Select';
import { Alert } from '../../design-system/Alert';
import { formatDateTime } from '../../utils/formatters';
import { useWorkspace } from '../../context/WorkspaceContext';

export const UserManagement: React.FC = () => {
  const { notify } = useWorkspace();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [role, setRole] = useState<UserRole>('member');
  const [createLoading, setCreateLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await api.listUsers();
      setUsers(data);
    } catch (err: any) {
      notify('error', err.message || 'Failed to list users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setCreateLoading(true);
    setError(null);
    try {
      await api.createUser({ email, password: password || undefined, role });
      notify('success', `User ${email} created successfully.`);
      setIsCreateOpen(false);
      setEmail('');
      setPassword('');
      fetchUsers();
    } catch (err: any) {
      setError(err.message || 'Failed to create user.');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleToggleStatus = async (userId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'active' ? 'suspended' : 'active';
    try {
      await api.updateUserStatus(userId, newStatus);
      notify('success', `User status updated to ${newStatus}.`);
      fetchUsers();
    } catch (err: any) {
      notify('error', err.message || 'Failed to update user status.');
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Tenant User Directory ({users.length})
          </h3>
          <p className="text-xs text-slate-500">Manage role-based permissions and access policies.</p>
        </div>
        <Button variant="primary" size="sm" onClick={() => setIsCreateOpen(true)} icon={<UserPlus className="w-3.5 h-3.5" />}>
          Invite New User
        </Button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4">User Email</th>
              <th className="py-3 px-4">Role</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Created Date</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-850/40">
                <td className="py-3 px-4 font-medium text-slate-200">{u.email}</td>
                <td className="py-3 px-4">
                  <Badge
                    variant={u.role === 'owner' ? 'emerald' : u.role === 'admin' ? 'cyan' : u.role === 'member' ? 'amber' : 'slate'}
                    size="xs"
                  >
                    {u.role}
                  </Badge>
                </td>
                <td className="py-3 px-4">
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      u.status === 'active'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-950 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {u.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-400 font-mono">{formatDateTime(u.created_at)}</td>
                <td className="py-3 px-4 text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleStatus(u.id, u.status)}
                  >
                    {u.status === 'active' ? 'Suspend' : 'Activate'}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Invite User to Tenant Workspace"
        subtitle="Provision role-based access for an analyst or administrator."
        footer={
          <div className="flex items-center justify-end gap-3">
            <Button variant="ghost" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreateUser} loading={createLoading}>
              Create User
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreateUser} className="flex flex-col gap-4">
          {error && <Alert variant="error">{error}</Alert>}
          <Input
            label="Corporate Email"
            type="email"
            placeholder="colleague@financial.org"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Temporary Password"
            type="password"
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            helperText="Minimum 8 characters (backend security requirement)"
          />
          <Select
            label="Role & Permissions"
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            options={[
              { value: 'viewer', label: 'Viewer (Read-only search & questions)' },
              { value: 'member', label: 'Member (Upload documents, run analyses)' },
              { value: 'admin', label: 'Admin (Manage users, retry pipelines)' },
              { value: 'owner', label: 'Owner (Full cryptographic tenant control)' },
            ]}
          />
        </form>
      </Modal>
    </div>
  );
};

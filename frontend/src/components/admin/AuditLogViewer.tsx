import React, { useState, useEffect } from 'react';
import { AuditEventResponse } from '../../api/types';
import { api } from '../../api/client';
import { Shield, RefreshCw, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Badge } from '../../design-system/Badge';
import { formatDateTime } from '../../utils/formatters';

export const AuditLogViewer: React.FC = () => {
  const [events, setEvents] = useState<AuditEventResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.listAuditEvents(50, 0);
      setEvents(data);
    } catch (err) {
      console.warn('Audit logs fetch failed', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Immutable Audit Trail ({events.length} Events)
          </h3>
          <p className="text-xs text-slate-500">Cryptographically correlated access and pipeline activity logs.</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchLogs} loading={loading} icon={<RefreshCw className="w-3.5 h-3.5" />}>
          Refresh Trail
        </Button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4 font-sans">Timestamp</th>
              <th className="py-3 px-4 font-sans">Action / Event</th>
              <th className="py-3 px-4 font-sans">Resource</th>
              <th className="py-3 px-4 font-sans">Outcome</th>
              <th className="py-3 px-4 font-sans">Request ID</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {events.map((ev) => (
              <tr key={ev.event_id} className="hover:bg-slate-850/40">
                <td className="py-3 px-4 text-slate-400">{formatDateTime(ev.timestamp)}</td>
                <td className="py-3 px-4 font-bold text-slate-200">{ev.event_type}</td>
                <td className="py-3 px-4 text-slate-300">{ev.resource_type} {ev.resource_id ? `(${ev.resource_id.substring(0, 8)})` : ''}</td>
                <td className="py-3 px-4">
                  <Badge variant={ev.outcome?.toLowerCase() === 'success' ? 'emerald' : 'rose'} size="xs">
                    {ev.outcome}
                  </Badge>
                </td>
                <td className="py-3 px-4 text-slate-500">{ev.request_id || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

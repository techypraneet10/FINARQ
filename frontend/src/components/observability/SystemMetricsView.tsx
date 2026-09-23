import React, { useState, useEffect } from 'react';
import { MetricsResponse, ReadyResponse, HealthResponse } from '../../api/types';
import { api } from '../../api/client';
import { Activity, Server, Cpu, Database, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '../../design-system/Button';
import { Badge } from '../../design-system/Badge';
import { Card } from '../../design-system/Card';
import { formatDateTime } from '../../utils/formatters';

export const SystemMetricsView: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadyResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealthAndMetrics = async () => {
    setLoading(true);
    try {
      const [hData, rData, mData] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getReadiness().catch(() => null),
        api.getMetrics().catch(() => null),
      ]);
      setHealth(hData);
      setReadiness(rData);
      setMetrics(mData);
    } catch (err) {
      console.warn('Metrics fetch error', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthAndMetrics();
    const interval = setInterval(fetchHealthAndMetrics, 20000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100">System Observability & Health</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time pipeline diagnostics, latency histograms, and downstream dependency health.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchHealthAndMetrics}
          loading={loading}
          icon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh Probes
        </Button>
      </div>

      {/* Downstream Dependency Readiness Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {readiness?.checks ? (
          Object.entries(readiness.checks).map(([service, statusObj]) => {
            const isOk = statusObj.status === 'ready' || statusObj.status === 'healthy';
            return (
              <div
                key={service}
                className={`p-4 rounded-2xl border flex items-center justify-between ${
                  isOk ? 'bg-emerald-950/20 border-emerald-500/30' : 'bg-rose-950/20 border-rose-500/30'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl ${isOk ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'}`}>
                    <Database className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">{service}</h4>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {statusObj.details || 'Operational'}
                    </span>
                  </div>
                </div>
                <Badge variant={isOk ? 'emerald' : 'rose'} size="xs">
                  {statusObj.status}
                </Badge>
              </div>
            );
          })
        ) : (
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-xs text-slate-400 col-span-3">
            Checking downstream service readiness probes...
          </div>
        )}
      </div>

      {/* Metrics & Counter Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Pipeline Telemetry Counters" subtitle="Lifetime event throughput">
          <div className="flex flex-col divide-y divide-slate-800 text-xs font-mono">
            {metrics?.counters && Object.keys(metrics.counters).length > 0 ? (
              Object.entries(metrics.counters).map(([key, val]) => (
                <div key={key} className="py-2.5 flex justify-between items-center">
                  <span className="text-slate-400">{key}</span>
                  <span className="font-bold text-emerald-400">{val}</span>
                </div>
              ))
            ) : (
              <div className="py-4 text-center text-slate-500">No telemetry counters recorded yet.</div>
            )}
          </div>
        </Card>

        <Card title="System Performance Gauges" subtitle="Active memory, queue, and thread usage">
          <div className="flex flex-col divide-y divide-slate-800 text-xs font-mono">
            {metrics?.gauges && Object.keys(metrics.gauges).length > 0 ? (
              Object.entries(metrics.gauges).map(([key, val]) => (
                <div key={key} className="py-2.5 flex justify-between items-center">
                  <span className="text-slate-400">{key}</span>
                  <span className="font-bold text-cyan-400">{val}</span>
                </div>
              ))
            ) : (
              <div className="py-4 text-center text-slate-500">Gauges telemetry initialized.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

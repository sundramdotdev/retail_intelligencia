'use client';

import React from 'react';
import { MetricCard } from '@/components/dashboard/metric-card';
import { EventFeed } from '@/components/dashboard/event-feed';
import { ConnectionStatus } from '@/components/dashboard/connection-status';
import { useAnalyticsOverview } from '@/hooks/use-analytics';
import { useAlerts } from '@/hooks/use-alerts';
import { useEvents } from '@/hooks/use-events';
import { useTasks } from '@/hooks/use-tasks';
import { useRealtime } from '@/providers/realtime-provider';

export default function OverviewPage() {
  const { data: overview, isLoading: loadingOverview } = useAnalyticsOverview();
  const { data: alerts, isLoading: loadingAlerts } = useAlerts(undefined, 'ACTIVE');
  const { data: events, isLoading: loadingEvents } = useEvents(undefined, 20);
  const { data: tasks, isLoading: loadingTasks } = useTasks();
  const { eventCount } = useRealtime();

  const criticalAlerts = alerts?.filter((a) => a.severity === 'CRITICAL' || a.severity === 'HIGH').length || 0;
  const activeTasks = tasks?.filter((t) => t.status !== 'COMPLETED' && t.status !== 'CANCELLED').length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            Store Overview
          </h1>
          <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
            Operational pulse · Real-time intelligence
          </p>
        </div>
        <ConnectionStatus />
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <MetricCard
          label="Foot Traffic"
          value={overview?.footTrafficCurrentHour ?? '—'}
          loading={loadingOverview}
        />
        <MetricCard
          label="Active Queues"
          value={overview?.activeQueues ?? '—'}
          loading={loadingOverview}
        />
        <MetricCard
          label="Open Alerts"
          value={criticalAlerts}
          accentColor={criticalAlerts > 0 ? 'var(--severity-high)' : undefined}
          loading={loadingAlerts}
        />
        <MetricCard
          label="Low Stock"
          value={overview?.lowStockIncidentsToday ?? '—'}
          loading={loadingOverview}
        />
        <MetricCard
          label="Active Tasks"
          value={activeTasks}
          loading={loadingTasks}
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* System Status */}
        <div className="surface p-4 space-y-3">
          <h3 className="text-xs font-mono uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
            System Status
          </h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Store Status</span>
              <div className="flex items-center gap-2">
                <span className="status-dot status-dot-online" />
                <span className="text-xs font-mono" style={{ color: 'var(--status-online)' }}>Operational</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Device Fleet</span>
              <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
                {overview?.deviceHealthStatus || '—'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Events Today</span>
              <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
                {eventCount || events?.length || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Recent Events */}
        <div className="surface p-4 lg:col-span-2">
          <h3 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
            Recent Events
          </h3>
          <EventFeed events={events || []} maxItems={8} loading={loadingEvents} />
        </div>
      </div>
    </div>
  );
}

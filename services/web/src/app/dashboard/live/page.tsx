'use client';

import React from 'react';
import { MetricCard } from '@/components/dashboard/metric-card';
import { EventFeed } from '@/components/dashboard/event-feed';
import { StoreMap } from '@/components/dashboard/store-map';
import { ConnectionStatus } from '@/components/dashboard/connection-status';
import { useAlerts } from '@/hooks/use-alerts';
import { useEvents } from '@/hooks/use-events';
import { useZones } from '@/hooks/use-zones';
import { useAnalyticsOverview } from '@/hooks/use-analytics';

export default function LiveStorePage() {
  const { data: zones, isLoading: loadingZones } = useZones();
  const { data: events, isLoading: loadingEvents } = useEvents(undefined, 30);
  const { data: alerts } = useAlerts(undefined, 'ACTIVE');
  const { data: overview } = useAnalyticsOverview();

  const activeAlerts = alerts?.filter((a) => a.status === 'ACTIVE').length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="font-display text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            Store Live
          </h1>
          <ConnectionStatus />
        </div>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-3 gap-3">
        <MetricCard label="Foot Traffic" value={overview?.footTrafficCurrentHour ?? '—'} />
        <MetricCard label="Active Queues" value={overview?.activeQueues ?? '—'} />
        <MetricCard label="Open Alerts" value={activeAlerts} accentColor={activeAlerts > 0 ? 'var(--severity-high)' : undefined} />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Store Map */}
        <div className="lg:col-span-3">
          <StoreMap zones={zones || []} loading={loadingZones} />

          {/* Zone List */}
          <div className="surface p-4 mt-4">
            <h3 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
              Zone Status
            </h3>
            <div className="space-y-2">
              {loadingZones ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-center justify-between py-2">
                    <div className="skeleton h-3 w-32" />
                    <div className="skeleton h-3 w-16" />
                  </div>
                ))
              ) : zones?.length ? (
                zones.map((zone) => (
                  <div
                    key={zone.zoneCode || zone.zoneId}
                    className="flex items-center justify-between py-2 border-b border-[var(--border-subtle)] last:border-0"
                  >
                    <div>
                      <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                        {zone.name}
                      </span>
                      <span className="text-xs font-mono ml-2" style={{ color: 'var(--text-tertiary)' }}>
                        {zone.zoneType}
                      </span>
                    </div>
                    <span className="text-xs font-mono" style={{ color: zone.isActive !== false ? 'var(--status-online)' : 'var(--text-tertiary)' }}>
                      {zone.isActive !== false ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>
                ))
              ) : (
                <div className="empty-state py-6">
                  <h3>No zones configured</h3>
                  <p>Zones will appear when spatial regions are defined.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Live Events */}
        <div className="lg:col-span-2 surface p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
            Live Events
          </h3>
          <EventFeed events={events || []} maxItems={20} loading={loadingEvents} />
        </div>
      </div>
    </div>
  );
}

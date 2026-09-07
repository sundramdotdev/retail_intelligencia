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
import { CameraView } from '@/components/dashboard/camera-view';
import { LiveAnalyticsGrid } from '@/components/dashboard/live-analytics-grid';
import { LiveZoneOccupancy } from '@/components/dashboard/live-zone-occupancy';
import { LiveObjectAnalytics } from '@/components/dashboard/live-object-analytics';

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
        {/* Store Map & Live Stream */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          <CameraView deviceId="edge-dev-001" />
          <LiveAnalyticsGrid deviceId="edge-dev-001" />
          <StoreMap zones={zones || []} loading={loadingZones} />

          {/* Live Zone Status */}
          <LiveZoneOccupancy deviceId="edge-dev-001" zones={zones || []} />
          <LiveObjectAnalytics deviceId="edge-dev-001" />
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

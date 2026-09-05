'use client';

import React from 'react';
import { useTraffic, useQueues, useDwell, useShelves } from '@/hooks/use-analytics';
import { MetricCard } from '@/components/dashboard/metric-card';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

export default function AnalyticsPage() {
  const { data: traffic, isLoading: loadingTraffic } = useTraffic();
  const { data: queues, isLoading: loadingQueues } = useQueues();
  const { data: dwell, isLoading: loadingDwell } = useDwell();
  const { data: shelves, isLoading: loadingShelves } = useShelves();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
          Analytics
        </h1>
        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
          Operational KPIs · Historical intelligence
        </p>
      </div>

      {/* Shelf Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="Shelf Zones" value={shelves?.totalShelfZones ?? '—'} loading={loadingShelves} />
        <MetricCard label="Low Stock" value={shelves?.lowStockZones ?? '—'} accentColor={shelves?.lowStockZones ? 'var(--severity-high)' : undefined} loading={loadingShelves} />
        <MetricCard label="Empty Shelves" value={shelves?.emptyZones ?? '—'} accentColor={shelves?.emptyZones ? 'var(--severity-critical)' : undefined} loading={loadingShelves} />
        <MetricCard label="Incidents Today" value={shelves?.incidentsToday ?? '—'} loading={loadingShelves} />
      </div>

      {/* Traffic Chart */}
      <div className="surface p-4">
        <h3 className="text-xs font-mono uppercase tracking-wider mb-4" style={{ color: 'var(--text-tertiary)' }}>
          Foot Traffic
        </h3>
        {loadingTraffic ? (
          <div className="skeleton w-full" style={{ height: 200 }} />
        ) : traffic?.series?.length ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={traffic.series}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-emphasis)',
                  borderRadius: 6,
                  fontSize: 12,
                  color: 'var(--text-primary)',
                }}
              />
              <Line type="monotone" dataKey="count" stroke="var(--accent-bronze)" strokeWidth={2} dot={{ fill: 'var(--accent-bronze)', r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state py-8">
            <p>No traffic data available.</p>
          </div>
        )}
      </div>

      {/* Queue & Dwell */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Queue Metrics */}
        <div className="surface p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
            Queue Performance
          </h3>
          {loadingQueues ? (
            <div className="skeleton w-full" style={{ height: 120 }} />
          ) : queues?.zones?.length ? (
            <div className="space-y-3">
              {queues.zones.map((zone) => (
                <div key={zone.zoneId} className="flex items-center justify-between py-2 border-b border-[var(--border-subtle)] last:border-0">
                  <div>
                    <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{zone.zoneId}</span>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{zone.status}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>{zone.currentQueueLength}</span>
                    <p className="text-xs font-mono" style={{ color: 'var(--text-tertiary)' }}>
                      ~{Math.round(zone.averageWaitSeconds / 60)}m wait
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state py-8">
              <p>No queue data available.</p>
            </div>
          )}
        </div>

        {/* Dwell Times */}
        <div className="surface p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
            Dwell Time
          </h3>
          {loadingDwell ? (
            <div className="skeleton w-full" style={{ height: 120 }} />
          ) : dwell?.zones?.length ? (
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={dwell.zones}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'var(--text-tertiary)' }} />
                <YAxis tick={{ fontSize: 10, fill: 'var(--text-tertiary)' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-emphasis)',
                    borderRadius: 6,
                    fontSize: 12,
                    color: 'var(--text-primary)',
                  }}
                />
                <Bar dataKey="averageDwellSeconds" fill="var(--accent-bronze-muted)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state py-8">
              <p>No dwell data available.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

'use client';

import React from 'react';
import { useZones } from '@/hooks/use-zones';

export default function ZonesPage() {
  const { data: zones, isLoading, isError } = useZones();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
          Zones
        </h1>
        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
          Spatial intelligence · Configured detection regions
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="surface p-4">
              <div className="skeleton h-4 w-40 mb-2" />
              <div className="skeleton h-3 w-24" />
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="surface p-6 text-center">
          <p className="text-sm" style={{ color: 'var(--error)' }}>Unable to load zones</p>
        </div>
      ) : zones?.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {zones.map((zone) => {
            const id = zone.zoneCode || zone.zoneId || '';
            return (
              <div key={id} className="surface p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                    {zone.name}
                  </h3>
                  <span
                    className="text-xs font-mono px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: zone.isActive !== false ? 'rgba(34,197,94,0.1)' : 'rgba(107,114,128,0.1)',
                      color: zone.isActive !== false ? 'var(--status-online)' : 'var(--text-tertiary)',
                    }}
                  >
                    {zone.isActive !== false ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Type</span>
                    <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{zone.zoneType}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Zone ID</span>
                    <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{id}</span>
                  </div>
                  {zone.thresholds && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Thresholds</span>
                      <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>
                        {Object.entries(zone.thresholds as Record<string, number>).map(([k, v]) => `${k}=${v}`).join(', ')}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-state py-12">
          <h3>No zones configured</h3>
          <p>Spatial detection zones are configured per-store and linked to camera views.</p>
        </div>
      )}
    </div>
  );
}

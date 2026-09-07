'use client';

import React from 'react';
import { useLiveMetricsQuery } from '@/hooks/use-live-metrics';
import { useLiveMetrics } from '@/providers/realtime-provider';

interface LiveZoneOccupancyProps {
  deviceId: string;
  zones: { zoneCode?: string; zoneId?: string; name: string; zoneType?: string; isActive?: boolean }[];
}

export function LiveZoneOccupancy({ deviceId, zones }: LiveZoneOccupancyProps) {
  useLiveMetricsQuery(deviceId);
  
  const metricsMap = useLiveMetrics();
  const liveData = metricsMap[deviceId];

  if (!liveData) return null;

  return (
    <div className="surface p-4 mt-4">
      <h3 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
        Live Zone Occupancy & Dwell
      </h3>
      <div className="space-y-3">
        {zones.map((zone) => {
          const zid = zone.zoneCode || zone.zoneId || '';
          if (!zid) return null;
          
          const occupancy = liveData.zoneOccupancy?.[zid] || 0;
          const dwell = liveData.dwellByZone?.[zid];
          
          return (
            <div key={zid} className="flex flex-col py-2 border-b border-[var(--border-subtle)] last:border-0">
              <div className="flex items-center justify-between mb-1">
                <div>
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                    {zone.name}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-[10px] font-mono text-[var(--text-tertiary)] uppercase block">People</span>
                    <span className="text-sm font-display font-semibold" style={{ color: occupancy > 0 ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>
                      {occupancy}
                    </span>
                  </div>
                  <div className="text-right w-16">
                    <span className="text-[10px] font-mono text-[var(--text-tertiary)] uppercase block">Avg Dwell</span>
                    <span className="text-sm font-mono" style={{ color: dwell?.averageDwellSeconds ? 'var(--text-secondary)' : 'var(--text-tertiary)' }}>
                      {dwell?.averageDwellSeconds ? `${dwell.averageDwellSeconds}s` : '—'}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Visual Occupancy Bar */}
              <div className="w-full bg-[var(--surface-sunken)] h-1.5 rounded-full overflow-hidden mt-1">
                <div 
                  className="h-full bg-[var(--status-online)] transition-all duration-500 ease-in-out" 
                  style={{ width: `${Math.min((occupancy / 5) * 100, 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

'use client';

import React from 'react';
import { useLiveMetricsQuery } from '@/hooks/use-live-metrics';
import { useLiveMetrics } from '@/providers/realtime-provider';

interface LiveObjectAnalyticsProps {
  deviceId: string;
}

export function LiveObjectAnalytics({ deviceId }: LiveObjectAnalyticsProps) {
  useLiveMetricsQuery(deviceId);
  
  const metricsMap = useLiveMetrics();
  const liveData = metricsMap[deviceId];

  if (!liveData?.objectsByClass || Object.keys(liveData.objectsByClass).length === 0) {
    return null;
  }

  const sortedObjects = Object.entries(liveData.objectsByClass).sort((a, b) => b[1] - a[1]);

  return (
    <div className="surface p-4 mt-4">
      <h3 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
        Detected Objects
      </h3>
      <div className="flex flex-wrap gap-2">
        {sortedObjects.map(([className, count]) => (
          <div 
            key={className} 
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--surface-sunken)] border border-[var(--border-subtle)]"
          >
            <span className="text-xs font-medium text-[var(--text-primary)] capitalize">
              {className}
            </span>
            <span className="text-xs font-mono font-semibold text-[var(--text-secondary)] bg-[var(--surface-base)] px-1.5 py-0.5 rounded-md">
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

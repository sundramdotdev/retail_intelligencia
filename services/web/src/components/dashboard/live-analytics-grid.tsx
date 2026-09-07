'use client';

import React from 'react';
import { useLiveMetricsQuery } from '@/hooks/use-live-metrics';
import { useLiveMetrics } from '@/providers/realtime-provider';

interface LiveAnalyticsGridProps {
  deviceId: string;
}

export function LiveAnalyticsGrid({ deviceId }: LiveAnalyticsGridProps) {
  useLiveMetricsQuery(deviceId);
  
  const metricsMap = useLiveMetrics();
  const liveData = metricsMap[deviceId];

  if (!liveData) {
    return (
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-4 gap-4 opacity-50">
        <div className="skeleton h-16" />
        <div className="skeleton h-16" />
        <div className="skeleton h-16" />
        <div className="skeleton h-16" />
      </div>
    );
  }

  return (
    <div className="surface p-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="flex flex-col">
        <span className="text-[10px] font-mono text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
          Active Persons
        </span>
        <span className="text-2xl font-display font-semibold" style={{ color: 'var(--text-primary)' }}>
          {liveData.peopleNow}
        </span>
      </div>
      
      <div className="flex flex-col">
        <span className="text-[10px] font-mono text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
          Active Objects
        </span>
        <span className="text-2xl font-display font-semibold" style={{ color: 'var(--text-primary)' }}>
          {liveData.activeObjects}
        </span>
      </div>

      <div className="flex flex-col">
        <span className="text-[10px] font-mono text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
          Footfall (Today)
        </span>
        <span className="text-2xl font-display font-semibold" style={{ color: 'var(--text-primary)' }}>
          {liveData.footfallToday}
        </span>
      </div>

      <div className="flex flex-col">
        <span className="text-[10px] font-mono text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
          Footfall (Last Hr)
        </span>
        <span className="text-2xl font-display font-semibold" style={{ color: 'var(--text-primary)' }}>
          {liveData.footfallLastHour}
        </span>
      </div>
    </div>
  );
}

'use client';

import React from 'react';
import type { Zone } from '@/lib/types';

interface StoreMapProps {
  zones: Zone[];
  loading?: boolean;
}

const ZONE_TYPE_COLORS: Record<string, { normal: string; alert: string }> = {
  QUEUE: { normal: '#3B82F633', alert: '#DC262644' },
  SHELF: { normal: '#22C55E22', alert: '#F59E0B44' },
  TRAFFIC_AISLE: { normal: '#8B8B8B22', alert: '#F59E0B44' },
  DWELL_AREA: { normal: '#C18A4222', alert: '#DC262644' },
};

const ZONE_LAYOUT: Record<string, { x: number; y: number; w: number; h: number }> = {
  'zone-checkout': { x: 400, y: 20, w: 170, h: 160 },
  'zone-aisle-01': { x: 20, y: 20, w: 170, h: 160 },
  'zone-aisle-02': { x: 210, y: 20, w: 170, h: 160 },
};

export function StoreMap({ zones, loading }: StoreMapProps) {
  if (loading) {
    return (
      <div className="skeleton w-full" style={{ height: 200, borderRadius: 'var(--radius-lg)' }} />
    );
  }

  return (
    <div className="surface p-4">
      <h3 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
        Store Layout
      </h3>
      <svg
        viewBox="0 0 600 200"
        className="w-full"
        style={{ maxHeight: 220 }}
        role="img"
        aria-label="Store zone map showing current occupancy"
      >
        {/* Background */}
        <rect x="0" y="0" width="600" height="200" rx="6" fill="var(--bg-elevated)" stroke="var(--border-subtle)" strokeWidth="1" />

        {zones.map((zone) => {
          const id = zone.zoneCode || zone.zoneId || '';
          const layout = ZONE_LAYOUT[id] || { x: 20, y: 20, w: 100, h: 80 };
          const typeColors = ZONE_TYPE_COLORS[zone.zoneType] || ZONE_TYPE_COLORS.TRAFFIC_AISLE;
          const fill = typeColors.normal;

          return (
            <g key={id}>
              <rect
                x={layout.x}
                y={layout.y}
                width={layout.w}
                height={layout.h}
                rx="4"
                fill={fill}
                stroke="var(--border-emphasis)"
                strokeWidth="1"
              />
              <text
                x={layout.x + layout.w / 2}
                y={layout.y + layout.h / 2 - 8}
                textAnchor="middle"
                fill="var(--text-secondary)"
                fontSize="11"
                fontFamily="Inter, sans-serif"
              >
                {zone.name?.split(' ').slice(0, 2).join(' ') || id}
              </text>
              <text
                x={layout.x + layout.w / 2}
                y={layout.y + layout.h / 2 + 10}
                textAnchor="middle"
                fill="var(--text-tertiary)"
                fontSize="10"
                fontFamily="JetBrains Mono, monospace"
              >
                {zone.zoneType}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

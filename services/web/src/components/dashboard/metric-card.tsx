'use client';

import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  suffix?: string;
  accentColor?: string;
  loading?: boolean;
}

export function MetricCard({ label, value, suffix, accentColor, loading }: MetricCardProps) {
  if (loading) {
    return (
      <div className="metric-card">
        <div className="skeleton h-3 w-20 mb-2" />
        <div className="skeleton h-7 w-16" />
      </div>
    );
  }

  return (
    <div className="metric-card">
      <span className="metric-label">{label}</span>
      <div className="flex items-baseline gap-1">
        <span className="metric-value" style={accentColor ? { color: accentColor } : undefined}>
          {value}
        </span>
        {suffix && (
          <span className="text-xs font-mono" style={{ color: 'var(--text-tertiary)' }}>
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}

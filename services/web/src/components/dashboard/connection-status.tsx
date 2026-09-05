'use client';

import React from 'react';
import type { ConnectionState } from '@/lib/types';
import { useRealtime } from '@/providers/realtime-provider';

const stateConfig: Record<ConnectionState, { label: string; dotClass: string; color: string }> = {
  LIVE: { label: 'Live', dotClass: 'status-dot-online', color: 'var(--status-online)' },
  CONNECTING: { label: 'Connecting…', dotClass: 'status-dot-warning', color: 'var(--status-warning)' },
  RECONNECTING: { label: 'Reconnecting…', dotClass: 'status-dot-reconnecting', color: 'var(--status-reconnecting)' },
  OFFLINE: { label: 'Offline', dotClass: 'status-dot-offline', color: 'var(--status-offline)' },
};

export function ConnectionStatus() {
  const { connectionState } = useRealtime();
  const config = stateConfig[connectionState];

  return (
    <div className="flex items-center gap-2">
      <span className={`status-dot ${config.dotClass}`} aria-label={`Connection status: ${config.label}`} role="status" />
      <span className="text-xs font-mono uppercase tracking-wider" style={{ color: config.color }}>
        {config.label}
      </span>
    </div>
  );
}

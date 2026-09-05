'use client';

import React from 'react';
import { useRealtime } from '@/providers/realtime-provider';
import { useAuth } from '@/lib/auth';
import type { ConnectionState } from '@/lib/types';

const stateConfig: Record<ConnectionState, { label: string; dotClass: string }> = {
  LIVE: { label: 'Live', dotClass: 'status-dot-online' },
  CONNECTING: { label: 'Connecting', dotClass: 'status-dot-warning' },
  RECONNECTING: { label: 'Reconnecting', dotClass: 'status-dot-reconnecting' },
  OFFLINE: { label: 'Offline', dotClass: 'status-dot-offline' },
};

export function Header() {
  const { connectionState } = useRealtime();
  const { session } = useAuth();
  const config = stateConfig[connectionState];

  return (
    <header
      className="fixed top-0 right-0 flex items-center justify-between px-6 border-b border-[var(--border-subtle)] z-10"
      style={{
        left: 'var(--sidebar-width)',
        height: 'var(--header-height)',
        backgroundColor: 'var(--bg-secondary)',
      }}
    >
      {/* Store indicator */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-mono" style={{ color: 'var(--text-tertiary)' }}>
          {session?.storeId?.toUpperCase().replace('_', ' ') || 'NO STORE'}
        </span>
      </div>

      {/* Connection status */}
      <div className="flex items-center gap-2">
        <span className={`status-dot ${config.dotClass}`} />
        <span
          className="text-xs font-mono uppercase tracking-wider"
          style={{ color: connectionState === 'LIVE' ? 'var(--status-online)' : 'var(--text-secondary)' }}
        >
          {config.label}
        </span>
      </div>
    </header>
  );
}

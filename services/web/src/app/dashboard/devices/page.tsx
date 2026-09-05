'use client';

import React from 'react';
import Link from 'next/link';
import { useDevice } from '@/hooks/use-devices';
import { timeAgo } from '@/lib/utils';

// Known device IDs from seed data
const KNOWN_DEVICES = ['edge-dev-001'];

export default function DevicesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
          Edge Devices
        </h1>
        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
          Hardware fleet management · Physical edge AI appliances
        </p>
      </div>

      <div className="space-y-3">
        {KNOWN_DEVICES.map((deviceId) => (
          <DeviceRow key={deviceId} deviceId={deviceId} />
        ))}
      </div>
    </div>
  );
}

function DeviceRow({ deviceId }: { deviceId: string }) {
  const { data: device, isLoading } = useDevice(deviceId);

  if (isLoading) {
    return (
      <div className="surface p-4 flex items-center justify-between">
        <div className="skeleton h-4 w-32" />
        <div className="skeleton h-3 w-16" />
      </div>
    );
  }

  const isOnline = device?.status === 'ONLINE';

  return (
    <Link href={`/dashboard/devices/${deviceId}`} className="block">
      <div className="surface p-4 transition-all hover:border-[var(--border-emphasis)] cursor-pointer">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`status-dot ${isOnline ? 'status-dot-online' : 'status-dot-offline'}`} />
            <div>
              <h3 className="text-sm font-mono font-medium" style={{ color: 'var(--text-primary)' }}>
                {deviceId.toUpperCase()}
              </h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
                {device?.hardwareModel || 'Edge AI Node'}
              </p>
            </div>
          </div>

          <div className="text-right">
            <span
              className="text-xs font-mono"
              style={{ color: isOnline ? 'var(--status-online)' : 'var(--status-offline)' }}
            >
              {isOnline ? 'ONLINE' : 'OFFLINE'}
            </span>
            {device?.lastHeartbeatAt && (
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
                {timeAgo(device.lastHeartbeatAt)}
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t border-[var(--border-subtle)]">
          <div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Cameras</span>
            <p className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>
              {device?.connectedCamerasCount ?? '—'}
            </p>
          </div>
          <div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Zones</span>
            <p className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>
              {device?.activeZonesCount ?? '—'}
            </p>
          </div>
          <div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Store</span>
            <p className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>
              {device?.storeId || '—'}
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}

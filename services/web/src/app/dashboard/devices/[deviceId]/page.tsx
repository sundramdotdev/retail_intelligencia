'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { useDevice, useDeviceHealth } from '@/hooks/use-devices';
import { MetricCard } from '@/components/dashboard/metric-card';
import { timeAgo } from '@/lib/utils';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function DeviceDetailPage() {
  const params = useParams();
  const deviceId = params?.deviceId as string;
  const { data: device, isLoading: loadingDevice } = useDevice(deviceId);
  const { data: health, isLoading: loadingHealth } = useDeviceHealth(deviceId);

  const isOnline = device?.status === 'ONLINE';

  return (
    <div className="space-y-6">
      {/* Back */}
      <Link href="/dashboard/devices" className="inline-flex items-center gap-1 text-xs btn-ghost">
        <ArrowLeft size={14} />
        Back to Devices
      </Link>

      {/* Header */}
      <div className="flex items-center gap-4">
        <span className={`status-dot ${isOnline ? 'status-dot-online' : 'status-dot-offline'}`} style={{ width: 12, height: 12 }} />
        <div>
          <h1 className="font-display text-xl font-semibold font-mono" style={{ color: 'var(--text-primary)' }}>
            {deviceId?.toUpperCase() || 'DEVICE'}
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
            {device?.hardwareModel || '—'} · {device?.firmwareVersion ? `v${device.firmwareVersion}` : ''}
          </p>
        </div>
      </div>

      {/* Status Card */}
      <div className="surface p-4 space-y-3">
        <h3 className="text-xs font-mono uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
          Connection Status
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Status</span>
            <p className="text-sm font-mono font-medium" style={{ color: isOnline ? 'var(--status-online)' : 'var(--status-offline)' }}>
              {device?.status || '—'}
            </p>
          </div>
          <div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Last Heartbeat</span>
            <p className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>
              {device?.lastHeartbeatAt ? timeAgo(device.lastHeartbeatAt) : '—'}
            </p>
          </div>
          <div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Cameras</span>
            <p className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>
              {health?.connectedCamerasCount ?? device?.connectedCamerasCount ?? '—'}
            </p>
          </div>
          <div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Active Zones</span>
            <p className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>
              {health?.activeZonesCount ?? device?.activeZonesCount ?? '—'}
            </p>
          </div>
        </div>
      </div>

      {/* Hardware Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="CPU" value={health?.cpuUtilizationPercent != null ? `${Math.round(health.cpuUtilizationPercent)}` : '—'} suffix="%" loading={loadingHealth} />
        <MetricCard label="GPU" value={health?.gpuUtilizationPercent != null ? `${Math.round(health.gpuUtilizationPercent)}` : '—'} suffix="%" loading={loadingHealth} />
        <MetricCard label="RAM" value={health?.memoryUsedMb != null ? `${Math.round(health.memoryUsedMb)}` : '—'} suffix="MB" loading={loadingHealth} />
        <MetricCard label="GPU Temp" value={health?.gpuTemperatureCelsius != null ? `${Math.round(health.gpuTemperatureCelsius)}` : '—'} suffix="°C" loading={loadingHealth} />
      </div>

      {/* Device Info */}
      <div className="surface p-4 space-y-3">
        <h3 className="text-xs font-mono uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
          Device Information
        </h3>
        <div className="space-y-2">
          {[
            ['Device ID', device?.deviceId],
            ['Store', device?.storeId],
            ['Hardware', device?.hardwareModel],
            ['Firmware', device?.firmwareVersion],
            ['Runtime', device?.runtimeVersion],
            ['MAC Address', device?.macAddress],
          ].map(([label, value]) => (
            <div key={String(label)} className="flex items-center justify-between py-1 border-b border-[var(--border-subtle)] last:border-0">
              <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{label}</span>
              <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>{String(value || '—')}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

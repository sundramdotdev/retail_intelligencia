'use client';

import React, { useState } from 'react';
import { AlertCard } from '@/components/dashboard/alert-card';
import { useAlerts } from '@/hooks/use-alerts';
import { apiClient } from '@/lib/api-client';
import { useQueryClient } from '@tanstack/react-query';
import type { Alert } from '@/lib/types';

const statusFilters = ['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'] as const;

export default function AlertsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const queryClient = useQueryClient();

  const { data: alerts, isLoading, isError } = useAlerts(
    undefined,
    statusFilter === 'ALL' ? undefined : statusFilter,
  );

  const handleAcknowledge = async (alertId: string) => {
    try {
      await apiClient.acknowledgeAlert(alertId);
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleCreateTask = (alert: Alert) => {
    // Navigate or open modal for task creation
    const taskTitle = `${alert.alertType?.replace(/_/g, ' ')} — ${alert.zoneId || 'Unknown Zone'}`;
    apiClient.createTask({
      storeId: alert.storeId,
      zoneId: alert.zoneId || undefined,
      alertId: alert.id,
      type: alert.alertType,
      priority: alert.severity === 'CRITICAL' ? 'URGENT' : alert.severity === 'HIGH' ? 'HIGH' : 'MEDIUM',
      title: taskTitle,
      description: alert.message,
    }).then(() => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    }).catch(console.error);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
          Alerts
        </h1>
        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
          Operational triage · AI-detected events requiring attention
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        {statusFilters.map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={statusFilter === status ? 'btn-primary' : 'btn-ghost'}
            style={{ fontSize: '12px' }}
          >
            {status === 'ALL' ? 'All' : status.charAt(0) + status.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Alert List */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="surface p-4 space-y-3">
              <div className="skeleton h-4 w-48" />
              <div className="skeleton h-3 w-64" />
              <div className="skeleton h-3 w-32" />
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="surface p-6 text-center">
          <p className="text-sm" style={{ color: 'var(--error)' }}>Unable to load alerts</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>Check API connection and try again.</p>
        </div>
      ) : alerts?.length ? (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <AlertCard
              key={alert.id || alert.alertCode}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onCreateTask={handleCreateTask}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state py-12">
          <h3>No {statusFilter === 'ALL' ? '' : statusFilter.toLowerCase()} alerts</h3>
          <p>The store is currently operating without unresolved operational alerts.</p>
        </div>
      )}
    </div>
  );
}

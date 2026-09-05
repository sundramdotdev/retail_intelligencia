'use client';

import React from 'react';
import type { Alert } from '@/lib/types';
import { severityClass, eventTypeLabel, timeAgo } from '@/lib/utils';

interface AlertCardProps {
  alert: Alert;
  onAcknowledge?: (alertId: string) => void;
  onCreateTask?: (alert: Alert) => void;
}

export function AlertCard({ alert, onAcknowledge, onCreateTask }: AlertCardProps) {
  const alertId = alert.id || alert.alertCode || '';

  return (
    <div className="surface p-4 space-y-3" style={{ animation: 'fade-in 0.3s ease-out' }}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`severity-badge ${severityClass(alert.severity)}`}>
            {alert.severity}
          </span>
          <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
            {eventTypeLabel(alert.alertType)}
          </span>
        </div>
        <span className="text-xs font-mono flex-shrink-0" style={{ color: 'var(--text-tertiary)' }}>
          {timeAgo(alert.createdAt)}
        </span>
      </div>

      {alert.zoneId && (
        <p className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>
          {alert.zoneId}
        </p>
      )}

      <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
        {alert.message}
      </p>

      {alert.status === 'ACTIVE' && (
        <div className="flex items-center gap-2 pt-1">
          {onAcknowledge && (
            <button
              onClick={() => onAcknowledge(alertId)}
              className="btn-secondary text-xs"
            >
              Acknowledge
            </button>
          )}
          {onCreateTask && (
            <button
              onClick={() => onCreateTask(alert)}
              className="btn-ghost text-xs"
            >
              Create Task
            </button>
          )}
        </div>
      )}

      {alert.status === 'ACKNOWLEDGED' && (
        <p className="text-xs font-mono" style={{ color: 'var(--text-tertiary)' }}>
          Acknowledged {alert.acknowledgedAt ? timeAgo(alert.acknowledgedAt) : ''}
        </p>
      )}
    </div>
  );
}

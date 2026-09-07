'use client';

import React from 'react';
import { CanonicalRetailEvent } from '@/lib/types';
import { formatTime, severityClass, eventTypeLabel } from '@/lib/utils';

interface EventFeedProps {
  events: CanonicalRetailEvent[];
  maxItems?: number;
  loading?: boolean;
}

export function EventFeed({ events, maxItems = 20, loading }: EventFeedProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="event-feed-item">
            <div className="skeleton h-3 w-14" />
            <div className="flex-1 space-y-1">
              <div className="skeleton h-3 w-24" />
              <div className="skeleton h-3 w-32" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!events.length) {
    return (
      <div className="empty-state py-8">
        <h3>No events</h3>
        <p>Events will appear here as they arrive from edge devices.</p>
      </div>
    );
  }

  const displayed = events.slice(0, maxItems);

  return (
    <div className="space-y-0">
      {displayed.map((event) => (
        <div key={event.eventId} className="event-feed-item" style={{ animation: 'slide-in-right 0.3s ease-out' }}>
          <span className="event-time">{formatTime(event.timestamp)}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={`severity-badge ${severityClass(event.severity)}`} style={{ fontSize: '10px', padding: '1px 6px' }}>
                {eventTypeLabel(event.eventType)}
              </span>
            </div>
            {event.zoneId && (
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
                {event.zoneId}
              </p>
            )}
          </div>
          <span className="text-xs font-mono" style={{ color: 'var(--text-tertiary)' }}>
            {Math.round(event.confidence * 100)}%
          </span>
        </div>
      ))}
    </div>
  );
}

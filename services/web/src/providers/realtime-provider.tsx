'use client';

/**
 * SSE Realtime provider and hook.
 * Connects to the FastAPI SSE stream and broadcasts events to the React tree.
 * Invalidates TanStack Query caches when relevant events arrive.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { sseClient } from '@/lib/sse-client';
import { useAuth } from '@/lib/auth';
import type { ConnectionState, SSEEvent } from '@/lib/types';

interface RealtimeContextValue {
  connectionState: ConnectionState;
  lastEvent: SSEEvent | null;
  eventCount: number;
}

const RealtimeContext = createContext<RealtimeContextValue>({
  connectionState: 'OFFLINE',
  lastEvent: null,
  eventCount: 0,
});

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [connectionState, setConnectionState] = useState<ConnectionState>('OFFLINE');
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [eventCount, setEventCount] = useState(0);
  const eventCountRef = useRef(0);

  useEffect(() => {
    if (!session?.storeId) return;

    // Subscribe to connection state changes
    const unsubState = sseClient.onConnectionState(setConnectionState);

    // Subscribe to events and invalidate relevant queries
    const unsubEvent = sseClient.onEvent((event: SSEEvent) => {
      setLastEvent(event);
      eventCountRef.current += 1;
      setEventCount(eventCountRef.current);

      // Invalidate relevant TanStack Query caches
      switch (event.type) {
        case 'EVENT_RECEIVED':
          queryClient.invalidateQueries({ queryKey: ['events'] });
          queryClient.invalidateQueries({ queryKey: ['analytics'] });
          break;
        case 'ALERT_TRIGGERED':
          queryClient.invalidateQueries({ queryKey: ['alerts'] });
          break;
        case 'TASK_UPDATED':
          queryClient.invalidateQueries({ queryKey: ['tasks'] });
          break;
        case 'DEVICE_STATUS':
          queryClient.invalidateQueries({ queryKey: ['devices'] });
          break;
        case 'ZONE_TELEMETRY':
          queryClient.invalidateQueries({ queryKey: ['zones'] });
          break;
      }
    });

    // Connect
    sseClient.connect(session.storeId, session.token);

    return () => {
      unsubState();
      unsubEvent();
      sseClient.disconnect();
    };
  }, [session?.storeId, session?.token, queryClient]);

  return (
    <RealtimeContext.Provider value={{ connectionState, lastEvent, eventCount }}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  return useContext(RealtimeContext);
}

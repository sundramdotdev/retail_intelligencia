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
import type { ConnectionState, SSEEvent, CanonicalRetailEvent, Alert, Task, DeviceStatus, ZoneTelemetry, LiveMetrics } from '@/lib/types';

interface RealtimeState {
  events: CanonicalRetailEvent[];
  alerts: Alert[];
  tasks: Task[];
  deviceStatus: Record<string, DeviceStatus>;
  zoneTelemetry: Record<string, ZoneTelemetry>;
  liveMetrics: Record<string, LiveMetrics>;
  isConnected: boolean;
  error: string | null;
  lastEventTime: Date | null;
}

interface RealtimeContextValue {
  connectionState: ConnectionState;
  lastEvent: SSEEvent | null;
  eventCount: number;
  state: RealtimeState;
}

const RealtimeContext = createContext<RealtimeContextValue | undefined>(undefined);

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [connectionState, setConnectionState] = useState<ConnectionState>('OFFLINE');
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [eventCount, setEventCount] = useState(0);
  const eventCountRef = useRef(0);
  const [state, setState] = useState<RealtimeState>({
    events: [],
    alerts: [],
    tasks: [],
    deviceStatus: {},
    zoneTelemetry: {},
    liveMetrics: {},
    isConnected: false,
    error: null,
    lastEventTime: null,
  });

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
        case 'DEVICE_STATUS': {
          const payload = (event.data || event) as any;
          const deviceId = payload.deviceId || event.deviceId || 'edge-dev-001';
          setState(prev => ({
            ...prev,
            deviceStatus: { ...prev.deviceStatus, [deviceId]: payload as DeviceStatus }
          }));
          queryClient.invalidateQueries({ queryKey: ['devices'] });
          break;
        }
        case 'ZONE_TELEMETRY': {
          const payload = (event.data || event) as any;
          const zoneId = payload.zoneId || event.zoneId || 'zone-checkout';
          setState(prev => ({
            ...prev,
            zoneTelemetry: { ...prev.zoneTelemetry, [zoneId]: payload as ZoneTelemetry }
          }));
          queryClient.invalidateQueries({ queryKey: ['zones'] });
          break;
        }
        case 'LIVE_METRICS': {
          const payload = (event.data || event) as any;
          const deviceId = payload.deviceId || event.deviceId || 'edge-dev-001';
          setState(prev => ({
            ...prev,
            liveMetrics: { ...prev.liveMetrics, [deviceId]: payload as LiveMetrics }
          }));
          break;
        }
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
    <RealtimeContext.Provider value={{ connectionState, lastEvent, eventCount, state }}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (context === undefined) throw new Error('Must be used within RealtimeProvider');
  return context;
}

export function useDeviceStatus() {
  const context = useContext(RealtimeContext);
  if (context === undefined) throw new Error('Must be used within RealtimeProvider');
  return context.state.deviceStatus;
}

export function useLiveMetrics() {
  const context = useContext(RealtimeContext);
  if (context === undefined) throw new Error('Must be used within RealtimeProvider');
  return context.state.liveMetrics;
}

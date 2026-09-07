'use client';

import React, { useState } from 'react';
import { useLiveMetricsQuery } from '@/hooks/use-live-metrics';
import { useLiveMetrics } from '@/providers/realtime-provider';

interface CameraViewProps {
  deviceId: string;
}

export function CameraView({ deviceId }: CameraViewProps) {
  const { data: queryData } = useLiveMetricsQuery(deviceId);
  const metricsMap = useLiveMetrics();
  const liveData = metricsMap[deviceId] || queryData;
  const [hasError, setHasError] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const primaryStreamUrl = `${apiBase}/devices/${deviceId}/stream`;

  const isCameraStreaming = liveData && !liveData.isStale && (liveData.camera?.status === 'STREAMING' || liveData.camera?.status === 'ONLINE');
  const isLive = Boolean(isCameraStreaming);

  const fpsValue = liveData?.vision?.inferenceFps ?? liveData?.camera?.fps;
  const latencyValue = liveData?.vision?.latencyMs;

  return (
    <div className="surface p-0 overflow-hidden relative group h-[400px]">
      <img
        src={hasError ? `http://localhost:8080/stream.mjpeg` : primaryStreamUrl}
        alt="Live Edge Camera Stream"
        className="w-full h-full object-cover"
        onError={(e) => {
          if (!hasError) {
            setHasError(true);
          } else {
            const target = e.target as HTMLImageElement;
            target.src = 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D"http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg" width%3D"640" height%3D"360" viewBox%3D"0 0 640 360"%3E%3Crect width%3D"640" height%3D"360" fill%3D"%231a1a1a"%2F%3E%3Ctext x%3D"320" y%3D"180" font-family%3D"monospace" font-size%3D"16" fill%3D"%23666" text-anchor%3D"middle"%3ECAMERA OFFLINE%3C%2Ftext%3E%3C%2Fsvg%3E';
          }
        }}
      />
      
      {/* Stream Overlay HUD */}
      <div className="absolute top-0 left-0 right-0 p-3 flex justify-between items-start bg-gradient-to-b from-black/60 to-transparent pointer-events-none">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="relative flex h-2.5 w-2.5">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isLive ? 'bg-[var(--status-online)]' : 'bg-red-500'}`}></span>
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isLive ? 'bg-[var(--status-online)]' : 'bg-red-500'}`}></span>
            </span>
            <span className="text-xs font-mono font-medium text-white shadow-sm">
              {isLive ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
          <div className="text-[10px] font-mono text-gray-300">
            {liveData?.camera?.id || 'camera-01'}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono text-white shadow-sm">
            {fpsValue !== undefined && fpsValue > 0 ? `${fpsValue.toFixed(1)} FPS` : '—'}
          </div>
          <div className="text-[10px] font-mono text-gray-300">
            {latencyValue !== undefined && latencyValue > 0 ? `Lat: ${latencyValue.toFixed(0)}ms` : 'Lat: —'}
          </div>
        </div>
      </div>

      {/* Diagnostic Source Label */}
      <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/60 backdrop-blur text-[9px] font-mono text-gray-300 pointer-events-none">
        Source: Edge Stream ({liveData?.camera?.id || 'camera-01'})
      </div>
    </div>
  );
}

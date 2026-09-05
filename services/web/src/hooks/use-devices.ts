'use client';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function useDevice(deviceId: string) {
  return useQuery({
    queryKey: ['devices', deviceId],
    queryFn: () => apiClient.getDevice(deviceId),
    enabled: !!deviceId,
  });
}

export function useDeviceHealth(deviceId: string) {
  return useQuery({
    queryKey: ['devices', deviceId, 'health'],
    queryFn: () => apiClient.getDeviceHealth(deviceId),
    enabled: !!deviceId,
  });
}

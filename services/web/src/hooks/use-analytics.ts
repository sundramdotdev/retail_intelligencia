'use client';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function useAnalyticsOverview(storeId?: string) {
  return useQuery({
    queryKey: ['analytics', 'overview', storeId],
    queryFn: () => apiClient.getAnalyticsOverview(storeId),
  });
}

export function useTraffic(storeId?: string) {
  return useQuery({
    queryKey: ['analytics', 'traffic', storeId],
    queryFn: () => apiClient.getTraffic(storeId),
  });
}

export function useQueues(storeId?: string) {
  return useQuery({
    queryKey: ['analytics', 'queues', storeId],
    queryFn: () => apiClient.getQueues(storeId),
  });
}

export function useDwell(storeId?: string) {
  return useQuery({
    queryKey: ['analytics', 'dwell', storeId],
    queryFn: () => apiClient.getDwell(storeId),
  });
}

export function useShelves(storeId?: string) {
  return useQuery({
    queryKey: ['analytics', 'shelves', storeId],
    queryFn: () => apiClient.getShelves(storeId),
  });
}

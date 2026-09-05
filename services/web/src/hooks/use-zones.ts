'use client';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function useZones(storeId?: string) {
  return useQuery({
    queryKey: ['zones', storeId],
    queryFn: () => apiClient.getStoreZones(storeId),
    select: (data) => data.zones,
  });
}

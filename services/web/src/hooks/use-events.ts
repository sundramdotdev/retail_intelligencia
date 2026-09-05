'use client';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function useEvents(storeId?: string, limit: number = 50) {
  return useQuery({
    queryKey: ['events', storeId, limit],
    queryFn: () => apiClient.getEvents({ storeId, limit }),
    select: (data) => data.items,
  });
}

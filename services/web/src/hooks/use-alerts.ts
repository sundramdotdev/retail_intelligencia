'use client';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function useAlerts(storeId?: string, status?: string) {
  return useQuery({
    queryKey: ['alerts', storeId, status],
    queryFn: () => apiClient.getAlerts({ storeId, status }),
    select: (data) => data.alerts,
  });
}

'use client';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function useTasks(storeId?: string, status?: string) {
  return useQuery({
    queryKey: ['tasks', storeId, status],
    queryFn: () => apiClient.getTasks({ storeId, status }),
    select: (data) => data.tasks,
  });
}

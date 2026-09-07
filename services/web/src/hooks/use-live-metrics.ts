import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth';
import { apiClient } from '@/lib/api-client';
import { LiveMetrics } from '@/lib/types';

export function useLiveMetricsQuery(deviceId?: string) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['metrics', 'live', deviceId],
    queryFn: async () => {
      const response = await apiClient.get<{
        storeId: string;
        deviceId?: string;
        [key: string]: any;
      }>(`/api/v1/metrics/live?storeId=${session?.storeId}`);
      
      // If a deviceId is specified and the returned metrics aren't for that device
      // (or are NO_DATA), return null.
      if (response.status === 'NO_DATA') {
         return null;
      }
      return response as unknown as LiveMetrics;
    },
    enabled: !!session?.storeId,
    refetchInterval: 5000, // Fallback polling if SSE drops
  });
}

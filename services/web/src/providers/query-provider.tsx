'use client';

/**
 * TanStack Query provider for server state management.
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,       // 30 seconds
      refetchInterval: 60_000, // Refetch every 60 seconds as baseline
      refetchOnWindowFocus: true,
      retry: 2,
    },
  },
});

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

export { queryClient };

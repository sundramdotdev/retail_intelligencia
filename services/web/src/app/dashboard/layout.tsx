'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AuthProvider, useAuth } from '@/lib/auth';
import { QueryProvider } from '@/providers/query-provider';
import { RealtimeProvider } from '@/providers/realtime-provider';
import { Sidebar } from '@/components/dashboard/sidebar';
import { Header } from '@/components/dashboard/header';

function DashboardShell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isInitializing } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isInitializing && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isInitializing, router]);

  if (isInitializing || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="skeleton w-6 h-6 rounded-full" />
      </div>
    );
  }

  return (
    <RealtimeProvider>
      <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <Sidebar />
        <Header />
        <main
          className="pt-14 px-6 py-6"
          style={{
            marginLeft: 'var(--sidebar-width)',
            paddingTop: 'calc(var(--header-height) + 24px)',
          }}
        >
          {children}
        </main>
      </div>
    </RealtimeProvider>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>;
}

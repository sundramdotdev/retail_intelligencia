'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { AuthProvider } from '@/lib/auth';

function HomeRedirect() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/dashboard');
    } else {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="skeleton w-6 h-6 rounded-full" />
    </div>
  );
}

export default function HomePage() {
  return (
    <AuthProvider>
      <HomeRedirect />
    </AuthProvider>
  );
}

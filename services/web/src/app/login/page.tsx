'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { AuthProvider, useAuth } from '@/lib/auth';
import type { UserRole } from '@/lib/types';

const roles: { role: UserRole; label: string; description: string }[] = [
  {
    role: 'STORE_MANAGER',
    label: 'Store Manager',
    description: 'Full store visibility, alert triage, task dispatch, analytics',
  },
  {
    role: 'STORE_STAFF',
    label: 'Floor Staff',
    description: 'View assigned tasks, acknowledge alerts, mark completion',
  },
  {
    role: 'PLATFORM_ADMIN',
    label: 'Platform Admin',
    description: 'Fleet-wide access, device provisioning, global configuration',
  },
];

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = (role: UserRole) => {
    login(role);
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="w-full max-w-md space-y-8">
        {/* Brand */}
        <div className="text-center">
          <h1 className="font-display text-2xl font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>
            Retail Intelligencia
          </h1>
          <p className="mt-2 text-sm" style={{ color: 'var(--text-tertiary)' }}>
            Operations Console
          </p>
        </div>

        {/* Role Selection */}
        <div className="space-y-3">
          <p className="text-xs font-mono uppercase tracking-wider text-center" style={{ color: 'var(--text-tertiary)' }}>
            Select Role
          </p>

          {roles.map(({ role, label, description }) => (
            <button
              key={role}
              onClick={() => handleLogin(role)}
              className="w-full surface p-4 text-left transition-all hover:border-[var(--border-emphasis)]"
              style={{ cursor: 'pointer' }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                    {label}
                  </h3>
                  <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
                    {description}
                  </p>
                </div>
                <span className="text-xs font-mono" style={{ color: 'var(--accent-bronze)' }}>→</span>
              </div>
            </button>
          ))}
        </div>

        <p className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
          Development mode · No credentials required
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <AuthProvider>
      <LoginForm />
    </AuthProvider>
  );
}

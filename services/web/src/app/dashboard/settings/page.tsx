'use client';

import React from 'react';
import { useAuth } from '@/lib/auth';

export default function SettingsPage() {
  const { session } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
          Settings
        </h1>
        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
          Store configuration · System preferences
        </p>
      </div>

      {/* Store Info */}
      <div className="surface p-4 space-y-3">
        <h3 className="text-xs font-mono uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
          Store Information
        </h3>
        <div className="space-y-2">
          {[
            ['Store ID', session?.storeId || 'store_001'],
            ['Name', 'Market Street Superstore'],
            ['Timezone', 'America/Los_Angeles'],
            ['City', 'San Francisco, CA'],
          ].map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{label}</span>
              <span className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* User Info */}
      <div className="surface p-4 space-y-3">
        <h3 className="text-xs font-mono uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
          Current User
        </h3>
        <div className="space-y-2">
          {[
            ['Name', session?.user.fullName],
            ['Email', session?.user.email],
            ['Role', session?.user.role?.replace('_', ' ')],
            ['User ID', session?.user.userId],
          ].map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{label}</span>
              <span className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>{String(value || '—')}</span>
            </div>
          ))}
        </div>
      </div>

      {/* System */}
      <div className="surface p-4 space-y-3">
        <h3 className="text-xs font-mono uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
          System
        </h3>
        <div className="space-y-2">
          {[
            ['API Endpoint', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'],
            ['Platform Version', '1.0.0'],
            ['Phase', '6 — Real-Time Dashboard'],
          ].map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{label}</span>
              <span className="text-xs font-mono" style={{ color: 'var(--text-tertiary)' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

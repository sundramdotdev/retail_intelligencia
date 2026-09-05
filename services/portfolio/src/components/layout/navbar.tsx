'use client';

import React from 'react';
import Link from 'next/link';
import { NAV_ITEMS } from '@/lib/constants';

export function Navbar() {
  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        backgroundColor: 'rgba(8, 8, 8, 0.85)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--color-border-subtle)',
      }}
    >
      <div className="section-container flex items-center justify-between h-14">
        <Link
          href="/"
          className="font-display text-sm font-semibold tracking-wide flex items-center gap-2"
          style={{ color: 'var(--color-text-primary)' }}
        >
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-accent)' }} />
          RETAIL INTELLIGENCIA
        </Link>

        <div className="hidden md:flex items-center gap-6">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-xs font-medium transition-colors hover:text-white"
              style={{
                color: 'var(--color-text-tertiary)',
              }}
            >
              {item.label}
            </Link>
          ))}
          <a
            href="http://localhost:3001" // Pointing to potential dashboard URL if running locally
            target="_blank"
            rel="noopener noreferrer"
            className="badge badge-accent hover:opacity-80 transition-opacity"
            style={{ fontSize: '11px', padding: '4px 10px', color: 'var(--color-text-primary)' }}
          >
            Operations Dashboard
          </a>
        </div>
      </div>
    </nav>
  );
}

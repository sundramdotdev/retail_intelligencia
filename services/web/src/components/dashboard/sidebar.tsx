'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Radio,
  AlertTriangle,
  ClipboardList,
  Cpu,
  MapPin,
  BarChart3,
  Settings,
  LogOut,
} from 'lucide-react';
import { useAuth } from '@/lib/auth';

const navItems = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/live', label: 'Live Store', icon: Radio },
  { href: '/dashboard/alerts', label: 'Alerts', icon: AlertTriangle },
  { href: '/dashboard/tasks', label: 'Tasks', icon: ClipboardList },
  { href: '/dashboard/devices', label: 'Devices', icon: Cpu },
  { href: '/dashboard/zones', label: 'Zones', icon: MapPin },
  { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { session, logout } = useAuth();

  return (
    <aside
      className="fixed left-0 top-0 bottom-0 flex flex-col border-r border-[var(--border-subtle)]"
      style={{
        width: 'var(--sidebar-width)',
        backgroundColor: 'var(--bg-secondary)',
      }}
    >
      {/* Brand */}
      <div className="px-4 h-14 flex items-center border-b border-[var(--border-subtle)]">
        <span className="font-display font-semibold text-sm tracking-wide" style={{ color: 'var(--text-primary)' }}>
          RETAIL
        </span>
        <span className="font-display font-light text-sm tracking-wide ml-1" style={{ color: 'var(--text-tertiary)' }}>
          INTELLIGENCIA
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive =
            item.href === '/dashboard'
              ? pathname === '/dashboard'
              : pathname?.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn('nav-item', isActive && 'active')}
            >
              <item.icon size={16} strokeWidth={1.5} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User info */}
      <div className="px-3 py-3 border-t border-[var(--border-subtle)]">
        <div className="px-3 py-2">
          <p className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
            {session?.user.fullName || 'Not signed in'}
          </p>
          <p className="text-xs font-mono mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
            {session?.user.role?.replace('_', ' ') || ''}
          </p>
        </div>
        <button
          onClick={logout}
          className="nav-item w-full mt-1"
          style={{ color: 'var(--text-tertiary)' }}
        >
          <LogOut size={14} strokeWidth={1.5} />
          <span className="text-xs">Sign out</span>
        </button>
      </div>
    </aside>
  );
}

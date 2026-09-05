import React from 'react';

export function Footer() {
  return (
    <footer
      className="py-12 mt-24"
      style={{ borderTop: '1px solid var(--color-border-subtle)' }}
    >
      <div className="section-container">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <p className="font-display text-sm font-semibold tracking-wide mb-1" style={{ color: 'var(--color-text-primary)' }}>
              RETAIL INTELLIGENCIA
            </p>
            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              Edge AI for smarter retail operations.
            </p>
          </div>
          <div className="text-left md:text-right">
             <p className="text-xs mb-1" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
               Computer Vision · Edge AI · Retail Intelligence
             </p>
             <p className="text-xs" style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-mono)' }}>
               SIH PS-179 / Problem Statement 26179
             </p>
          </div>
        </div>
      </div>
    </footer>
  );
}

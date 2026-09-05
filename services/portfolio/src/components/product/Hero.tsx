import React from 'react';

export function Hero() {
  return (
    <section className="section-container pt-24 md:pt-40 pb-16">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        <div className="animate-fade-up">
          <p className="font-mono text-xs mb-4 uppercase tracking-widest" style={{ color: 'var(--color-accent)' }}>
            Edge AI / Retail Computer Vision
          </p>
          <h1 className="section-title text-4xl md:text-6xl mb-6 leading-tight">
            Understand your store <br />
            <span style={{ color: 'var(--color-text-secondary)' }}>as it operates.</span>
          </h1>
          <p className="text-base md:text-lg mb-10" style={{ color: 'var(--color-text-tertiary)', maxWidth: '500px' }}>
            On-device computer vision that turns camera feeds into real-time retail intelligence, without sending raw video to the cloud.
          </p>
          <div className="flex items-center gap-6">
            <a
              href="#live-demo"
              className="badge badge-accent hover:opacity-80 transition-opacity"
              style={{ fontSize: '13px', padding: '8px 16px', color: 'var(--color-text-primary)' }}
            >
              Explore Live Demo
            </a>
            <a
              href="#how-it-works"
              className="text-sm font-medium link-underline"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              How it works
            </a>
          </div>
        </div>

        <div className="card p-6 md:p-8 animate-fade-up delay-200">
          <div className="flex items-center justify-between mb-6 pb-4" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
            <span className="font-mono text-xs" style={{ color: 'var(--color-text-secondary)' }}>EDGE-NODE-001</span>
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="font-mono text-xs" style={{ color: 'var(--color-text-primary)' }}>HEALTHY</span>
            </div>
          </div>
          
          <div className="space-y-4 font-mono text-sm">
            <div className="flex justify-between">
              <span style={{ color: 'var(--color-text-tertiary)' }}>CAMERA-01</span>
              <span style={{ color: 'var(--color-text-secondary)' }}>● STREAMING</span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: 'var(--color-text-tertiary)' }}>YOLO11n</span>
              <span style={{ color: 'var(--color-text-secondary)' }}>READY</span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: 'var(--color-text-tertiary)' }}>BYTETRACK</span>
              <span style={{ color: 'var(--color-accent)' }}>12 ACTIVE TRACKS</span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: 'var(--color-text-tertiary)' }}>ZONE ENGINE</span>
              <span style={{ color: 'var(--color-text-secondary)' }}>4 ACTIVE ZONES</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

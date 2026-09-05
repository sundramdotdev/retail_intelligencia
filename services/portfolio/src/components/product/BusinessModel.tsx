import React from 'react';

export function BusinessModel() {
  return (
    <section id="business" className="section-container py-16 md:py-24 border-t border-[#222]">
      <div className="text-center mb-16 max-w-2xl mx-auto">
        <h2 className="section-heading mb-4">Proposed Business Model</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
          Hardware + Software + SaaS for scalable retail intelligence.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6">
          <span className="font-mono text-[10px] text-[#666] block mb-4">01</span>
          <h3 className="text-sm font-semibold text-[#eee] mb-2">Edge Hardware</h3>
          <p className="text-xs text-[#aaa]">
            One-time hardware fee for the physical edge appliance deployed in-store.
          </p>
        </div>
        <div className="card p-6">
          <span className="font-mono text-[10px] text-[#666] block mb-4">02</span>
          <h3 className="text-sm font-semibold text-[#eee] mb-2">Installation</h3>
          <p className="text-xs text-[#aaa]">
            Camera configuration, physical deployment, and zone mapping setup.
          </p>
        </div>
        <div className="card p-6">
          <span className="font-mono text-[10px] text-[#666] block mb-4">03</span>
          <h3 className="text-sm font-semibold text-[#eee] mb-2">SaaS Subscription</h3>
          <p className="text-xs text-[#aaa]">
            Recurring subscription per active edge device for platform access and real-time alerts.
          </p>
        </div>
        <div className="card p-6">
          <span className="font-mono text-[10px] text-[#666] block mb-4">04</span>
          <h3 className="text-sm font-semibold text-[#eee] mb-2">Enterprise Analytics</h3>
          <p className="text-xs text-[#aaa]">
            Advanced cross-store reporting and historical trend analysis for regional managers.
          </p>
        </div>
      </div>
    </section>
  );
}

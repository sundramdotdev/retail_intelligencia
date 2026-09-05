import React from 'react';

export function RetailIntelligence() {
  return (
    <section id="intelligence" className="section-container py-16 md:py-24 border-t border-[#222]">
      <div className="text-center mb-16 max-w-2xl mx-auto">
        <h2 className="section-heading mb-4">Retail Intelligence</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
          Where computer vision becomes business intelligence. The edge system evaluates observations against deterministic rules to emit structured JSON events.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-8">
          <h3 className="font-mono text-xs mb-4 text-[#C18A42]">QUEUE CONGESTION</h3>
          <p className="text-sm text-[#eee] mb-2">People in checkout zone</p>
          <p className="font-mono text-[10px] text-[#666] mb-2">↓ Threshold exceeded</p>
          <p className="badge badge-accent inline-block">QUEUE_HIGH</p>
        </div>
        
        <div className="card p-8">
          <h3 className="font-mono text-xs mb-4 text-[#C18A42]">TRAFFIC INTENSITY</h3>
          <p className="text-sm text-[#eee] mb-2">Zone entries over time</p>
          <p className="font-mono text-[10px] text-[#666] mb-2">↓ Computed average</p>
          <p className="badge badge-accent inline-block">HIGH_TRAFFIC</p>
        </div>
        
        <div className="card p-8">
          <h3 className="font-mono text-xs mb-4 text-[#C18A42]">SHELF AVAILABILITY</h3>
          <p className="text-sm text-[#eee] mb-2">Shelf occupancy signal</p>
          <p className="font-mono text-[10px] text-[#666] mb-2">↓ Drops below 20%</p>
          <p className="badge badge-accent inline-block">LOW_STOCK</p>
        </div>
      </div>

      <div className="mt-12 card p-8 bg-[#080808]">
        <h3 className="font-mono text-xs mb-4 text-[#888]">STANDARDIZED EVENT CONTRACT</h3>
        <pre className="font-mono text-[11px] text-[#aaa] overflow-x-auto bg-[#111] p-4 rounded border border-[#222]">
{`{
  "eventType": "QUEUE_HIGH",
  "deviceId": "edge_001",
  "storeId": "store_001",
  "zoneId": "checkout_02",
  "confidence": 0.94,
  "severity": "HIGH",
  "schemaVersion": "1.0"
}`}
        </pre>
        <p className="text-xs text-[#666] mt-4">
          The edge system does not send raw video to communicate intelligence. It sends lightweight, structured events.
        </p>
      </div>
    </section>
  );
}

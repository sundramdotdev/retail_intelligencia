'use client';
import React, { useState } from 'react';
import { DEMO_METRICS } from '@/lib/constants';

export function LiveDemo() {
  const [events] = useState([
    { time: '10:31:02', type: 'PERSON_ENTERED', zone: 'AISLE_04' },
    { time: '10:31:07', type: 'ZONE_CHANGED', zone: 'AISLE_04 → CHECKOUT' },
    { time: '10:31:12', type: 'QUEUE_HIGH', zone: 'CHECKOUT_02' },
  ]);

  return (
    <section id="live-demo" className="section-container py-16 md:py-24">
      <div className="mb-12">
        <h2 className="section-heading mb-4">Live Edge AI Demonstration</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
          Real-time visualization of the on-device inference pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card overflow-hidden relative min-h-[300px] md:min-h-[400px]" style={{ backgroundColor: '#050505' }}>
          <div className="absolute top-4 left-4 z-10 flex flex-wrap gap-2">
            <span className="badge font-mono text-[10px]" style={{ backgroundColor: 'rgba(0,0,0,0.8)' }}>DEMO MODE</span>
            <span className="badge font-mono text-[10px]" style={{ backgroundColor: 'rgba(0,0,0,0.8)' }}>CAMERA-01</span>
          </div>
          
          {/* Simulated CV Canvas */}
          <div className="absolute inset-4 md:inset-8 flex flex-col items-center justify-center border border-dashed border-[#333] rounded">
            <p className="font-mono text-xs text-[#555] mb-8">CV FRAME SIMULATION</p>
            {/* Bounding box mock 1 */}
            <div className="absolute border border-[#C18A42] w-[20%] h-[40%] left-[30%] top-[40%] bg-[rgba(193,138,66,0.1)]">
              <span className="absolute -top-5 left-[-1px] bg-[#C18A42] text-black text-[9px] font-mono px-1 py-0.5 whitespace-nowrap">ID 04 0.94</span>
            </div>
            {/* Bounding box mock 2 */}
            <div className="absolute border border-[#C18A42] w-[18%] h-[35%] right-[25%] top-[50%] bg-[rgba(193,138,66,0.1)]">
              <span className="absolute -top-5 left-[-1px] bg-[#C18A42] text-black text-[9px] font-mono px-1 py-0.5 whitespace-nowrap">ID 08 0.88</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <div className="card p-6">
            <h3 className="font-mono text-xs mb-4 text-[#888]">METRICS</h3>
            <div className="grid grid-cols-2 gap-4">
               <div>
                 <p className="font-mono text-[10px] text-[#666]">MODEL</p>
                 <p className="font-mono text-sm text-[#eee]">YOLO11n</p>
               </div>
               <div>
                 <p className="font-mono text-[10px] text-[#666]">TRACKER</p>
                 <p className="font-mono text-sm text-[#eee]">ByteTrack</p>
               </div>
               <div>
                 <p className="font-mono text-[10px] text-[#666]">ACTIVE TRACKS</p>
                 <p className="font-mono text-sm text-[#C18A42]">{DEMO_METRICS.active_tracks}</p>
               </div>
               <div>
                 <p className="font-mono text-[10px] text-[#666]">INFERENCE</p>
                 <p className="font-mono text-sm text-[#eee]">{DEMO_METRICS.inference_fps} FPS</p>
               </div>
            </div>
          </div>
          
          <div className="card p-6 flex-1 flex flex-col">
            <h3 className="font-mono text-xs mb-4 text-[#888]">EVENT STREAM</h3>
            <div className="flex-1 overflow-y-auto space-y-3">
              {events.map((evt, i) => (
                <div key={i} className="font-mono text-[11px] flex flex-col sm:flex-row sm:gap-3">
                  <span className="text-[#555] sm:min-w-[60px]">{evt.time}</span>
                  <span className={evt.type === 'QUEUE_HIGH' ? 'text-red-400 font-medium' : 'text-[#C18A42] font-medium'}>{evt.type}</span>
                  <span className="text-[#aaa] truncate">{evt.zone}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

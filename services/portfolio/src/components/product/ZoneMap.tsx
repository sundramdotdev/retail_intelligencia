import React from 'react';

export function ZoneMap() {
  return (
    <section className="section-container py-16 md:py-24 border-t border-[#222]">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        <div>
          <h2 className="section-heading mb-4">Zone Engine & Heatmaps</h2>
          <p className="text-sm mb-6" style={{ color: 'var(--color-text-tertiary)' }}>
            Zones convert raw tracking coordinates into retail context. ByteTrack provides anonymous trajectories; the analytics layer converts those trajectories into spatial density and movement information.
          </p>
          <ul className="space-y-4 font-mono text-[11px]">
            <li className="flex items-center gap-3">
              <span className="text-[#C18A42] w-4 text-center">→</span>
              <span className="text-[#eee]">Person enters Checkout Zone</span>
              <span className="text-[#666]">Queue counter updated</span>
            </li>
            <li className="flex items-center gap-3">
              <span className="text-[#C18A42] w-4 text-center">→</span>
              <span className="text-[#eee]">Person enters Aisle 04</span>
              <span className="text-[#666]">Traffic metric updated</span>
            </li>
            <li className="flex items-center gap-3">
              <span className="text-[#C18A42] w-4 text-center">→</span>
              <span className="text-[#eee]">Person remains in Aisle 04</span>
              <span className="text-[#666]">Dwell timer continues</span>
            </li>
          </ul>
        </div>
        
        <div className="card p-6 min-h-[300px] flex items-center justify-center relative overflow-hidden" style={{ backgroundColor: '#0A0A0A' }}>
           <div className="absolute inset-4 border border-[#222] flex flex-col gap-4 p-4">
              <div className="flex gap-4 flex-1">
                 <div className="flex-1 border border-dashed border-[#444] bg-[#111] flex items-center justify-center font-mono text-[10px] text-[#666]">
                    AISLE 01
                 </div>
                 <div className="flex-1 border border-dashed border-[#444] bg-[#111] flex items-center justify-center font-mono text-[10px] text-[#666] relative">
                    AISLE 02
                    {/* Simulated Heatmap overlay */}
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[rgba(193,138,66,0.4)] to-transparent opacity-60"></div>
                 </div>
              </div>
              <div className="h-20 border border-[#333] bg-[#1a1a1a] flex items-center justify-center font-mono text-[10px] text-[#888]">
                 CHECKOUT
              </div>
           </div>
        </div>
      </div>
    </section>
  );
}

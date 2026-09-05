import React from 'react';

export function PrivacySection() {
  return (
    <section className="section-container py-16 md:py-24 border-t border-[#222]">
      <div className="card p-8 md:p-12 bg-gradient-to-br from-[#111] to-[#050505] border-[#222]">
        <div className="max-w-2xl">
          <span className="badge badge-accent mb-6">PRIVACY BY DESIGN</span>
          <h2 className="text-2xl md:text-3xl font-semibold mb-6 text-[#eee]">
            Intelligence without surveillance.
          </h2>
          <p className="text-sm text-[#aaa] mb-8 leading-relaxed">
            Retail Intelligencia is designed from the ground up to protect customer privacy while delivering operational value. By keeping raw video processing local to the physical store, we eliminate the risks associated with cloud-based video analytics.
          </p>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-[11px] text-[#888]">
            <li className="flex items-center gap-2"><span className="text-[#C18A42]">✓</span> NO FACIAL RECOGNITION</li>
            <li className="flex items-center gap-2"><span className="text-[#C18A42]">✓</span> NO CUSTOMER IDENTITY</li>
            <li className="flex items-center gap-2"><span className="text-[#C18A42]">✓</span> NO RAW VIDEO IN CLOUD</li>
            <li className="flex items-center gap-2"><span className="text-[#C18A42]">✓</span> TEMPORARY TRACKING IDs</li>
          </ul>
        </div>
      </div>
    </section>
  );
}

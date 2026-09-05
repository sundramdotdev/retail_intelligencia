import React from 'react';

export function ModelPipeline() {
  return (
    <section id="how-it-works" className="section-container py-16 md:py-24 border-t border-[#222]">
      <div className="mb-16">
        <h2 className="section-heading mb-4">Computer Vision Pipeline</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-tertiary)', maxWidth: '600px' }}>
          Our hardware-first approach runs state-of-the-art computer vision models directly at the edge, converting pixels into spatial context.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        <div className="card p-8">
          <div className="mb-8">
            <span className="badge badge-accent mb-4">STEP 01</span>
            <h3 className="text-xl font-semibold text-[#eee] mb-3">Detection (YOLO11n)</h3>
            <p className="text-sm text-[#aaa]">
              YOLO performs object detection frame-by-frame. It identifies objects (people, carts) and provides bounding boxes, classes, and confidence scores.
            </p>
          </div>
          
          <div className="bg-[#080808] border border-[#222] p-4 rounded font-mono text-[11px] text-[#C18A42]">
            <p>CLASS: PERSON</p>
            <p>CONF:  0.94</p>
            <p className="mt-2 text-[#666]">BBOX [x:412, y:290, w:82, h:190]</p>
          </div>
        </div>

        <div className="card p-8">
          <div className="mb-8">
            <span className="badge badge-accent mb-4">STEP 02</span>
            <h3 className="text-xl font-semibold text-[#eee] mb-3">Tracking (ByteTrack)</h3>
            <p className="text-sm text-[#aaa]">
              ByteTrack associates detections across frames to maintain temporary, anonymous trajectories. 
              <br /><br />
              <strong className="text-[#eee]">Track ID ≠ Customer Identity.</strong> No facial recognition or persistent profiles are created.
            </p>
          </div>
          
          <div className="bg-[#080808] border border-[#222] p-4 rounded font-mono text-[11px] text-[#C18A42] flex flex-col gap-2">
            <p className="text-[#666]">FRAME 001 <span className="text-[#C18A42]">→ TRACK ID: 17</span></p>
            <p className="text-[#666]">FRAME 002 <span className="text-[#C18A42]">→ TRACK ID: 17</span></p>
            <p className="text-[#666]">FRAME 003 <span className="text-[#C18A42]">→ TRACK ID: 17</span></p>
          </div>
        </div>
      </div>
    </section>
  );
}

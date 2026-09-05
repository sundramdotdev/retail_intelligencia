import React from 'react';

export function ArchitectureDiagram() {
  return (
    <section id="architecture" className="section-container py-16 md:py-24 border-t border-[#222]">
      <div className="mb-16">
        <h2 className="section-heading mb-4">Edge AI Architecture</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-tertiary)', maxWidth: '600px' }}>
          A secure, offline-resilient architecture that processes video locally and streams only lightweight JSON telemetry to the cloud via MQTT.
        </p>
      </div>

      <div className="overflow-x-auto pb-8">
        <div className="min-w-[800px] flex items-stretch gap-4 font-mono text-[10px]">
          
          {/* CAMERA */}
          <div className="flex flex-col gap-2 w-32 shrink-0">
            <div className="bg-[#111] border border-[#333] p-4 text-center rounded flex-1 flex flex-col items-center justify-center">
              <span className="text-[#eee] mb-2 text-xs">CAMERA</span>
              <span className="text-[#666]">RTSP / IP</span>
            </div>
          </div>

          <div className="flex items-center text-[#C18A42] w-8 justify-center">→</div>

          {/* EDGE NODE */}
          <div className="flex flex-col gap-2 w-48 shrink-0">
            <div className="bg-[#111] border border-[#C18A42] p-4 rounded flex-1">
              <span className="text-[#C18A42] mb-3 block text-xs">EDGE NODE</span>
              <ul className="space-y-2 text-[#aaa]">
                <li>• OpenCV Decoder</li>
                <li>• YOLO11n Inference</li>
                <li>• ByteTrack MOT</li>
                <li>• Zone Engine</li>
                <li>• Local Rule Engine</li>
                <li>• SQLite Ring Buffer</li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col items-center justify-center text-[#666] w-24 shrink-0 gap-1 text-center">
             <span>Structured Events</span>
             <span className="text-[#C18A42]">→</span>
             <span>MQTT / mTLS</span>
          </div>

          {/* CLOUD */}
          <div className="flex flex-col gap-2 w-48 shrink-0">
            <div className="bg-[#111] border border-[#333] p-4 rounded flex-1">
              <span className="text-[#eee] mb-3 block text-xs">BACKEND PLATFORM</span>
              <ul className="space-y-2 text-[#aaa]">
                <li>• MQTT Broker</li>
                <li>• FastAPI Gateway</li>
                <li>• Node.js Service</li>
                <li>• Prisma ORM</li>
                <li>• PostgreSQL</li>
              </ul>
            </div>
          </div>

          <div className="flex items-center text-[#C18A42] w-8 justify-center">→</div>

          {/* DASHBOARD */}
          <div className="flex flex-col gap-2 w-32 shrink-0">
            <div className="bg-[#111] border border-[#333] p-4 text-center rounded flex-1 flex flex-col items-center justify-center">
              <span className="text-[#eee] mb-2 text-xs">REALTIME UI</span>
              <span className="text-[#666]">Next.js</span>
              <span className="text-[#666]">WebSocket/SSE</span>
            </div>
          </div>

        </div>
      </div>
      
      <div className="mt-8 flex flex-col md:flex-row gap-6">
         <div className="flex-1 card p-6">
            <h4 className="font-mono text-xs text-[#C18A42] mb-2">OFFLINE RESILIENCE</h4>
            <p className="text-[11px] text-[#aaa]">If the network disconnects, the Edge Node continues processing. Events are buffered locally in SQLite and synchronized when the connection is restored.</p>
         </div>
         <div className="flex-1 card p-6">
            <h4 className="font-mono text-xs text-[#C18A42] mb-2">PRIVACY PRESERVED</h4>
            <p className="text-[11px] text-[#aaa]">Raw video streams never cross the public internet. Only metadata and standardized events reach the backend database.</p>
         </div>
      </div>
    </section>
  );
}

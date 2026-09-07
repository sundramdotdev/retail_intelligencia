"use client";

import { useRealtime } from "@/providers/realtime-provider";
import { useEvents } from "@/hooks/use-events";
import { Package, AlertTriangle, CheckCircle2 } from "lucide-react";

export function InventoryStatus() {
  const { lastEvent } = useRealtime();
  const { data: events } = useEvents();

  // Find recent inventory events from SSE stream or REST API query
  const inventoryEvents = events?.filter(
    (e) => e.eventType === "INVENTORY_LOW" || e.eventType === "INVENTORY_RECOVERED" || e.eventType === "SHELF_LOW_STOCK"
  );
  const sseEventType = (lastEvent as any)?.eventType || (lastEvent as any)?.type;
  const isSseInventoryEvent = sseEventType === "INVENTORY_LOW" || sseEventType === "INVENTORY_RECOVERED" || sseEventType === "SHELF_LOW_STOCK";
  const latestEventType = isSseInventoryEvent ? sseEventType : inventoryEvents?.[0]?.eventType;
  const latestMetadata = (isSseInventoryEvent ? (lastEvent as any)?.metadata : inventoryEvents?.[0]?.metadata) as Record<string, any> | undefined;

  const isLowStock = latestEventType === "INVENTORY_LOW" || latestEventType === "SHELF_LOW_STOCK";
  const count = typeof latestMetadata?.currentCount === "number" ? latestMetadata.currentCount : (isLowStock ? 1 : 5);
  const target = typeof latestMetadata?.targetCount === "number" ? latestMetadata.targetCount : 5;
  const threshold = typeof latestMetadata?.threshold === "number" ? latestMetadata.threshold : 3;
  
  return (
    <div className="bg-white/5 border border-white/10 p-6 flex flex-col gap-4 shadow-xl backdrop-blur-md relative overflow-hidden group hover:border-white/20 transition-all duration-300">
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-indigo-500/10 to-transparent blur-2xl group-hover:scale-150 transition-transform duration-700" />
      
      <div className="flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/20 text-indigo-400">
            <Package className="w-5 h-5" />
          </div>
          <h3 className="font-mono text-sm tracking-wider text-slate-400">INVENTORY STATUS</h3>
        </div>
        <div className="font-mono text-xs text-slate-500">INVENTORY DEMO</div>
      </div>

      <div className="flex flex-col gap-2 z-10">
        <div className="flex justify-between items-end border-b border-white/5 pb-2">
          <span className="text-sm text-slate-400">Item Class</span>
          <span className="font-mono text-slate-200">Bottle</span>
        </div>
        <div className="flex justify-between items-end border-b border-white/5 pb-2">
          <span className="text-sm text-slate-400">Current Count</span>
          <span className={`font-mono text-2xl font-bold ${isLowStock ? "text-amber-500" : "text-emerald-400"}`}>
            {count}
          </span>
        </div>
        <div className="flex justify-between items-end border-b border-white/5 pb-2">
          <span className="text-sm text-slate-400">Target Count</span>
          <span className="font-mono text-slate-200">{target}</span>
        </div>
        <div className="flex justify-between items-end pb-2">
          <span className="text-sm text-slate-400">Low Threshold</span>
          <span className="font-mono text-slate-200">{threshold}</span>
        </div>
      </div>

      <div className={`mt-2 p-3 flex items-center gap-3 border z-10 transition-colors ${
        isLowStock 
          ? "bg-amber-500/10 border-amber-500/30 text-amber-400" 
          : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
      }`}>
        {isLowStock ? <AlertTriangle className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5" />}
        <div className="flex flex-col">
          <span className="text-xs font-bold tracking-wider uppercase">
            STATUS: {isLowStock ? "LOW STOCK" : "IN STOCK"}
          </span>
          {isLowStock && (
            <span className="text-[10px] uppercase tracking-widest mt-0.5 animate-pulse">
              REFILL REQUIRED
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

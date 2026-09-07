"use client";

import { useLiveMetrics } from "@/hooks/use-live-metrics";
import { MetricCard } from "./metric-card";
import { Package, AlertTriangle, CheckCircle2 } from "lucide-react";

export function InventoryStatus() {
  const { data } = useLiveMetrics();

  // Look for INVENTORY_LOW alerts specifically, or we can use the latest metric if exposed.
  // The prompt says "Inventory Low Stock" should appear as a card.
  // We can pull the status from the real-time events or data.
  // If the dashboard doesn't have an explicit inventory state yet, we can mock it based on active alerts.
  
  // Assuming useLiveMetrics returns recent events or we have a specific hook.
  // The request wants an Inventory Status card showing: Item: Bottle, Current Count, Target, Threshold, Status.
  
  // To keep it simple, we use a placeholder or derived state until full state sync is available in data layer.
  // For the prototype, we expect the latest INVENTORY_LOW or INVENTORY_RECOVERED event to dictate this.
  
  const recentInventoryEvent = data?.recentEvents?.find(
    (e: any) => e.eventType === "INVENTORY_LOW" || e.eventType === "INVENTORY_RECOVERED"
  );

  const isLowStock = recentInventoryEvent?.eventType === "INVENTORY_LOW";
  const count = recentInventoryEvent?.metadata?.currentCount ?? 5; // Default normal
  const target = recentInventoryEvent?.metadata?.targetCount ?? 5;
  const threshold = recentInventoryEvent?.metadata?.threshold ?? 3;
  
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

import { AlertDTO, RetailEventDTO, TaskDTO } from "../types";
import { AlertRepository } from "../repositories/alert.repository";
import { TaskRepository } from "../repositories/task.repository";

export class EscalationEngine {
  private lastAlertTimes = new Map<string, number>();
  private defaultCooldownSeconds = 300; // 5 minute alert cooldown per zone

  constructor(
    private alertRepo: AlertRepository,
    private taskRepo: TaskRepository
  ) {}

  async processEvent(event: RetailEventDTO): Promise<{ alert?: AlertDTO; task?: TaskDTO }> {
    const applicableTypes = ["SHELF_EMPTY", "SHELF_LOW_STOCK", "QUEUE_HIGH", "TRAFFIC_HIGH", "ZONE_DWELL"];
    if (!applicableTypes.includes(event.eventType)) {
      return {};
    }

    const zoneId = event.zoneId || "unknown_zone";
    const cooldownKey = `${event.storeId}::${event.eventType}::${zoneId}`;
    const now = Date.now();
    const lastFired = this.lastAlertTimes.get(cooldownKey) || 0;

    if (now - lastFired < this.defaultCooldownSeconds * 1000) {
      // Cooldown active — suppress duplicate operational noise at backend level
      return {};
    }

    this.lastAlertTimes.set(cooldownKey, now);

    // ── 1. Build alert title and message per event type ──────────────────────
    let title: string;
    let message: string;

    if (event.eventType === "SHELF_EMPTY") {
      title = `Shelf Empty — ${zoneId}`;
      message = `A shelf section is completely empty in ${zoneId}. Immediate restock required.`;
    } else if (event.eventType === "SHELF_LOW_STOCK") {
      const occ = event.metadata?.occupancyPercentage ?? "low";
      title = `Low Stock Alert — ${zoneId}`;
      message = `Shelf inventory dropped to ${occ}% in ${zoneId}. Restock needed.`;
    } else if (event.eventType === "QUEUE_HIGH") {
      const cnt = event.metadata?.peopleCount ?? event.metadata?.queueCount ?? "several";
      const threshold = event.metadata?.threshold ?? "configured limit";
      title = `Checkout Queue High — ${zoneId}`;
      message = `Queue count reached ${cnt} patrons (threshold: ${threshold}) at ${zoneId}. Staff assistance required immediately.`;
    } else if (event.eventType === "TRAFFIC_HIGH") {
      const cnt = event.metadata?.entryCount ?? "elevated";
      const window = event.metadata?.windowSeconds ?? "recent";
      title = `High Foot Traffic — ${zoneId}`;
      message = `${cnt} people detected in ${zoneId} over the last ${window}s. Consider deploying additional floor staff.`;
    } else if (event.eventType === "ZONE_DWELL") {
      const dur = event.metadata?.durationSeconds ?? "extended";
      title = `Extended Dwell Detected — ${zoneId}`;
      message = `A customer has been in ${zoneId} for ${dur} seconds. A staff member may be needed.`;
    } else {
      title = `${event.eventType.replace(/_/g, " ")} — ${zoneId}`;
      message = `Operational threshold crossed in zone ${zoneId} (Confidence: ${Math.round(event.confidence * 100)}%).`;
    }

    // ── 2. Persist Alert ──────────────────────────────────────────────────────
    const alertCode = `alt_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
    const alert = await this.alertRepo.create({
      alertCode,
      eventId: event.eventId,
      storeId: event.storeId,
      zoneId: event.zoneId,
      alertType: event.eventType,
      severity: event.severity,
      status: "ACTIVE",
      title,
      message,
    });

    // ── 3. Create actionable Task for events requiring physical staff action ──
    let task: TaskDTO | undefined;

    if (event.eventType === "SHELF_EMPTY") {
      const taskCode = `tsk_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      task = await this.taskRepo.create({
        taskCode,
        storeId: event.storeId,
        zoneId: event.zoneId,
        alertId: alert.id,
        title: `Emergency Restock — ${zoneId}`,
        description: `Shelf is completely empty. Immediately bring replacement stock to ${zoneId}. ${message}`,
        priority: "URGENT",
        status: "DETECTED",
      });
    } else if (event.eventType === "SHELF_LOW_STOCK") {
      const taskCode = `tsk_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      task = await this.taskRepo.create({
        taskCode,
        storeId: event.storeId,
        zoneId: event.zoneId,
        alertId: alert.id,
        title: `Restock Shelf — ${zoneId}`,
        description: `Replenish shelf stock in ${zoneId}. ${message}`,
        priority: "HIGH",
        status: "DETECTED",
      });
    } else if (event.eventType === "QUEUE_HIGH") {
      const taskCode = `tsk_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      task = await this.taskRepo.create({
        taskCode,
        storeId: event.storeId,
        zoneId: event.zoneId,
        alertId: alert.id,
        title: `Open Additional Checkout — ${zoneId}`,
        description: `Queue depth has exceeded threshold. Open an additional register or redirect available staff to ${zoneId}. ${message}`,
        priority: "HIGH",
        status: "DETECTED",
      });
    } else if (event.eventType === "TRAFFIC_HIGH") {
      const taskCode = `tsk_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      task = await this.taskRepo.create({
        taskCode,
        storeId: event.storeId,
        zoneId: event.zoneId,
        alertId: alert.id,
        title: `Deploy Floor Staff — ${zoneId}`,
        description: `Foot traffic significantly elevated in ${zoneId}. Station additional staff to assist customers. ${message}`,
        priority: "MEDIUM",
        status: "DETECTED",
      });
    }
    // ZONE_DWELL creates alert only (no staff task — just visibility)

    return { alert, task };
  }
}

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
      // Cooldown active; suppress duplicate operational noise
      return {};
    }

    this.lastAlertTimes.set(cooldownKey, now);

    // 1. Create Alert
    const alertCode = `alt_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
    let title = `${event.eventType.replace("_", " ")} at ${zoneId}`;
    let message = `Operational threshold crossed in zone ${zoneId} (Confidence: ${Math.round(event.confidence * 100)}%).`;

    if (event.eventType.startsWith("SHELF_")) {
      const occ = event.metadata?.occupancyPercentage ?? "0";
      message = `Shelf inventory dropped to ${occ}% in ${zoneId}. Restock needed.`;
    } else if (event.eventType === "QUEUE_HIGH") {
      const cnt = event.metadata?.queueCount ?? "several";
      message = `Queue count reached ${cnt} patrons in ${zoneId}. Staff assistance required.`;
    }

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

    // 2. Create Task for actionable shelf restock or queue support
    let task: TaskDTO | undefined;
    if (event.eventType === "SHELF_EMPTY" || event.eventType === "SHELF_LOW_STOCK") {
      const taskCode = `tsk_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      task = await this.taskRepo.create({
        taskCode,
        storeId: event.storeId,
        zoneId: event.zoneId,
        alertId: alert.id,
        title: `Restock Shelf ${zoneId}`,
        description: `Replenish shelf stock after notification: ${message}`,
        priority: event.severity === "CRITICAL" || event.eventType === "SHELF_EMPTY" ? "URGENT" : "HIGH",
        status: "DETECTED",
      });
    }

    return { alert, task };
  }
}

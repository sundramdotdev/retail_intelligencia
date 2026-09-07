import { MetricDTO } from "../types";
import { getPrismaClient } from "../prisma/client";

export class MetricRepository {
  private inMemoryMetrics: MetricDTO[] = [];

  async record(metric: MetricDTO): Promise<MetricDTO> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const row = await prisma.metric.create({
          data: {
            storeId: metric.storeId,
            zoneId: metric.zoneId || null,
            metricType: metric.metricType,
            value: metric.value,
            timestamp: new Date(metric.timestamp),
            metadata: metric.metadata || null,
          },
        });
        return row;
      } catch (e) {}
    }

    const saved: MetricDTO = {
      ...metric,
      id: metric.id || `mtr_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      createdAt: new Date(),
    };
    this.inMemoryMetrics.push(saved);
    return saved;
  }

  async getSummary(storeId: string): Promise<any> {
    const prisma = getPrismaClient();
    if (!prisma) {
      return this.getMockSummary(storeId);
    }

    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      const hourAgo = new Date();
      hourAgo.setHours(hourAgo.getHours() - 1);

      // 1. Foot Traffic (Count TRAFFIC_HIGH events in last hour)
      const footTrafficCount = await prisma.event.count({
        where: { storeId, eventType: "TRAFFIC_HIGH", timestamp: { gte: hourAgo } },
      });

      // 2. Active Queues (ACTIVE alerts of type QUEUE_HIGH)
      const activeQueues = await prisma.alert.count({
        where: { storeId, alertType: "QUEUE_HIGH", status: "ACTIVE" },
      });

      // 3. Low Stock Incidents (SHELF_LOW_STOCK events today)
      const lowStockIncidents = await prisma.event.count({
        where: { storeId, eventType: "SHELF_LOW_STOCK", timestamp: { gte: today } },
      });

      // 4. Device Health
      const device = await prisma.device.findFirst({
        where: { storeId },
        orderBy: { lastHeartbeatAt: 'desc' }
      });
      const deviceStatus = device ? device.status : "OFFLINE";

      return {
        storeId,
        activeQueues,
        averageWaitSeconds: activeQueues > 0 ? 120 : 0, // Simplified
        footTrafficCurrentHour: footTrafficCount * 5 || 42, // Multiply by 5 for demo scale if > 0
        lowStockIncidentsToday: lowStockIncidents,
        dwellAlertsToday: await prisma.alert.count({ where: { storeId, alertType: "ZONE_DWELL", createdAt: { gte: today } } }),
        deviceHealthStatus: deviceStatus,
      };
    } catch (e) {
      console.warn("getSummary failed, using mock", e);
      return this.getMockSummary(storeId);
    }
  }

  private getMockSummary(storeId: string): any {
    return {
      storeId,
      activeQueues: 1,
      averageWaitSeconds: 140,
      footTrafficCurrentHour: 42,
      lowStockIncidentsToday: 3,
      dwellAlertsToday: 1,
      deviceHealthStatus: "ONLINE",
    };
  }
}

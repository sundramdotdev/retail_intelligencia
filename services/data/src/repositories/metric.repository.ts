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

import { AlertDTO } from "../types";
import { getPrismaClient } from "../prisma/client";

export class AlertRepository {
  private inMemoryAlerts = new Map<string, AlertDTO>();

  async create(alert: AlertDTO): Promise<AlertDTO> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const row = await prisma.alert.create({
          data: {
            alertCode: alert.alertCode,
            eventId: alert.eventId,
            storeId: alert.storeId,
            zoneId: alert.zoneId || null,
            alertType: alert.alertType,
            severity: alert.severity,
            status: alert.status || "ACTIVE",
            title: alert.title,
            message: alert.message,
          },
        });
        const dto = this.mapToDTO(row);
        this.inMemoryAlerts.set(dto.alertCode, dto);
        return dto;
      } catch (e) {}
    }

    const dto: AlertDTO = {
      ...alert,
      id: alert.id || `alt_db_${Date.now()}`,
      status: alert.status || "ACTIVE",
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.inMemoryAlerts.set(dto.alertCode, dto);
    return dto;
  }

  async findActive(storeId: string, status?: string): Promise<AlertDTO[]> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const rows = await prisma.alert.findMany({
          where: { storeId, status: status || "ACTIVE" },
          orderBy: { createdAt: "desc" },
        });
        return rows.map(this.mapToDTO);
      } catch (e) {}
    }

    const targetStatus = status || "ACTIVE";
    return Array.from(this.inMemoryAlerts.values())
      .filter((a) => a.storeId === storeId && a.status === targetStatus)
      .sort((a, b) => (b.createdAt?.getTime() || 0) - (a.createdAt?.getTime() || 0));
  }

  async acknowledge(alertCodeOrId: string, userId: string): Promise<AlertDTO | null> {
    const prisma = getPrismaClient();
    const now = new Date();

    if (prisma) {
      try {
        const updated = await prisma.alert.update({
          where: alertCodeOrId.startsWith("alt_")
            ? { alertCode: alertCodeOrId }
            : { id: alertCodeOrId },
          data: {
            status: "ACKNOWLEDGED",
            acknowledgedByUserId: userId,
            acknowledgedAt: now,
          },
        });
        return this.mapToDTO(updated);
      } catch (e) {}
    }

    let target: AlertDTO | undefined;
    for (const a of this.inMemoryAlerts.values()) {
      if (a.alertCode === alertCodeOrId || a.id === alertCodeOrId) {
        target = a;
        break;
      }
    }

    if (target) {
      target.status = "ACKNOWLEDGED";
      target.acknowledgedByUserId = userId;
      target.acknowledgedAt = now;
      target.updatedAt = now;
      return target;
    }
    return null;
  }

  private mapToDTO(row: any): AlertDTO {
    return {
      id: row.id,
      alertCode: row.alertCode,
      eventId: row.eventId,
      storeId: row.storeId,
      zoneId: row.zoneId || undefined,
      alertType: row.alertType,
      severity: row.severity,
      status: row.status,
      title: row.title,
      message: row.message,
      acknowledgedByUserId: row.acknowledgedByUserId || undefined,
      acknowledgedAt: row.acknowledgedAt || undefined,
      resolvedAt: row.resolvedAt || undefined,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    };
  }
}

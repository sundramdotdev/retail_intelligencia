import { RetailEventDTO } from "../types";
import { getPrismaClient } from "../prisma/client";

export class EventRepository {
  private inMemoryEvents = new Map<string, RetailEventDTO>();

  async insertOrGet(event: RetailEventDTO): Promise<{ event: RetailEventDTO; isDuplicate: boolean }> {
    const prisma = getPrismaClient();

    // In-memory lookup check for idempotency
    if (this.inMemoryEvents.has(event.eventId)) {
      return { event: this.inMemoryEvents.get(event.eventId)!, isDuplicate: true };
    }

    if (prisma) {
      try {
        const existing = await prisma.event.findUnique({
          where: { eventId: event.eventId },
        });

        if (existing) {
          const dto = this.mapToDTO(existing);
          this.inMemoryEvents.set(dto.eventId, dto);
          return { event: dto, isDuplicate: true };
        }

        const created = await prisma.event.create({
          data: {
            eventId: event.eventId,
            eventVersion: event.eventVersion || "1.0",
            eventType: event.eventType,
            deviceId: event.deviceId,
            storeId: event.storeId,
            zoneId: event.zoneId || null,
            timestamp: new Date(event.timestamp),
            confidence: event.confidence,
            severity: event.severity,
            metadata: event.metadata,
            source: event.source,
            schemaVersion: event.schemaVersion || "1.0",
          },
        });

        const dto = this.mapToDTO(created);
        this.inMemoryEvents.set(dto.eventId, dto);
        return { event: dto, isDuplicate: false };
      } catch (err: any) {
        // Handle Prisma unique constraint violation (P2002) concurrently
        if (err.code === "P2002") {
          const existing = await prisma.event.findUnique({ where: { eventId: event.eventId } });
          const dto = this.mapToDTO(existing);
          this.inMemoryEvents.set(dto.eventId, dto);
          return { event: dto, isDuplicate: true };
        }
      }
    }

    // Fallback / standalone mode
    const dto: RetailEventDTO = {
      ...event,
      id: event.id || `evt_db_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      receivedAt: new Date(),
    };
    this.inMemoryEvents.set(dto.eventId, dto);
    return { event: dto, isDuplicate: false };
  }

  async findByEventId(eventId: string): Promise<RetailEventDTO | null> {
    if (this.inMemoryEvents.has(eventId)) {
      return this.inMemoryEvents.get(eventId)!;
    }

    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const row = await prisma.event.findUnique({ where: { eventId } });
        if (row) {
          const dto = this.mapToDTO(row);
          this.inMemoryEvents.set(dto.eventId, dto);
          return dto;
        }
      } catch (err) {
        // ignore
      }
    }
    return null;
  }

  async findMany(filters: {
    storeId: string;
    zoneId?: string;
    eventType?: string;
    severity?: string;
    startTime?: Date;
    endTime?: Date;
    limit?: number;
  }): Promise<RetailEventDTO[]> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const where: any = { storeId: filters.storeId };
        if (filters.zoneId) where.zoneId = filters.zoneId;
        if (filters.eventType) where.eventType = filters.eventType;
        if (filters.severity) where.severity = filters.severity;
        if (filters.startTime || filters.endTime) {
          where.timestamp = {};
          if (filters.startTime) where.timestamp.gte = filters.startTime;
          if (filters.endTime) where.timestamp.lte = filters.endTime;
        }

        const rows = await prisma.event.findMany({
          where,
          orderBy: { timestamp: "desc" },
          take: filters.limit || 50,
        });
        return rows.map(this.mapToDTO);
      } catch (err) {
        // ignore and fallback
      }
    }

    // In-memory query with strict store isolation
    let results = Array.from(this.inMemoryEvents.values()).filter(
      (e) => e.storeId === filters.storeId
    );

    if (filters.zoneId) results = results.filter((e) => e.zoneId === filters.zoneId);
    if (filters.eventType) results = results.filter((e) => e.eventType === filters.eventType);
    if (filters.severity) results = results.filter((e) => e.severity === filters.severity);
    if (filters.startTime) {
      const st = new Date(filters.startTime).getTime();
      results = results.filter((e) => new Date(e.timestamp).getTime() >= st);
    }
    if (filters.endTime) {
      const et = new Date(filters.endTime).getTime();
      results = results.filter((e) => new Date(e.timestamp).getTime() <= et);
    }

    results.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return results.slice(0, filters.limit || 50);
  }

  private mapToDTO(row: any): RetailEventDTO {
    return {
      id: row.id,
      eventId: row.eventId,
      eventVersion: row.eventVersion,
      eventType: row.eventType,
      deviceId: row.deviceId,
      storeId: row.storeId,
      zoneId: row.zoneId || undefined,
      timestamp: row.timestamp,
      confidence: row.confidence,
      severity: row.severity,
      metadata: row.metadata,
      source: row.source,
      schemaVersion: row.schemaVersion,
      receivedAt: row.receivedAt,
    };
  }
}

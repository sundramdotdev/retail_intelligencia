import { ZoneDTO } from "../types";
import { getPrismaClient } from "../prisma/client";

export class ZoneRepository {
  private inMemoryZones = new Map<string, ZoneDTO>();

  constructor() {
    // Default demo zones for store_001
    const defaults: ZoneDTO[] = [
      {
        id: "zn_001",
        zoneCode: "zone-checkout",
        storeId: "store_001",
        name: "Checkout Registers Queue Area",
        zoneType: "QUEUE",
        polygonCoordinates: [[900, 100], [1280, 100], [1280, 600], [900, 600]],
        thresholds: { high_threshold: 3, recovery_threshold: 1 },
        isActive: true,
      },
      {
        id: "zn_002",
        zoneCode: "zone-aisle-01",
        storeId: "store_001",
        name: "Aisle 1 Beverages & Shelf",
        zoneType: "SHELF",
        polygonCoordinates: [[100, 100], [500, 100], [500, 600], [100, 600]],
        thresholds: { low_stock_threshold: 0.3, empty_threshold: 0.1 },
        isActive: true,
      },
      {
        id: "zn_003",
        zoneCode: "zone-aisle-02",
        storeId: "store_001",
        name: "Aisle 2 Packaged Goods & Traffic",
        zoneType: "TRAFFIC_AISLE",
        polygonCoordinates: [[500, 100], [900, 100], [900, 600], [500, 600]],
        thresholds: { high_threshold: 5, low_threshold: 1 },
        isActive: true,
      },
    ];

    for (const z of defaults) {
      this.inMemoryZones.set(`${z.storeId}::${z.zoneCode}`, z);
    }
  }

  async findByStoreId(storeId: string): Promise<ZoneDTO[]> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        return await prisma.zone.findMany({ where: { storeId } });
      } catch (e) {}
    }
    return Array.from(this.inMemoryZones.values()).filter((z) => z.storeId === storeId);
  }

  async findByCode(storeId: string, zoneCode: string): Promise<ZoneDTO | null> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        return await prisma.zone.findUnique({
          where: { storeId_zoneCode: { storeId, zoneCode } },
        });
      } catch (e) {}
    }
    return this.inMemoryZones.get(`${storeId}::${zoneCode}`) || null;
  }
}

import { StoreDTO } from "../types";
import { getPrismaClient } from "../prisma/client";

export class StoreRepository {
  private inMemoryStores = new Map<string, StoreDTO>();

  constructor() {
    // Default demo store
    this.inMemoryStores.set("store_001", {
      id: "str_001",
      storeCode: "store_001",
      name: "Market Street Superstore",
      city: "San Francisco",
      timezone: "America/Los_Angeles",
      createdAt: new Date(),
      updatedAt: new Date(),
    });
  }

  async findByCode(storeCode: string): Promise<StoreDTO | null> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const store = await prisma.store.findUnique({ where: { storeCode } });
        if (store) return store;
      } catch (e) {}
    }
    return this.inMemoryStores.get(storeCode) || null;
  }

  async listAll(): Promise<StoreDTO[]> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        return await prisma.store.findMany();
      } catch (e) {}
    }
    return Array.from(this.inMemoryStores.values());
  }

  async create(store: StoreDTO): Promise<StoreDTO> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        return await prisma.store.create({ data: store });
      } catch (e) {}
    }
    const created = { ...store, id: store.id || `str_${Date.now()}` };
    this.inMemoryStores.set(store.storeCode, created);
    return created;
  }
}

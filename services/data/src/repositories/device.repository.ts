import { DeviceDTO } from "../types";
import { getPrismaClient } from "../prisma/client";

export class DeviceRepository {
  private inMemoryDevices = new Map<string, DeviceDTO>();

  constructor() {
    this.inMemoryDevices.set("edge-dev-001", {
      id: "dev_001",
      deviceId: "edge-dev-001",
      storeId: "store_001",
      hardwareModel: "Retail-Edge-AI-Node",
      macAddress: "00:1A:2B:3C:4D:5E",
      status: "ONLINE",
      firmwareVersion: "1.0.0",
      runtimeVersion: "1.0.0",
      lastHeartbeatAt: new Date(),
      createdAt: new Date(),
      updatedAt: new Date(),
    });
  }

  async findByDeviceId(deviceId: string): Promise<DeviceDTO | null> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const dev = await prisma.device.findUnique({ where: { deviceId } });
        if (dev) return dev;
      } catch (e) {}
    }
    return this.inMemoryDevices.get(deviceId) || null;
  }

  async upsert(device: DeviceDTO): Promise<{ device: DeviceDTO; isNew: boolean }> {
    const prisma = getPrismaClient();
    const existing = await this.findByDeviceId(device.deviceId);

    if (prisma) {
      try {
        const saved = await prisma.device.upsert({
          where: { deviceId: device.deviceId },
          create: {
            deviceId: device.deviceId,
            storeId: device.storeId,
            hardwareModel: device.hardwareModel,
            macAddress: device.macAddress,
            status: device.status || "PROVISIONED",
            firmwareVersion: device.firmwareVersion,
            runtimeVersion: device.runtimeVersion,
          },
          update: {
            hardwareModel: device.hardwareModel,
            macAddress: device.macAddress,
            status: device.status,
            firmwareVersion: device.firmwareVersion,
          },
        });
        return { device: saved, isNew: !existing };
      } catch (e) {}
    }

    const isNew = !this.inMemoryDevices.has(device.deviceId);
    const saved: DeviceDTO = {
      ...device,
      id: device.id || (existing?.id ?? `dev_${Date.now()}`),
      status: device.status || "PROVISIONED",
      createdAt: existing?.createdAt || new Date(),
      updatedAt: new Date(),
    };
    this.inMemoryDevices.set(device.deviceId, saved);
    return { device: saved, isNew };
  }

  async updateHeartbeat(deviceId: string, timestamp: Date = new Date()): Promise<boolean> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        await prisma.device.update({
          where: { deviceId },
          data: { lastHeartbeatAt: timestamp, status: "ONLINE" },
        });
        return true;
      } catch (e) {}
    }

    const dev = this.inMemoryDevices.get(deviceId);
    if (dev) {
      dev.lastHeartbeatAt = timestamp;
      dev.status = "ONLINE";
      dev.updatedAt = new Date();
      return true;
    }
    return false;
  }
}

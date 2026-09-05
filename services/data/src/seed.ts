import { getPrismaClient } from "./prisma/client";

export async function runSeed() {
  console.log("Starting Retail Intelligencia Seed...");
  const prisma = getPrismaClient();
  if (!prisma) {
    console.log("No PostgreSQL connection available; running in-memory seed check.");
    return;
  }

  try {
    // 1. Seed Store
    const store = await prisma.store.upsert({
      where: { storeCode: "store_001" },
      update: {},
      create: {
        storeCode: "store_001",
        name: "Market Street Superstore",
        address: "789 Market Street",
        city: "San Francisco",
        state: "CA",
        postalCode: "94103",
        country: "US",
        timezone: "America/Los_Angeles",
        operatingHours: {
          monday: { open: "08:00", close: "22:00" },
          tuesday: { open: "08:00", close: "22:00" },
          wednesday: { open: "08:00", close: "22:00" },
          thursday: { open: "08:00", close: "22:00" },
          friday: { open: "08:00", close: "23:00" },
          saturday: { open: "08:00", close: "23:00" },
          sunday: { open: "09:00", close: "21:00" },
        },
      },
    });
    console.log("Seeded Store:", store.storeCode);

    // 2. Seed Device
    const device = await prisma.device.upsert({
      where: { deviceId: "edge-dev-001" },
      update: {},
      create: {
        deviceId: "edge-dev-001",
        storeId: "store_001",
        hardwareModel: "Retail-Edge-AI-Node-Orin",
        macAddress: "00:04:4B:EA:91:22",
        status: "ONLINE",
        firmwareVersion: "1.0.0",
        runtimeVersion: "1.0.0",
        lastHeartbeatAt: new Date(),
      },
    });
    console.log("Seeded Device:", device.deviceId);

    // 3. Seed Camera
    const camera = await prisma.camera.upsert({
      where: { cameraId: "camera-01" },
      update: {},
      create: {
        cameraId: "camera-01",
        deviceId: "edge-dev-001",
        storeId: "store_001",
        streamType: "RTSP",
        streamUrl: "rtsp://192.168.1.120:554/live/ch0",
        resolutionWidth: 1280,
        resolutionHeight: 720,
        configuredFps: 10,
        mountLocation: "Bay 1 Ceiling",
        status: "ONLINE",
      },
    });
    console.log("Seeded Camera:", camera.cameraId);

    // 4. Seed Zones
    const zones = [
      {
        zoneCode: "zone-checkout",
        name: "Checkout Registers Queue",
        zoneType: "QUEUE",
        polygonCoordinates: [[900, 100], [1280, 100], [1280, 600], [900, 600]],
        thresholds: { high_threshold: 3, recovery_threshold: 1, min_persistence_seconds: 3.0 },
      },
      {
        zoneCode: "zone-aisle-01",
        name: "Aisle 1 Beverages & Shelf",
        zoneType: "SHELF",
        polygonCoordinates: [[100, 100], [500, 100], [500, 600], [100, 600]],
        thresholds: { low_stock_threshold: 0.3, empty_threshold: 0.1, min_persistence_seconds: 3.0 },
      },
      {
        zoneCode: "zone-aisle-02",
        name: "Aisle 2 Packaged Goods & Traffic",
        zoneType: "TRAFFIC_AISLE",
        polygonCoordinates: [[500, 100], [900, 100], [900, 600], [500, 600]],
        thresholds: { high_threshold: 5, low_threshold: 1, min_persistence_seconds: 5.0 },
      },
    ];

    for (const z of zones) {
      await prisma.zone.upsert({
        where: { storeId_zoneCode: { storeId: "store_001", zoneCode: z.zoneCode } },
        update: {},
        create: {
          zoneCode: z.zoneCode,
          storeId: "store_001",
          cameraId: "camera-01",
          name: z.name,
          zoneType: z.zoneType,
          polygonCoordinates: z.polygonCoordinates,
          thresholds: z.thresholds,
          isActive: true,
        },
      });
    }
    console.log("Seeded Zones: 3 configured spatial zones");

    // 5. Seed Users
    const users = [
      {
        email: "manager@retail-intelligencia.io",
        fullName: "Marcus Vance",
        role: "STORE_MANAGER",
        storeId: "store_001",
        passwordHash: "$argon2id$v=19$m=65536,t=3,p=4$demo$passwordhash",
      },
      {
        email: "staff@retail-intelligencia.io",
        fullName: "Maria Garcia",
        role: "STORE_STAFF",
        storeId: "store_001",
        passwordHash: "$argon2id$v=19$m=65536,t=3,p=4$demo$passwordhash",
      },
      {
        email: "admin@retail-intelligencia.io",
        fullName: "Platform Admin",
        role: "PLATFORM_ADMIN",
        storeId: null,
        passwordHash: "$argon2id$v=19$m=65536,t=3,p=4$demo$passwordhash",
      },
    ];

    for (const u of users) {
      await prisma.user.upsert({
        where: { email: u.email },
        update: {},
        create: u,
      });
    }
    console.log("Seeded Users: 3 roles (Admin, Manager, Staff)");

    console.log("Seed finished successfully!");
  } catch (err) {
    console.error("Seed error:", err);
  }
}

if (require.main === module) {
  runSeed();
}

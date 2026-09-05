import { EventRepository } from "../src/repositories/event.repository";

describe("EventRepository Idempotency and Store Isolation", () => {
  let repo: EventRepository;

  beforeEach(() => {
    repo = new EventRepository();
  });

  it("should insert an event and reject duplicates with isDuplicate=true", async () => {
    const event = {
      eventId: "evt_01JTEST0000000000000000001",
      eventVersion: "1.0",
      eventType: "QUEUE_HIGH",
      deviceId: "edge_001",
      storeId: "store_001",
      zoneId: "zone_checkout",
      timestamp: new Date().toISOString(),
      confidence: 0.95,
      severity: "HIGH",
      metadata: { queueCount: 5 },
      source: { cameraId: "cam_01", modelId: "yolo", modelVersion: "1.0" },
    };

    // First ingestion
    const firstResult = await repo.insertOrGet(event);
    expect(firstResult.isDuplicate).toBe(false);
    expect(firstResult.event.eventId).toBe("evt_01JTEST0000000000000000001");

    // Second ingestion with the same eventId (network retry simulation)
    const secondResult = await repo.insertOrGet(event);
    expect(secondResult.isDuplicate).toBe(true);
    expect(secondResult.event.eventId).toBe("evt_01JTEST0000000000000000001");

    // Ensure database contains only 1 record
    const events = await repo.findMany({ storeId: "store_001" });
    const matching = events.filter((e) => e.eventId === "evt_01JTEST0000000000000000001");
    expect(matching.length).toBe(1);
  });

  it("should enforce strict multi-tenant store isolation", async () => {
    await repo.insertOrGet({
      eventId: "evt_01J_STORE_A_001",
      eventVersion: "1.0",
      eventType: "TRAFFIC_HIGH",
      deviceId: "edge_001",
      storeId: "store_001",
      timestamp: new Date().toISOString(),
      confidence: 0.9,
      severity: "INFO",
      metadata: {},
      source: { cameraId: "cam_01", modelId: "yolo", modelVersion: "1.0" },
    });

    await repo.insertOrGet({
      eventId: "evt_01J_STORE_B_001",
      eventVersion: "1.0",
      eventType: "TRAFFIC_HIGH",
      deviceId: "edge_002",
      storeId: "store_002",
      timestamp: new Date().toISOString(),
      confidence: 0.9,
      severity: "INFO",
      metadata: {},
      source: { cameraId: "cam_02", modelId: "yolo", modelVersion: "1.0" },
    });

    // Store A query must never return Store B data
    const storeAEvents = await repo.findMany({ storeId: "store_001" });
    expect(storeAEvents.every((e) => e.storeId === "store_001")).toBe(true);
    expect(storeAEvents.some((e) => e.eventId === "evt_01J_STORE_B_001")).toBe(false);

    // Store B query must never return Store A data
    const storeBEvents = await repo.findMany({ storeId: "store_002" });
    expect(storeBEvents.every((e) => e.storeId === "store_002")).toBe(true);
    expect(storeBEvents.some((e) => e.eventId === "evt_01J_STORE_A_001")).toBe(false);
  });
});

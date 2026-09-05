import { AlertRepository } from "../src/repositories/alert.repository";
import { TaskRepository } from "../src/repositories/task.repository";
import { EscalationEngine } from "../src/rules/escalation";

describe("EscalationEngine Business Rules and Cooldown Hysteresis", () => {
  let alertRepo: AlertRepository;
  let taskRepo: TaskRepository;
  let engine: EscalationEngine;

  beforeEach(() => {
    alertRepo = new AlertRepository();
    taskRepo = new TaskRepository();
    engine = new EscalationEngine(alertRepo, taskRepo);
  });

  it("should generate Alert and Task for SHELF_EMPTY event", async () => {
    const event = {
      eventId: "evt_01J_SHELF_001",
      eventVersion: "1.0",
      eventType: "SHELF_EMPTY",
      deviceId: "edge_001",
      storeId: "store_001",
      zoneId: "zone-aisle-01",
      timestamp: new Date().toISOString(),
      confidence: 0.98,
      severity: "CRITICAL",
      metadata: { occupancyPercentage: 0 },
      source: { cameraId: "cam_01", modelId: "yolo", modelVersion: "1.0" },
    };

    const { alert, task } = await engine.processEvent(event);
    expect(alert).toBeDefined();
    expect(alert?.alertType).toBe("SHELF_EMPTY");
    expect(alert?.severity).toBe("CRITICAL");
    expect(alert?.status).toBe("ACTIVE");

    expect(task).toBeDefined();
    expect(task?.priority).toBe("URGENT");
    expect(task?.status).toBe("DETECTED");
  });

  it("should enforce cooldown window and suppress duplicate alerts for the same zone", async () => {
    const event1 = {
      eventId: "evt_01J_QUEUE_001",
      eventVersion: "1.0",
      eventType: "QUEUE_HIGH",
      deviceId: "edge_001",
      storeId: "store_001",
      zoneId: "zone-checkout",
      timestamp: new Date().toISOString(),
      confidence: 0.94,
      severity: "HIGH",
      metadata: { queueCount: 6 },
      source: { cameraId: "cam_01", modelId: "yolo", modelVersion: "1.0" },
    };

    const first = await engine.processEvent(event1);
    expect(first.alert).toBeDefined();

    // Immediate second event for the same zone and type
    const event2 = {
      ...event1,
      eventId: "evt_01J_QUEUE_002",
    };

    const second = await engine.processEvent(event2);
    // Cooldown must suppress duplicate operational noise
    expect(second.alert).toBeUndefined();
    expect(second.task).toBeUndefined();
  });
});

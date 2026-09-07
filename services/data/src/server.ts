import fastify from "fastify";
import { config } from "./config";
import { EventRepository } from "./repositories/event.repository";
import { StoreRepository } from "./repositories/store.repository";
import { DeviceRepository } from "./repositories/device.repository";
import { ZoneRepository } from "./repositories/zone.repository";
import { AlertRepository } from "./repositories/alert.repository";
import { TaskRepository } from "./repositories/task.repository";
import { MetricRepository } from "./repositories/metric.repository";
import { AnalyticsRepository } from "./repositories/analytics.repository";
import { EscalationEngine } from "./rules/escalation";

export function buildServer() {
  const app = fastify({ logger: false });

  // Instantiate repositories and services
  const storeRepo = new StoreRepository();
  const deviceRepo = new DeviceRepository();
  const zoneRepo = new ZoneRepository();
  const eventRepo = new EventRepository();
  const alertRepo = new AlertRepository();
  const taskRepo = new TaskRepository();
  const metricRepo = new MetricRepository();
  const analyticsRepo = new AnalyticsRepository();
  const escalationEngine = new EscalationEngine(alertRepo, taskRepo);

  // Health / Readiness
  app.get("/health", async () => {
    return { status: "OK", service: "data-service", timestamp: new Date().toISOString() };
  });

  // Stores
  app.get("/internal/stores", async () => {
    const stores = await storeRepo.listAll();
    return { stores };
  });

  app.get("/internal/stores/:storeId", async (req: any, reply) => {
    const store = await storeRepo.findByCode(req.params.storeId);
    if (!store) return reply.code(404).send({ error: "Store not found" });
    return store;
  });

  app.get("/internal/stores/:storeId/zones", async (req: any) => {
    const zones = await zoneRepo.findByStoreId(req.params.storeId);
    return { zones };
  });

  // Devices
  app.post("/internal/devices/register", async (req: any) => {
    const body = req.body;
    const { device, isNew } = await deviceRepo.upsert({
      deviceId: body.deviceId,
      storeId: body.storeId,
      hardwareModel: body.hardwareModel,
      macAddress: body.macAddress,
      firmwareVersion: body.firmwareVersion,
      status: "PROVISIONED",
    });
    return {
      status: isNew ? "PROVISIONED" : "ALREADY_REGISTERED",
      device,
      mqttBrokerUrl: "tls://localhost:8883",
    };
  });

  app.get("/internal/devices/:deviceId", async (req: any, reply) => {
    const dev = await deviceRepo.findByDeviceId(req.params.deviceId);
    if (!dev) return reply.code(404).send({ error: "Device not found" });
    return dev;
  });

  app.post("/internal/devices/:deviceId/heartbeat", async (req: any) => {
    const timestamp = req.body?.timestamp ? new Date(req.body.timestamp) : new Date();
    const updated = await deviceRepo.updateHeartbeat(req.params.deviceId, timestamp);
    return { acknowledged: updated, timestamp: new Date().toISOString() };
  });

  // Events (with strict idempotency)
  // Response includes inline escalation results (alert, task) so the API
  // Gateway can broadcast SSE ALERT_TRIGGERED without a secondary HTTP call.
  app.post("/internal/events", async (req: any) => {
    const rawEvents = Array.isArray(req.body?.events)
      ? req.body.events
      : req.body?.eventId
      ? [req.body]
      : [];

    let acceptedCount = 0;
    let duplicateCount = 0;
    const results: any[] = [];
    const escalations: any[] = []; // [{eventId, alert, task}]

    for (const raw of rawEvents) {
      const { event, isDuplicate } = await eventRepo.insertOrGet(raw);
      if (isDuplicate) {
        duplicateCount++;
        results.push({ eventId: event.eventId, isDuplicate: true });
      } else {
        acceptedCount++;
        // Run the escalation engine — may create alert + task
        const escalationResult = await escalationEngine.processEvent(event);
        results.push({ eventId: event.eventId, isDuplicate: false });
        if (escalationResult.alert) {
          escalations.push({
            eventId: event.eventId,
            alert: escalationResult.alert,
            task: escalationResult.task || null,
          });
        }
      }
    }

    return {
      acceptedCount,
      duplicateCount,
      totalProcessed: rawEvents.length,
      results,
      escalations, // API Gateway uses this to broadcast ALERT_TRIGGERED via SSE
    };
  });

  app.get("/internal/events", async (req: any) => {
    const q = req.query || {};
    const events = await eventRepo.findMany({
      storeId: q.storeId || "store_001",
      zoneId: q.zoneId,
      eventType: q.eventType,
      severity: q.severity,
      limit: q.limit ? parseInt(q.limit, 10) : 50,
    });
    return { items: events, count: events.length };
  });

  app.get("/internal/events/:eventId", async (req: any, reply) => {
    const event = await eventRepo.findByEventId(req.params.eventId);
    if (!event) return reply.code(404).send({ error: "Event not found" });
    return event;
  });

  // Alerts
  app.get("/internal/alerts", async (req: any) => {
    const q = req.query || {};
    const alerts = await alertRepo.findActive(q.storeId || "store_001", q.status);
    return { alerts };
  });

  app.post("/internal/alerts/:alertId/acknowledge", async (req: any, reply) => {
    const userId = req.body?.userId || "usr_staff_default";
    const alert = await alertRepo.acknowledge(req.params.alertId, userId);
    if (!alert) return reply.code(404).send({ error: "Alert not found" });
    return alert;
  });

  // Tasks
  app.get("/internal/tasks", async (req: any) => {
    const q = req.query || {};
    const tasks = await taskRepo.findMany({
      storeId: q.storeId || "store_001",
      status: q.status,
      assignedUserId: q.assignedUserId,
    });
    return { tasks };
  });

  app.post("/internal/tasks", async (req: any) => {
    const body = req.body;
    const task = await taskRepo.create({
      taskCode: body.taskCode || `tsk_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      storeId: body.storeId || "store_001",
      zoneId: body.zoneId,
      alertId: body.alertId,
      title: body.title,
      description: body.description,
      priority: body.priority || "MEDIUM",
      status: body.status || "DETECTED",
    });
    return task;
  });

  app.post("/internal/tasks/:taskId/assign", async (req: any, reply) => {
    const userId = req.body?.assignedUserId || "usr_staff_102";
    const task = await taskRepo.assign(req.params.taskId, userId);
    if (!task) return reply.code(404).send({ error: "Task not found" });
    return task;
  });

  app.post("/internal/tasks/:taskId/complete", async (req: any, reply) => {
    const notes = req.body?.resolutionNotes || "";
    const task = await taskRepo.complete(req.params.taskId, notes);
    if (!task) return reply.code(404).send({ error: "Task not found" });
    return task;
  });

  // Analytics
  app.get("/internal/analytics/overview", async (req: any) => {
    const storeId = req.query?.storeId || "store_001";
    const summary = await metricRepo.getSummary(storeId);
    return summary;
  });

  app.get("/internal/analytics/traffic", async (request: any, reply) => {
    const { storeId, interval } = request.query as any;
    const series = await analyticsRepo.getTrafficSeries(storeId, interval || "hour");
    return { storeId, interval, series };
  });

  app.get("/internal/analytics/queues", async (request: any, reply) => {
    const { storeId } = request.query as any;
    const activeQueues = await alertRepo.findActive(storeId || "store_001", "ACTIVE");
    const queueAlerts = activeQueues.filter(a => a.alertType === "QUEUE_HIGH");
    
    return {
      storeId,
      activeRegisters: 4,
      zones: [
        {
          zoneId: "zone-checkout",
          currentQueueLength: queueAlerts.length > 0 ? 5 : 1,
          averageWaitSeconds: queueAlerts.length > 0 ? 135 : 45,
          status: queueAlerts.length > 0 ? "CONGESTED" : "NORMAL",
        },
      ],
    };
  });

  app.get("/internal/analytics/dwell", async (request: any, reply) => {
    const { storeId } = request.query as any;
    const zones = await analyticsRepo.getZoneDwellAggregates(storeId || "store_001");
    return { storeId, zones };
  });

  app.get("/internal/analytics/shelves", async (request: any, reply) => {
    const { storeId } = request.query as any;
    const alerts = await alertRepo.findActive(storeId || "store_001", "ACTIVE");
    const lowStock = alerts.filter(a => a.alertType === "SHELF_LOW_STOCK").length;
    const empty = alerts.filter(a => a.alertType === "SHELF_EMPTY").length;
    
    return {
      storeId,
      totalShelfZones: 6,
      lowStockZones: lowStock,
      emptyZones: empty,
      incidentsToday: lowStock + empty,
      zones: [
        {
          zoneId: "zone-aisle-01",
          shelfStatus: lowStock > 0 ? "LOW_STOCK" : "NORMAL",
          stockPercentage: lowStock > 0 ? 18 : 85,
        },
      ],
    };
  });

  app.post("/internal/metrics", async (request: any, reply) => {
    return { status: "accepted" };
  });

  app.get("/internal/metrics", async (request: any, reply) => {
    const { storeId, metricType, limit } = request.query as any;
    return { storeId, metricType, metrics: [] };
  });

  return app;
}

if (require.main === module) {
  const server = buildServer();
  server.listen({ port: config.port, host: config.host }, (err, address) => {
    if (err) {
      console.error("Failed to start data service:", err);
      process.exit(1);
    }
    console.log(`TypeScript Data Service listening at ${address}`);
  });
}

import { TaskRepository } from "../src/repositories/task.repository";

describe("TaskRepository Lifecycle Transitions", () => {
  let taskRepo: TaskRepository;

  beforeEach(() => {
    taskRepo = new TaskRepository();
  });

  it("should transition task through DETECTED -> ASSIGNED -> COMPLETED states", async () => {
    // 1. Creation (DETECTED)
    const task = await taskRepo.create({
      taskCode: "tsk_01J_LIFE_001",
      storeId: "store_001",
      zoneId: "zone-aisle-01",
      title: "Restock Beverage Shelf",
      priority: "HIGH",
      status: "DETECTED",
    });

    expect(task.status).toBe("DETECTED");
    expect(task.assignedToUserId).toBeUndefined();

    // 2. Assignment (ASSIGNED)
    const assigned = await taskRepo.assign("tsk_01J_LIFE_001", "usr_staff_102");
    expect(assigned).toBeDefined();
    expect(assigned?.status).toBe("ASSIGNED");
    expect(assigned?.assignedToUserId).toBe("usr_staff_102");
    expect(assigned?.assignedAt).toBeDefined();

    // 3. Completion (COMPLETED)
    const completed = await taskRepo.complete("tsk_01J_LIFE_001", "Restocked 18 units from backroom inventory.");
    expect(completed).toBeDefined();
    expect(completed?.status).toBe("COMPLETED");
    expect(completed?.completedAt).toBeDefined();
    expect(completed?.resolutionNotes).toContain("Restocked 18 units");
  });
});

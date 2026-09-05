import { TaskDTO } from "../types";
import { getPrismaClient } from "../prisma/client";

export class TaskRepository {
  private inMemoryTasks = new Map<string, TaskDTO>();

  async create(task: TaskDTO): Promise<TaskDTO> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const row = await prisma.task.create({
          data: {
            taskCode: task.taskCode,
            storeId: task.storeId,
            zoneId: task.zoneId || null,
            alertId: task.alertId || null,
            title: task.title,
            description: task.description || null,
            priority: task.priority || "MEDIUM",
            status: task.status || "DETECTED",
          },
        });
        const dto = this.mapToDTO(row);
        this.inMemoryTasks.set(dto.taskCode, dto);
        return dto;
      } catch (e) {}
    }

    const dto: TaskDTO = {
      ...task,
      id: task.id || `tsk_db_${Date.now()}`,
      status: task.status || "DETECTED",
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this.inMemoryTasks.set(dto.taskCode, dto);
    return dto;
  }

  async findMany(filters: {
    storeId: string;
    status?: string;
    assignedUserId?: string;
  }): Promise<TaskDTO[]> {
    const prisma = getPrismaClient();
    if (prisma) {
      try {
        const where: any = { storeId: filters.storeId };
        if (filters.status) where.status = filters.status;
        if (filters.assignedUserId) where.assignedToUserId = filters.assignedUserId;

        const rows = await prisma.task.findMany({
          where,
          orderBy: { createdAt: "desc" },
        });
        return rows.map(this.mapToDTO);
      } catch (e) {}
    }

    let list = Array.from(this.inMemoryTasks.values()).filter((t) => t.storeId === filters.storeId);
    if (filters.status) list = list.filter((t) => t.status === filters.status);
    if (filters.assignedUserId) list = list.filter((t) => t.assignedToUserId === filters.assignedUserId);
    return list.sort((a, b) => (b.createdAt?.getTime() || 0) - (a.createdAt?.getTime() || 0));
  }

  async assign(taskCodeOrId: string, userId: string): Promise<TaskDTO | null> {
    const prisma = getPrismaClient();
    const now = new Date();

    if (prisma) {
      try {
        const updated = await prisma.task.update({
          where: taskCodeOrId.startsWith("tsk_")
            ? { taskCode: taskCodeOrId }
            : { id: taskCodeOrId },
          data: {
            assignedToUserId: userId,
            assignedAt: now,
            status: "ASSIGNED",
          },
        });
        return this.mapToDTO(updated);
      } catch (e) {}
    }

    let target: TaskDTO | undefined;
    for (const t of this.inMemoryTasks.values()) {
      if (t.taskCode === taskCodeOrId || t.id === taskCodeOrId) {
        target = t;
        break;
      }
    }

    if (target) {
      target.assignedToUserId = userId;
      target.assignedAt = now;
      target.status = "ASSIGNED";
      target.updatedAt = now;
      return target;
    }
    return null;
  }

  async complete(taskCodeOrId: string, notes?: string): Promise<TaskDTO | null> {
    const prisma = getPrismaClient();
    const now = new Date();

    if (prisma) {
      try {
        const updated = await prisma.task.update({
          where: taskCodeOrId.startsWith("tsk_")
            ? { taskCode: taskCodeOrId }
            : { id: taskCodeOrId },
          data: {
            status: "COMPLETED",
            completedAt: now,
            resolutionNotes: notes || null,
          },
        });
        return this.mapToDTO(updated);
      } catch (e) {}
    }

    let target: TaskDTO | undefined;
    for (const t of this.inMemoryTasks.values()) {
      if (t.taskCode === taskCodeOrId || t.id === taskCodeOrId) {
        target = t;
        break;
      }
    }

    if (target) {
      target.status = "COMPLETED";
      target.completedAt = now;
      target.resolutionNotes = notes;
      target.updatedAt = now;
      return target;
    }
    return null;
  }

  private mapToDTO(row: any): TaskDTO {
    return {
      id: row.id,
      taskCode: row.taskCode,
      storeId: row.storeId,
      zoneId: row.zoneId || undefined,
      alertId: row.alertId || undefined,
      title: row.title,
      description: row.description || undefined,
      priority: row.priority,
      status: row.status,
      assignedToUserId: row.assignedToUserId || undefined,
      assignedAt: row.assignedAt || undefined,
      completedAt: row.completedAt || undefined,
      resolutionNotes: row.resolutionNotes || undefined,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    };
  }
}

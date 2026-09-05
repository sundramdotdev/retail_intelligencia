'use client';

import React from 'react';
import type { Task } from '@/lib/types';
import { taskStatusLabel, priorityColor, timeAgo } from '@/lib/utils';

interface TaskCardProps {
  task: Task;
  onAssign?: (taskId: string) => void;
  onStart?: (taskId: string) => void;
  onComplete?: (taskId: string) => void;
  userRole?: string;
}

export function TaskCard({ task, onAssign, onStart, onComplete, userRole }: TaskCardProps) {
  const taskId = task.id || task.taskCode || '';
  const isManager = userRole === 'STORE_MANAGER' || userRole === 'PLATFORM_ADMIN';
  const isStaff = userRole === 'STORE_STAFF';

  return (
    <div className="surface p-4 space-y-3" style={{ animation: 'fade-in 0.3s ease-out' }}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
            {task.title}
          </h4>
          {task.zoneId && (
            <p className="text-xs font-mono mt-1" style={{ color: 'var(--text-secondary)' }}>
              {task.zoneId}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span
            className="text-xs font-mono font-medium px-2 py-0.5 rounded"
            style={{
              color: priorityColor(task.priority),
              backgroundColor: 'var(--bg-elevated)',
              border: `1px solid ${priorityColor(task.priority)}33`,
            }}
          >
            {task.priority}
          </span>
        </div>
      </div>

      {task.description && (
        <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          {task.description}
        </p>
      )}

      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-3">
          <span
            className="text-xs font-mono px-2 py-0.5 rounded"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              color: task.status === 'COMPLETED' ? 'var(--status-online)' : 'var(--text-secondary)',
            }}
          >
            {taskStatusLabel(task.status)}
          </span>
          {task.assignedTo && (
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
              {task.assignedTo.name || task.assignedToUserId}
            </span>
          )}
        </div>
        <span className="text-xs font-mono" style={{ color: 'var(--text-tertiary)' }}>
          {timeAgo(task.createdAt)}
        </span>
      </div>

      {/* Actions based on status and role */}
      <div className="flex items-center gap-2 pt-1">
        {task.status === 'DETECTED' && isManager && onAssign && (
          <button onClick={() => onAssign(taskId)} className="btn-secondary text-xs">
            Assign
          </button>
        )}
        {(task.status === 'DETECTED' || task.status === 'ASSIGNED') && onStart && (
          <button onClick={() => onStart(taskId)} className="btn-secondary text-xs">
            Start
          </button>
        )}
        {(task.status === 'ASSIGNED' || task.status === 'IN_PROGRESS') && onComplete && (
          <button onClick={() => onComplete(taskId)} className="btn-primary text-xs">
            Complete
          </button>
        )}
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { TaskCard } from '@/components/dashboard/task-card';
import { useTasks } from '@/hooks/use-tasks';
import { useAuth } from '@/lib/auth';
import { apiClient } from '@/lib/api-client';
import { useQueryClient } from '@tanstack/react-query';

const statusFilters = ['ALL', 'DETECTED', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED'] as const;

export default function TasksPage() {
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const { session } = useAuth();
  const queryClient = useQueryClient();

  const { data: tasks, isLoading, isError } = useTasks(
    undefined,
    statusFilter === 'ALL' ? undefined : statusFilter,
  );

  const handleAssign = async (taskId: string) => {
    try {
      await apiClient.assignTask(taskId, 'usr_staff_102');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    } catch (err) {
      console.error('Failed to assign task:', err);
    }
  };

  const handleStart = async (taskId: string) => {
    // For now, assign-to-self starts the task
    try {
      await apiClient.assignTask(taskId, session?.user.userId || 'usr_staff_102');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    } catch (err) {
      console.error('Failed to start task:', err);
    }
  };

  const handleComplete = async (taskId: string) => {
    try {
      await apiClient.completeTask(taskId, 'Task completed.');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    } catch (err) {
      console.error('Failed to complete task:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
          Tasks
        </h1>
        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
          Staff action queue · Detect → Assign → Resolve
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        {statusFilters.map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={statusFilter === status ? 'btn-primary' : 'btn-ghost'}
            style={{ fontSize: '12px' }}
          >
            {status === 'ALL' ? 'All' : status === 'IN_PROGRESS' ? 'In Progress' : status.charAt(0) + status.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Task List */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="surface p-4 space-y-3">
              <div className="skeleton h-4 w-48" />
              <div className="skeleton h-3 w-32" />
              <div className="skeleton h-3 w-24" />
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="surface p-6 text-center">
          <p className="text-sm" style={{ color: 'var(--error)' }}>Unable to load tasks</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>Check API connection and try again.</p>
        </div>
      ) : tasks?.length ? (
        <div className="space-y-3">
          {tasks.map((task) => (
            <TaskCard
              key={task.id || task.taskCode}
              task={task}
              onAssign={handleAssign}
              onStart={handleStart}
              onComplete={handleComplete}
              userRole={session?.user.role}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state py-12">
          <h3>No {statusFilter === 'ALL' ? '' : statusFilter.toLowerCase().replace('_', ' ')} tasks</h3>
          <p>Tasks are created automatically from alerts or manually by store managers.</p>
        </div>
      )}
    </div>
  );
}

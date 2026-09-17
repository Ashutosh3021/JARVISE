"""
JARVIS Brain Layer - Task Planning & Goal Decomposition

Breaks complex goals into manageable sub-tasks with:
- Goal decomposition into ordered tasks
- Task dependency graph
- Status tracking (pending/in_progress/done/blocked/failed)
- Progress monitoring with percentage
- Adaptive re-planning
- Plan persistence to disk
"""

import json
import time
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """A single task in a plan."""
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    depends_on: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)
    result: str | None = None
    error: str | None = None
    estimated_minutes: int | None = None
    actual_minutes: float | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "depends_on": self.depends_on,
            "subtasks": self.subtasks,
            "result": self.result,
            "error": self.error,
            "estimated_minutes": self.estimated_minutes,
            "actual_minutes": self.actual_minutes,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", "medium")),
            depends_on=data.get("depends_on", []),
            subtasks=data.get("subtasks", []),
            result=data.get("result"),
            error=data.get("error"),
            estimated_minutes=data.get("estimated_minutes"),
            actual_minutes=data.get("actual_minutes"),
            created_at=data.get("created_at", time.time()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )

    @property
    def is_ready(self) -> bool:
        """Check if task can start (all dependencies done)."""
        return (
            self.status == TaskStatus.PENDING
            and len(self.depends_on) == 0
        )

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a final state."""
        return self.status in (
            TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.SKIPPED
        )


@dataclass
class Plan:
    """A complete plan with goal, tasks, and metadata."""
    id: str
    goal: str
    tasks: list[Task] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        plan = cls(
            id=data["id"],
            goal=data["goal"],
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            completed=data.get("completed", False),
        )
        for t in data.get("tasks", []):
            plan.tasks.append(Task.from_dict(t))
        return plan

    @property
    def progress(self) -> float:
        """Calculate progress percentage (0.0 - 1.0)."""
        if not self.tasks:
            return 1.0
        done = sum(1 for t in self.tasks if t.is_terminal and t.status == TaskStatus.DONE)
        return done / len(self.tasks)

    @property
    def blocked_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED)

    @property
    def failed_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

    def get_task(self, task_id: str) -> Task | None:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def get_next_tasks(self) -> list[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        done_ids = {
            t.id for t in self.tasks
            if t.status in (TaskStatus.DONE, TaskStatus.SKIPPED)
        }
        ready = []
        for t in self.tasks:
            if t.status == TaskStatus.PENDING:
                if all(dep in done_ids for dep in t.depends_on):
                    ready.append(t)
        return ready

    def get_ready_task(self) -> Task | None:
        """Get the highest-priority ready task."""
        ready = self.get_next_tasks()
        if not ready:
            return None
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }
        ready.sort(key=lambda t: priority_order.get(t.priority, 2))
        return ready[0]

    def format_status(self) -> str:
        """Format plan status as human-readable string."""
        lines = [f"Plan: {self.goal}"]
        lines.append(f"Progress: {self.progress:.0%} ({self.blocked_count} blocked, {self.failed_count} failed)")
        lines.append("")

        for t in self.tasks:
            icon = {
                TaskStatus.PENDING: "[ ]",
                TaskStatus.IN_PROGRESS: "[>]",
                TaskStatus.DONE: "[x]",
                TaskStatus.BLOCKED: "[!]",
                TaskStatus.FAILED: "[X]",
                TaskStatus.SKIPPED: "[-]",
            }.get(t.status, "[?]")

            deps = f" (needs: {', '.join(t.depends_on)})" if t.depends_on and t.status == TaskStatus.PENDING else ""
            result_note = f" -> {t.result[:50]}" if t.result else ""
            error_note = f" ERROR: {t.error[:50]}" if t.error else ""

            lines.append(f"  {icon} {t.id}: {t.title}{deps}{result_note}{error_note}")

        return "\n".join(lines)


class TaskPlanner:
    """
    Task planner that decomposes goals into executable task graphs.

    Features:
    - Goal decomposition into ordered tasks
    - Dependency resolution
    - Status tracking
    - Progress monitoring
    - Adaptive re-planning
    - Persistence
    """

    def __init__(self, storage_path: str = "./data/plans.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._plans: dict[str, Plan] = {}
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            for plan_data in data.get("plans", []):
                plan = Plan.from_dict(plan_data)
                self._plans[plan.id] = plan
        except Exception as e:
            logger.warning(f"Failed to load plans: {e}")

    def _save(self) -> None:
        try:
            data = {
                "plans": [p.to_dict() for p in self._plans.values()]
            }
            self.storage_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Failed to save plans: {e}")

    def create_plan(
        self,
        goal: str,
        tasks: list[dict[str, Any]],
        plan_id: str | None = None,
    ) -> Plan:
        """
        Create a new plan from a goal and task list.

        Args:
            goal: The high-level goal
            tasks: List of task dicts with id, title, description, depends_on, priority
            plan_id: Optional plan ID (auto-generated if None)

        Returns:
            Created Plan
        """
        if plan_id is None:
            plan_id = f"plan_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        plan = Plan(id=plan_id, goal=goal)

        for t in tasks:
            task = Task(
                id=t.get("id", f"t{len(plan.tasks)}"),
                title=t.get("title", "Untitled"),
                description=t.get("description", ""),
                priority=TaskPriority(t.get("priority", "medium")),
                depends_on=t.get("depends_on", []),
                estimated_minutes=t.get("estimated_minutes"),
            )
            plan.tasks.append(task)

        self._plans[plan_id] = plan
        self._save()
        logger.info(f"Created plan '{plan_id}' with {len(plan.tasks)} tasks")
        return plan

    def decompose_goal(self, goal: str, steps: list[dict[str, Any]]) -> Plan:
        """
        Decompose a goal into an ordered task graph.

        Args:
            goal: The high-level goal
            steps: Ordered steps with dependencies

        Returns:
            Created Plan
        """
        return self.create_plan(goal, steps)

    def start_task(self, plan_id: str, task_id: str) -> Task | None:
        """Mark a task as in-progress."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        task = plan.get_task(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = time.time()
            plan.updated_at = time.time()
            self._save()
            return task
        return None

    def complete_task(self, plan_id: str, task_id: str, result: str = "") -> Task | None:
        """Mark a task as done."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        task = plan.get_task(task_id)
        if task:
            task.status = TaskStatus.DONE
            task.result = result
            task.completed_at = time.time()
            if task.started_at:
                task.actual_minutes = round((time.time() - task.started_at) / 60, 1)
            plan.updated_at = time.time()

            # Unblock dependent tasks
            for t in plan.tasks:
                if task_id in t.depends_on and t.status == TaskStatus.BLOCKED:
                    remaining_deps = [d for d in t.depends_on if d != task_id]
                    still_blocked = any(
                        plan.get_task(d) and not plan.get_task(d).is_terminal
                        for d in remaining_deps
                    )
                    if not still_blocked:
                        t.status = TaskStatus.PENDING

            # Check if plan is complete
            plan.completed = all(t.is_terminal for t in plan.tasks)

            self._save()
            return task
        return None

    def fail_task(self, plan_id: str, task_id: str, error: str = "") -> Task | None:
        """Mark a task as failed."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        task = plan.get_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = time.time()
            plan.updated_at = time.time()

            # Block dependent tasks
            for t in plan.tasks:
                if task_id in t.depends_on and t.status == TaskStatus.PENDING:
                    t.status = TaskStatus.BLOCKED
                    t.error = f"Blocked by failed task: {task_id}"

            self._save()
            return task
        return None

    def skip_task(self, plan_id: str, task_id: str) -> Task | None:
        """Skip a task."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        task = plan.get_task(task_id)
        if task:
            task.status = TaskStatus.SKIPPED
            task.completed_at = time.time()
            plan.updated_at = time.time()
            self._save()
            return task
        return None

    def replan(self, plan_id: str, new_tasks: list[dict[str, Any]]) -> Plan | None:
        """
        Add new tasks to an existing plan (adaptive re-planning).

        Args:
            plan_id: Plan to modify
            new_tasks: New tasks to add

        Returns:
            Updated plan or None
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        existing_ids = {t.id for t in plan.tasks}
        for t in new_tasks:
            if t.get("id") not in existing_ids:
                task = Task(
                    id=t.get("id", f"t{len(plan.tasks)}"),
                    title=t.get("title", "Untitled"),
                    description=t.get("description", ""),
                    priority=TaskPriority(t.get("priority", "medium")),
                    depends_on=t.get("depends_on", []),
                    estimated_minutes=t.get("estimated_minutes"),
                )
                plan.tasks.append(task)

        plan.updated_at = time.time()
        self._save()
        return plan

    def get_plan(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def list_plans(self) -> list[dict]:
        """List all plans with summary info."""
        return [
            {
                "id": p.id,
                "goal": p.goal,
                "progress": f"{p.progress:.0%}",
                "tasks": len(p.tasks),
                "completed": p.completed,
            }
            for p in self._plans.values()
        ]

    def delete_plan(self, plan_id: str) -> bool:
        if plan_id in self._plans:
            del self._plans[plan_id]
            self._save()
            return True
        return False

    def get_stats(self) -> dict[str, Any]:
        total_tasks = sum(len(p.tasks) for p in self._plans.values())
        completed = sum(
            sum(1 for t in p.tasks if t.status == TaskStatus.DONE)
            for p in self._plans.values()
        )
        return {
            "total_plans": len(self._plans),
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "active_plans": sum(1 for p in self._plans.values() if not p.completed),
        }


__all__ = ["TaskPlanner", "Plan", "Task", "TaskStatus", "TaskPriority"]

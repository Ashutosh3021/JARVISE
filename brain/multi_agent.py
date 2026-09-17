"""
JARVIS Brain Layer - Multi-Agent Collaboration

Orchestrates multiple specialized agents working together:
- Spawn sub-agents with specific roles
- Execute tasks in parallel or sequential
- Track token/time budgets per agent
- Aggregate results from all agents
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from loguru import logger

from brain.providers.base import LLMProvider
from brain.prompt_builder import PromptBuilder


class AgentRole(Enum):
    """Specialized agent roles."""
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    PLANNER = "planner"
    GENERAL = "general"


ROLE_SYSTEM_PROMPTS = {
    AgentRole.RESEARCHER: (
        "You are a research specialist. Your job is to gather information, "
        "search the web, extract relevant data, and provide well-sourced findings. "
        "Always cite your sources. Be thorough but concise."
    ),
    AgentRole.CODER: (
        "You are a coding specialist. Your job is to write clean, efficient code. "
        "Follow best practices, handle errors properly, and include comments "
        "for complex logic. Output only the code with brief explanations."
    ),
    AgentRole.REVIEWER: (
        "You are a code reviewer. Your job is to review code for bugs, security "
        "issues, performance problems, and style violations. Be constructive "
        "but thorough. Rate severity: critical/major/minor."
    ),
    AgentRole.PLANNER: (
        "You are a project planner. Your job is to break down complex tasks into "
        "clear, ordered steps. Consider dependencies, risks, and estimates. "
        "Output a structured plan with actionable items."
    ),
    AgentRole.GENERAL: (
        "You are a helpful assistant. Complete the task as instructed. "
        "Be accurate, thorough, and concise."
    ),
}


@dataclass
class AgentTask:
    """A task assigned to a sub-agent."""
    id: str
    description: str
    role: AgentRole
    prompt: str
    timeout_seconds: int = 60
    max_tokens: int = 2000


@dataclass
class AgentResult:
    """Result from a sub-agent execution."""
    task_id: str
    role: AgentRole
    output: str
    duration_ms: float
    tokens_used: int
    success: bool
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "role": self.role.value,
            "output": self.output[:1000],
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class AgentBudget:
    """Budget limits for an agent."""
    max_tokens: int = 5000
    max_time_seconds: int = 120
    tokens_used: int = 0
    time_started: float = 0.0

    def can_continue(self) -> bool:
        if self.tokens_used >= self.max_tokens:
            return False
        if self.time_started > 0:
            elapsed = time.time() - self.time_started
            if elapsed >= self.max_time_seconds:
                return False
        return True

    def record_tokens(self, count: int) -> None:
        self.tokens_used += count


class SubAgent:
    """
    A specialized sub-agent that executes a single task.

    Wraps an LLM provider with a role-specific system prompt
    and budget tracking.
    """

    def __init__(
        self,
        role: AgentRole,
        llm_client: LLMProvider,
        budget: AgentBudget | None = None,
    ):
        self.role = role
        self.llm = llm_client
        self.budget = budget or AgentBudget()
        self.prompt_builder = PromptBuilder(
            system_prompt=ROLE_SYSTEM_PROMPTS.get(role, ROLE_SYSTEM_PROMPTS[AgentRole.GENERAL])
        )

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute a task and return the result.

        Args:
            task: The task to execute

        Returns:
            AgentResult with output and metadata
        """
        start = time.time()
        self.budget.time_started = start

        try:
            messages = self.prompt_builder.build(
                user_input={"role": "user", "content": task.prompt}
            )

            response = self.llm.chat(messages)
            content = response.get("message", {}).get("content", "")

            # Estimate tokens (rough: 1 token ~= 4 chars)
            tokens = len(content) // 4
            self.budget.record_tokens(tokens)

            duration = (time.time() - start) * 1000

            return AgentResult(
                task_id=task.id,
                role=self.role,
                output=content,
                duration_ms=round(duration, 1),
                tokens_used=tokens,
                success=True,
            )

        except Exception as e:
            duration = (time.time() - start) * 1000
            return AgentResult(
                task_id=task.id,
                role=self.role,
                output="",
                duration_ms=round(duration, 1),
                tokens_used=0,
                success=False,
                error=str(e),
            )


class MultiAgentOrchestrator:
    """
    Orchestrates multiple sub-agents for parallel task execution.

    Usage:
        orchestrator = MultiAgentOrchestrator(llm_client=provider)

        # Define tasks
        tasks = [
            AgentTask(id="t1", description="Research", role=AgentRole.RESEARCHER, prompt="Research X"),
            AgentTask(id="t2", description="Code", role=AgentRole.CODER, prompt="Write code for Y"),
        ]

        # Execute in parallel
        results = orchestrator.run_parallel(tasks)

        # Or sequential
        results = orchestrator.run_sequential(tasks)
    """

    def __init__(
        self,
        llm_client: LLMProvider | None = None,
        max_workers: int = 3,
    ):
        """
        Args:
            llm_client: LLM provider for all sub-agents
            max_workers: Max parallel agents
        """
        self.llm_client = llm_client
        self.max_workers = max_workers
        self._results: list[AgentResult] = []

    def run_parallel(
        self,
        tasks: list[AgentTask],
        on_complete: Callable[[AgentResult], None] | None = None,
    ) -> list[AgentResult]:
        """
        Execute tasks in parallel using thread pool.

        Args:
            tasks: List of tasks to execute
            on_complete: Optional callback when each task completes

        Returns:
            List of results from all agents
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for task in tasks:
                agent = SubAgent(
                    role=task.role,
                    llm_client=self.llm_client,
                    budget=AgentBudget(max_tokens=task.max_tokens, max_time_seconds=task.timeout_seconds),
                )
                future = executor.submit(agent.execute, task)
                futures[future] = task

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result(timeout=task.timeout_seconds + 5)
                    results.append(result)
                    if on_complete:
                        on_complete(result)
                    logger.info(
                        f"Agent [{task.role.value}] completed: "
                        f"{result.duration_ms:.0f}ms, {result.tokens_used} tokens"
                    )
                except Exception as e:
                    results.append(AgentResult(
                        task_id=task.id,
                        role=task.role,
                        output="",
                        duration_ms=0,
                        tokens_used=0,
                        success=False,
                        error=str(e),
                    ))

        self._results.extend(results)
        return results

    def run_sequential(self, tasks: list[AgentTask]) -> list[AgentResult]:
        """
        Execute tasks sequentially, passing context between them.

        Args:
            tasks: Ordered list of tasks

        Returns:
            List of results
        """
        results = []
        context = ""

        for task in tasks:
            # Inject previous results as context
            if context:
                task_copy = AgentTask(
                    id=task.id,
                    description=task.description,
                    role=task.role,
                    prompt=f"Previous context:\n{context[:2000]}\n\nYour task:\n{task.prompt}",
                    timeout_seconds=task.timeout_seconds,
                    max_tokens=task.max_tokens,
                )
            else:
                task_copy = task

            agent = SubAgent(
                role=task.role,
                llm_client=self.llm_client,
                budget=AgentBudget(max_tokens=task.max_tokens, max_time_seconds=task.timeout_seconds),
            )
            result = agent.execute(task_copy)
            results.append(result)

            if result.success:
                context += f"\n--- {task.description} ---\n{result.output[:1000]}\n"

        self._results.extend(results)
        return results

    def run_pipeline(
        self,
        research_task: AgentTask | None = None,
        plan_task: AgentTask | None = None,
        code_task: AgentTask | None = None,
        review_task: AgentTask | None = None,
    ) -> list[AgentResult]:
        """
        Run a full development pipeline: research → plan → code → review.

        Each stage is optional. Results from earlier stages feed into later ones.

        Returns:
            List of results from each stage
        """
        tasks = []
        if research_task:
            tasks.append(research_task)
        if plan_task:
            tasks.append(plan_task)
        if code_task:
            tasks.append(code_task)
        if review_task:
            tasks.append(review_task)

        if not tasks:
            return []

        return self.run_sequential(tasks)

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about all executed agents."""
        total_tokens = sum(r.tokens_used for r in self._results)
        total_time = sum(r.duration_ms for r in self._results)
        successful = sum(1 for r in self._results if r.success)

        by_role = {}
        for r in self._results:
            role = r.role.value
            if role not in by_role:
                by_role[role] = {"count": 0, "tokens": 0, "time_ms": 0}
            by_role[role]["count"] += 1
            by_role[role]["tokens"] += r.tokens_used
            by_role[role]["time_ms"] += r.duration_ms

        return {
            "total_tasks": len(self._results),
            "successful": successful,
            "failed": len(self._results) - successful,
            "total_tokens": total_tokens,
            "total_time_ms": round(total_time, 1),
            "by_role": by_role,
        }

    def clear_history(self) -> None:
        """Clear execution history."""
        self._results.clear()


__all__ = [
    "MultiAgentOrchestrator",
    "SubAgent",
    "AgentRole",
    "AgentTask",
    "AgentResult",
    "AgentBudget",
    "ROLE_SYSTEM_PROMPTS",
]

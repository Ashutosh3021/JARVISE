"""
JARVIS Brain Layer - Task Chains Module

Implements multi-step workflows with up to 5 steps.
Each step's output feeds into the next step.
"""

import uuid
import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any

from loguru import logger


class ChainStatus(Enum):
    """Status of a chain or chain step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class ChainStep:
    """Represents a single step in a task chain."""
    step_number: int
    action: str  # Tool name or LLM request
    input: str  # From previous step or user
    output: str | None = None
    status: ChainStatus = ChainStatus.PENDING
    error: str | None = None
    duration_ms: int = 0


@dataclass
class ChainResult:
    """Result of executing a full task chain."""
    chain_id: str
    steps: list[ChainStep]
    status: ChainStatus
    total_duration_ms: int
    final_output: str

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "chain_id": self.chain_id,
            "status": self.status.value,
            "steps": [
                {
                    "step_number": s.step_number,
                    "action": s.action,
                    "input": s.input,
                    "output": s.output,
                    "status": s.status.value,
                    "error": s.error,
                    "duration_ms": s.duration_ms,
                }
                for s in self.steps
            ],
            "total_duration_ms": self.total_duration_ms,
            "final_output": self.final_output,
        }


# Type alias for progress callback
ProgressCallback = Callable[[dict[str, Any]], None]


class TaskChain:
    """
    Task Chain execution engine.
    
    Enables JARVIS to execute sequences like "search web → scrape pages → 
    summarize → save notes". Each step's output feeds into the next.
    
    Maximum 5 steps per chain.
    """
    
    # Built-in chain templates
    BUILTIN_TEMPLATES = {
        "research_and_summarize": [
            {"action": "web_search", "input": "{query}"},
            {"action": "browser", "action_type": "extract_content"},
            {"action": "llm_summarize", "input": "{content}"},
            {"action": "filesystem", "action": "save", "content": "{summary}"},
        ],
        "code_review": [
            {"action": "filesystem", "action": "list_files"},
            {"action": "filesystem", "action": "read_code"},
            {"action": "llm_review", "input": "{code}"},
            {"action": "filesystem", "action": "create_review_file"},
        ],
        "find_and_replace": [
            {"action": "filesystem", "action": "search_files"},
            {"action": "filesystem", "action": "read_files"},
            {"action": "llm_replace", "input": "{content}"},
            {"action": "filesystem", "action": "save_files"},
        ],
    }
    
    MAX_STEPS = 5
    
    def __init__(
        self,
        agent=None,
        tool_registry=None,
        max_steps: int = MAX_STEPS,
        progress_callback: ProgressCallback | None = None,
    ):
        """
        Initialize the TaskChain.
        
        Args:
            agent: ReActAgent instance for LLM interactions
            tool_registry: ToolRegistry for tool execution
            max_steps: Maximum number of steps (default: 5)
            progress_callback: Optional callback for progress updates
        """
        from brain.agent import ReActAgent
        from brain.tools import ToolRegistry
        
        self.agent = agent or ReActAgent()
        self.tool_registry = tool_registry or ToolRegistry()
        self.max_steps = min(max_steps, self.MAX_STEPS)
        self.progress_callback = progress_callback
        self._is_interrupted = False
        
        # Chain history (last 20 chains)
        self._chain_history: list[ChainResult] = []
        self._max_history = 20
        
        # Custom templates
        self._custom_templates: dict[str, list[dict]] = {}
    
    def list_templates(self) -> dict[str, list[dict]]:
        """List all available chain templates."""
        all_templates = {**self.BUILTIN_TEMPLATES, **self._custom_templates}
        return all_templates
    
    def get_template(self, name: str) -> list[dict] | None:
        """Get a specific template by name."""
        templates = self.list_templates()
        return templates.get(name)
    
    def add_template(self, name: str, steps: list[dict]) -> None:
        """
        Add a custom chain template.
        
        Args:
            name: Template name
            steps: List of step definitions
        """
        if len(steps) > self.MAX_STEPS:
            raise ValueError(f"Template cannot exceed {self.MAX_STEPS} steps")
        
        self._custom_templates[name] = steps
        logger.info(f"Added custom chain template: {name}")
    
    def parse_chain_request(self, user_input: str) -> list[ChainStep]:
        """
        Parse user input into a list of chain steps using LLM.
        
        Args:
            user_input: User's chain request
            
        Returns:
            List of ChainStep objects
            
        Raises:
            ValueError: If request exceeds max steps
        """
        # Use LLM to break down the request
        prompt = f"""Parse this user request into a sequence of steps for execution.
Maximum {self.MAX_STEPS} steps allowed.

User request: {user_input}

Respond with a JSON array of steps, each with:
- action: The tool name or action to perform
- input: What to pass as input

Available tools: {', '.join(self.tool_registry.list_tools().keys())}

Example response format:
[{{"action": "web_search", "input": "What to search for"}}, {{"action": "browser", "input": "URL to navigate to"}}]
"""
        
        try:
            response = self.agent.run(prompt)
            # Parse the LLM response to extract steps
            import json
            # Try to extract JSON from response
            if "[" in response:
                start = response.find("[")
                end = response.rfind("]") + 1
                if start >= 0 and end > start:
                    steps_data = json.loads(response[start:end])
                else:
                    steps_data = []
            else:
                steps_data = []
            
            # Validate step count
            if len(steps_data) > self.MAX_STEPS:
                raise ValueError(f"Request has {len(steps_data)} steps, maximum is {self.MAX_STEPS}")
            
            # Convert to ChainStep objects
            chain_steps = []
            for i, step_data in enumerate(steps_data):
                chain_steps.append(ChainStep(
                    step_number=i + 1,
                    action=step_data.get("action", ""),
                    input=step_data.get("input", ""),
                ))
            
            return chain_steps
            
        except Exception as e:
            logger.error(f"Failed to parse chain request: {e}")
            # Fallback: create a simple single-step chain
            return [ChainStep(
                step_number=1,
                action="llm_process",
                input=user_input,
            )]
    
    def interrupt(self) -> None:
        """Interrupt chain execution at the next step boundary."""
        self._is_interrupted = True
        logger.info("Chain execution interrupted")
    
    def _reset_interrupt(self) -> None:
        """Reset interrupt flag."""
        self._is_interrupted = False
    
    def _emit_progress(self, signal: str, data: dict[str, Any]) -> None:
        """Emit progress update."""
        if self.progress_callback:
            self.progress_callback({
                "signal": signal,
                **data,
            })
    
    async def execute_chain_async(
        self,
        steps: list[dict] | list[ChainStep],
        progress_callback: ProgressCallback | None = None,
    ) -> ChainResult:
        """
        Execute a chain asynchronously with progress streaming.
        
        Args:
            steps: List of step definitions or ChainStep objects
            progress_callback: Optional callback for progress updates
            
        Returns:
            ChainResult with execution details
        """
        chain_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()
        
        # Convert dict steps to ChainStep objects
        chain_steps: list[ChainStep]
        if isinstance(steps[0], dict):
            chain_steps = [
                ChainStep(
                    step_number=i + 1,
                    action=step.get("action", ""),
                    input=step.get("input", ""),
                )
                for i, step in enumerate(steps)
            ]
        else:
            chain_steps = steps
        
        # Validate step count
        if len(chain_steps) > self.MAX_STEPS:
            return ChainResult(
                chain_id=chain_id,
                steps=chain_steps,
                status=ChainStatus.FAILED,
                total_duration_ms=0,
                final_output=f"Error: Chain exceeds maximum of {self.MAX_STEPS} steps",
            )
        
        # Use callback
        callback = progress_callback or self.progress_callback
        self._reset_interrupt()
        
        # Execute each step
        previous_output = ""
        final_output = ""
        
        for i, step in enumerate(chain_steps):
            # Check for interruption
            if self._is_interrupted:
                step.status = ChainStatus.INTERRUPTED
                step.error = "Chain interrupted by user"
                break
            
            # Emit step start
            if callback:
                callback({
                    "signal": "step_start",
                    "step_number": step.step_number,
                    "action": step.action,
                })
            
            step.status = ChainStatus.RUNNING
            step_start = time.perf_counter()
            
            try:
                # Execute the step
                if hasattr(self.tool_registry, 'execute'):
                    # Pass previous output as input if not provided
                    input_to_use = step.input if step.input else previous_output
                    result = self.tool_registry.execute(step.action, {"input": input_to_use})
                    step.output = str(result)
                else:
                    step.output = f"Tool registry not available"
                
                step.status = ChainStatus.COMPLETED
                step.duration_ms = int((time.perf_counter() - step_start) * 1000)
                previous_output = step.output
                final_output = step.output
                
                # Emit step complete
                if callback:
                    callback({
                        "signal": "step_complete",
                        "step_number": step.step_number,
                        "output": step.output,
                        "duration_ms": step.duration_ms,
                    })
                    
            except Exception as e:
                step.status = ChainStatus.FAILED
                step.error = str(e)
                step.duration_ms = int((time.perf_counter() - step_start) * 1000)
                
                # Emit step error
                if callback:
                    callback({
                        "signal": "step_error",
                        "step_number": step.step_number,
                        "error": str(e),
                    })
                
                # Don't continue on error
                break
        
        # Determine overall status
        if self._is_interrupted:
            overall_status = ChainStatus.INTERRUPTED
        elif any(s.status == ChainStatus.FAILED for s in chain_steps):
            overall_status = ChainStatus.FAILED
        else:
            overall_status = ChainStatus.COMPLETED
        
        total_duration = int((time.perf_counter() - start_time) * 1000)
        
        result = ChainResult(
            chain_id=chain_id,
            steps=chain_steps,
            status=overall_status,
            total_duration_ms=total_duration,
            final_output=final_output,
        )
        
        # Store in history
        self._add_to_history(result)
        
        # Emit chain complete
        if callback:
            callback({
                "signal": "chain_complete",
                "final_output": final_output,
                "total_duration": total_duration,
                "status": overall_status.value,
            })
        
        return result
    
    def execute_chain(
        self,
        steps: list[dict] | list[ChainStep],
        progress_callback: ProgressCallback | None = None,
    ) -> ChainResult:
        """
        Execute a chain synchronously.
        
        Args:
            steps: List of step definitions or ChainStep objects
            progress_callback: Optional callback for progress updates
            
        Returns:
            ChainResult with execution details
        """
        return asyncio.run(self.execute_chain_async(steps, progress_callback))
    
    def _add_to_history(self, result: ChainResult) -> None:
        """Add result to chain history."""
        self._chain_history.append(result)
        if len(self._chain_history) > self._max_history:
            self._chain_history.pop(0)
    
    def get_history(self) -> list[dict]:
        """Get chain execution history."""
        return [r.to_dict() for r in self._chain_history]
    
    def get_chain(self, chain_id: str) -> ChainResult | None:
        """Get a specific chain result from history."""
        for chain in self._chain_history:
            if chain.chain_id == chain_id:
                return chain
        return None


# Factory function
def create_task_chain(
    agent=None,
    tool_registry=None,
    max_steps: int = 5,
) -> TaskChain:
    """Factory function to create a TaskChain instance."""
    return TaskChain(
        agent=agent,
        tool_registry=tool_registry,
        max_steps=max_steps,
    )


__all__ = [
    "TaskChain",
    "ChainStep",
    "ChainResult",
    "ChainStatus",
    "create_task_chain",
]

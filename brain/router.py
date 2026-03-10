"""
JARVIS Brain Layer - Smart Command Router

Routes user input to either direct tools (for fast execution) or LLM agent.
Simple commands like "open chrome", "what time is it" bypass the LLM for
speed and reliability.
"""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger


class RouteType(Enum):
    """Types of routing decisions."""
    DIRECT_TOOL = "direct_tool"  # Execute via tool directly
    LLM_AGENT = "llm_agent"     # Process through LLM
    CHAIN = "chain"              # Execute as multi-step chain
    UNKNOWN = "unknown"          # Unknown command, default to LLM


@dataclass
class RouterResult:
    """Result of routing a user input."""
    route_type: RouteType
    tool_name: str | None = None
    tool_args: dict | None = None
    chain_name: str | None = None
    chain_steps: list[dict] | None = None
    response: str | None = None
    confidence: float = 0.0
    execution_time_ms: float | None = None


@dataclass
class CommandStats:
    """Statistics for router performance tracking."""
    direct_tool_calls: int = 0
    llm_agent_calls: int = 0
    unknown_routes: int = 0
    total_execution_time_ms: float = 0.0
    last_reset: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    
    def get_direct_percentage(self) -> float:
        """Get percentage of calls routed to direct tools."""
        total = self.direct_tool_calls + self.llm_agent_calls + self.unknown_routes
        if total == 0:
            return 0.0
        return (self.direct_tool_calls / total) * 100
    
    def to_dict(self) -> dict:
        """Convert stats to dictionary for API responses."""
        return {
            "direct_tool_calls": self.direct_tool_calls,
            "llm_agent_calls": self.llm_agent_calls,
            "unknown_routes": self.unknown_routes,
            "direct_percentage": round(self.get_direct_percentage(), 1),
            "total_execution_time_ms": round(self.total_execution_time_ms, 2),
            "last_reset": self.last_reset,
        }


class CommandRouter:
    """
    Smart command router that directs input to tools or LLM.
    
    Simple commands (like "open chrome", "what time") execute directly without LLM,
    making JARVIS faster, cheaper, and more reliable.
    """
    
    def __init__(self, tool_registry=None, use_preferences: bool = True):
        """
        Initialize the command router.
        
        Args:
            tool_registry: ToolRegistry instance for executing tools
            use_preferences: Whether to use preference memory (default: True)
        """
        self.tool_registry = tool_registry
        self._direct_commands: dict[str, tuple[str, dict]] = {}
        self._learned_commands: dict[str, tuple[str, dict]] = {}
        self._stats = CommandStats()
        
        # Preference memory for learning
        self._use_preferences = use_preferences
        self._preference_memory = None
        
        if use_preferences:
            try:
                from learning import PreferenceMemory
                self._preference_memory = PreferenceMemory()
                logger.debug("Preference memory enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize preference memory: {e}")
        
        # Load built-in direct commands
        self._load_builtin_commands()
        self._load_chain_patterns()
    
    def _load_chain_patterns(self) -> None:
        """Load chain trigger patterns for multi-step workflows."""
        # Chain trigger patterns - these indicate multi-step workflows
        self._chain_patterns = [
            (r"research\s+(.+?)\s+and\s+summarize", "research_and_summarize"),
            (r"search\s+(.+?)\s+and\s+save", "search_and_save"),
            (r"find\s+(.+?)\s+and\s+replace", "find_and_replace"),
            (r"look\s+up\s+(.+?)\s+then\s+(.+)", None),  # Custom chain
            (r"do\s+(.+?),\s+then\s+(.+?),\s+then\s+(.+)", None),  # Custom chain
            (r"(.+?)\s+and\s+(.+?)\s+and\s+(.+)", None),  # 3+ step custom
        ]
        
        # Known chain template triggers
        self._template_triggers = {
            "research": "research_and_summarize",
            "research and summarize": "research_and_summarize",
            "find and replace": "find_and_replace",
            "find and replace in": "find_and_replace",
            "search and save": "search_and_save",
            "search and save to": "search_and_save",
        }
    
    def _detect_chain_request(self, normalized: str) -> tuple[str | None, list[dict] | None]:
        """
        Detect if input is a chain request.
        
        Returns:
            Tuple of (template_name, parsed_steps) or (None, None)
        """
        # Check template triggers
        for trigger, template in self._template_triggers.items():
            if trigger in normalized:
                return template, None
        
        # Check regex patterns
        import re
        for pattern, template_name in self._chain_patterns:
            match = re.search(pattern, normalized)
            if match:
                # Return template name or None for custom chains
                return template_name, None
        
        return None, None
    
    def _load_builtin_commands(self) -> None:
        """Load built-in direct command patterns."""
        builtin_patterns = {
            # "open *" patterns
            "open *": ("filesystem", {"action": "open", "path": "*"}),
            "open chrome": ("browser", {"action": "navigate", "url": "https://chrome.google.com"}),
            "open google chrome": ("browser", {"action": "navigate", "url": "https://chrome.google.com"}),
            "open vscode": ("browser", {"action": "vscode", "url": "vscode"}),
            "open code": ("browser", {"action": "vscode", "url": "vscode"}),
            "open notepad": ("filesystem", {"action": "open", "path": "notepad"}),
            "open calculator": ("filesystem", {"action": "open", "path": "calculator"}),
            "open terminal": ("filesystem", {"action": "open", "path": "cmd"}),
            "open cmd": ("filesystem", {"action": "open", "path": "cmd"}),
            "open powershell": ("filesystem", {"action": "open", "path": "powershell"}),
            
            # Time and date
            "what time": ("get_time", {}),
            "what time is it": ("get_time", {}),
            "tell me the time": ("get_time", {}),
            "what date": ("get_date", {}),
            "what day is it": ("get_date", {}),
            "what's the date": ("get_date", {}),
            
            # Search
            "search *": ("web_search", {"query": "*"}),
            "google *": ("web_search", {"query": "*"}),
            
            # Project commands
            "run tests": ("detect_project", {"action": "test"}),
            "run test": ("detect_project", {"action": "test"}),
            "test": ("detect_project", {"action": "test"}),
            "run *": ("detect_project", {"action": "run", "target": "*"}),
            
            # System commands
            "list files": ("filesystem", {"action": "list"}),
            "list directory": ("filesystem", {"action": "list"}),
            "show files": ("filesystem", {"action": "list"}),
            "system status": ("system_monitor", {"action": "all"}),
            "system info": ("system_monitor", {"action": "all"}),
            "cpu usage": ("system_monitor", {"action": "cpu"}),
            "memory usage": ("system_monitor", {"action": "memory"}),
            
            # Shutdown/restart (these need confirmation)
            "shutdown": ("system", {"action": "shutdown"}),
            "restart": ("system", {"action": "restart"}),
            "sleep": ("system", {"action": "sleep"}),
            "hibernate": ("system", {"action": "hibernate"}),
            
            # Quick actions
            "volume up": ("system", {"action": "volume_up"}),
            "volume down": ("system", {"action": "volume_down"}),
            "mute": ("system", {"action": "mute"}),
            "screenshot": ("system", {"action": "screenshot"}),
        }
        
        for pattern, (tool, args) in builtin_patterns.items():
            self._direct_commands[pattern] = (tool, args)
    
    def add_direct_command(self, pattern: str, tool_name: str, tool_args: dict | None = None) -> None:
        """
        Add a direct command pattern.
        
        Args:
            pattern: Command pattern (supports * wildcard)
            tool_name: Name of tool to execute
            tool_args: Arguments for the tool
        """
        self._direct_commands[pattern.lower()] = (tool_name, tool_args or {})
        logger.info(f"Added direct command: '{pattern}' -> {tool_name}")
    
    def remove_direct_command(self, pattern: str) -> bool:
        """
        Remove a direct command pattern.
        
        Args:
            pattern: Command pattern to remove
            
        Returns:
            True if removed, False if not found
        """
        pattern_lower = pattern.lower()
        if pattern_lower in self._direct_commands:
            del self._direct_commands[pattern_lower]
            logger.info(f"Removed direct command: '{pattern}'")
            return True
        return False
    
    def learn_command(self, user_input: str, tool_name: str, tool_args: dict | None = None) -> None:
        """
        Learn a command from successful executions (for learning engine).
        
        Args:
            user_input: The user input that triggered this
            tool_name: Tool that was executed
            tool_args: Arguments used
        """
        normalized = user_input.lower().strip()
        self._learned_commands[normalized] = (tool_name, tool_args or {})
        logger.debug(f"Learned command: '{user_input}' -> {tool_name}")
    
    def learn_correction(
        self, 
        trigger: str, 
        correct_tool: str, 
        correct_args: dict | None = None,
        confidence: int = 7
    ) -> None:
        """
        Learn from a user correction (when user corrects JARVIS's choice).
        
        Args:
            trigger: The action/command that was corrected
            correct_tool: The correct tool the user wanted
            correct_args: The correct arguments
            confidence: Confidence level (1-10)
        """
        if self._preference_memory is None:
            logger.warning("Preference memory not enabled")
            return
        
        self._preference_memory.learn(
            trigger=trigger,
            tool_name=correct_tool,
            tool_args=correct_args or {},
            confidence=confidence
        )
        
        # Also add to learned commands
        self.learn_command(trigger, correct_tool, correct_args)
        logger.info(f"Learned correction: '{trigger}' -> {correct_tool}")
    
    def get_preferred_tool(self, trigger: str) -> dict | None:
        """
        Get the preferred tool for a trigger.
        
        Args:
            trigger: The action/command to look up
            
        Returns:
            Dict with tool_name and tool_args, or None
        """
        if self._preference_memory is None:
            return None
        
        pref = self._preference_memory.get_preferred(trigger)
        if pref:
            return {
                "tool_name": pref.tool_name,
                "tool_args": pref.tool_args,
                "confidence": pref.confidence,
                "use_count": pref.use_count,
            }
        return None
    
    def forget_preference(self, trigger: str) -> bool:
        """
        Forget a learned preference.
        
        Args:
            trigger: The trigger to forget
            
        Returns:
            True if removed, False if not found
        """
        if self._preference_memory is None:
            return False
        
        return self._preference_memory.forget(trigger)
    
    def get_preference_stats(self) -> dict | None:
        """
        Get preference memory statistics.
        
        Returns:
            Dict with stats or None if preferences not enabled
        """
        if self._preference_memory is None:
            return None
        
        return self._preference_memory.get_stats()
    
    def route(self, user_input: str) -> RouterResult:
        """
        Route user input to appropriate handler.
        
        Args:
            user_input: The user's input text
            
        Returns:
            RouterResult with routing decision
        """
        start_time = time.perf_counter()
        
        # Normalize input
        normalized = user_input.lower().strip()
        
        # Check preference memory first (highest priority for learned preferences)
        if self._preference_memory is not None:
            pref = self._preference_memory.get_preferred(normalized)
            if pref:
                execution_time = (time.perf_counter() - start_time) * 1000
                result = RouterResult(
                    route_type=RouteType.DIRECT_TOOL,
                    tool_name=pref.tool_name,
                    tool_args=self._substitute_wildcards(pref.tool_args, user_input),
                    confidence=pref.confidence / 10.0,  # Convert 1-10 to 0.1-1.0
                    execution_time_ms=execution_time,
                )
                logger.info(f"Preference matched: '{user_input}' -> {pref.tool_name} (confidence: {pref.confidence}/10)")
                self._stats.direct_tool_calls += 1
                self._stats.total_execution_time_ms += execution_time
                return result
        
        # Check learned commands (next priority)
        if normalized in self._learned_commands:
            tool_name, tool_args = self._learned_commands[normalized]
            execution_time = (time.perf_counter() - start_time) * 1000
            result = RouterResult(
                route_type=RouteType.DIRECT_TOOL,
                tool_name=tool_name,
                tool_args=self._substitute_wildcards(tool_args, user_input),
                confidence=1.0,
                execution_time_ms=execution_time,
            )
            logger.info(f"Learned command matched: '{user_input}' -> {tool_name}")
            self._stats.direct_tool_calls += 1
            self._stats.total_execution_time_ms += execution_time
            return result
        
        # Check exact matches in direct commands
        if normalized in self._direct_commands:
            tool_name, tool_args = self._direct_commands[normalized]
            execution_time = (time.perf_counter() - start_time) * 1000
            result = RouterResult(
                route_type=RouteType.DIRECT_TOOL,
                tool_name=tool_name,
                tool_args=self._substitute_wildcards(tool_args, user_input),
                confidence=1.0,
                execution_time_ms=execution_time,
            )
            logger.info(f"Direct command matched: '{user_input}' -> {tool_name}")
            self._stats.direct_tool_calls += 1
            self._stats.total_execution_time_ms += execution_time
            return result
        
        # Check wildcard patterns
        wildcard_result = self._match_wildcard(normalized)
        if wildcard_result:
            execution_time = (time.perf_counter() - start_time) * 1000
            result = RouterResult(
                route_type=RouteType.DIRECT_TOOL,
                tool_name=wildcard_result[0],
                tool_args=self._substitute_wildcards(wildcard_result[1], user_input),
                confidence=0.9,
                execution_time_ms=execution_time,
            )
            logger.info(f"Wildcard command matched: '{user_input}' -> {wildcard_result[0]}")
            self._stats.direct_tool_calls += 1
            self._stats.total_execution_time_ms += execution_time
            return result
        
        # Check fuzzy matches
        fuzzy_result = self._match_fuzzy(normalized)
        if fuzzy_result and fuzzy_result[2] >= 0.7:  # High confidence threshold
            execution_time = (time.perf_counter() - start_time) * 1000
            result = RouterResult(
                route_type=RouteType.DIRECT_TOOL,
                tool_name=fuzzy_result[0],
                tool_args=self._substitute_wildcards(fuzzy_result[1], user_input),
                confidence=fuzzy_result[2],
                execution_time_ms=execution_time,
            )
            logger.info(f"Fuzzy command matched: '{user_input}' -> {fuzzy_result[0]} (confidence: {fuzzy_result[2]:.2f})")
            self._stats.direct_tool_calls += 1
            self._stats.total_execution_time_ms += execution_time
            return result
        
        # Check for chain requests (multi-step workflows)
        chain_template, chain_steps = self._detect_chain_request(normalized)
        if chain_template or chain_steps:
            execution_time = (time.perf_counter() - start_time) * 1000
            result = RouterResult(
                route_type=RouteType.CHAIN,
                chain_name=chain_template,
                chain_steps=chain_steps,
                confidence=0.9,
                execution_time_ms=execution_time,
            )
            logger.info(f"Chain request detected: '{user_input}' -> {chain_template or 'custom'}")
            return result
        
        # Check if it's explicitly requesting LLM
        if any(phrase in normalized for phrase in ["why", "how do i", "explain", "what is", "what are", "help me", "write code", "create"]):
            execution_time = (time.perf_counter() - start_time) * 1000
            result = RouterResult(
                route_type=RouteType.LLM_AGENT,
                confidence=0.8,
                execution_time_ms=execution_time,
            )
            logger.info(f"LLM agent requested: '{user_input}'")
            self._stats.llm_agent_calls += 1
            self._stats.total_execution_time_ms += execution_time
            return result
        
        # Default: unknown, route to LLM (safer)
        execution_time = (time.perf_counter() - start_time) * 1000
        result = RouterResult(
            route_type=RouteType.UNKNOWN,
            confidence=0.3,
            execution_time_ms=execution_time,
        )
        logger.info(f"Unknown command, defaulting to LLM: '{user_input}'")
        self._stats.unknown_routes += 1
        self._stats.total_execution_time_ms += execution_time
        return result
    
    def _match_wildcard(self, normalized: str) -> tuple[str, dict] | None:
        """Match wildcard patterns."""
        for pattern in self._direct_commands:
            if "*" in pattern:
                # Convert wildcard pattern to regex
                regex_pattern = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
                if re.match(regex_pattern, normalized):
                    return self._direct_commands[pattern]
        return None
    
    def _match_fuzzy(self, normalized: str) -> tuple[str, dict, float] | None:
        """Match using fuzzy/Levenshtein distance."""
        best_match = None
        best_distance = float("inf")
        
        for pattern in self._direct_commands:
            distance = self._levenshtein_distance(normalized, pattern)
            # Allow up to 3 edits for matching
            if distance < best_distance and distance <= 3:
                best_distance = distance
                best_match = pattern
        
        if best_match:
            # Convert distance to confidence (closer = higher confidence)
            max_len = max(len(normalized), len(best_match))
            confidence = 1.0 - (best_distance / max_len)
            return (self._direct_commands[best_match][0], self._direct_commands[best_match][1], confidence)
        
        return None
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _substitute_wildcards(self, args: dict, user_input: str) -> dict:
        """Substitute wildcard placeholders in tool arguments."""
        result = {}
        for key, value in args.items():
            if value == "*":
                # Extract from user input
                result[key] = user_input
            elif isinstance(value, str) and "*" in value:
                # Handle patterns like "search *"
                result[key] = value.replace("*", user_input.replace("search ", "").replace("google ", ""))
            else:
                result[key] = value
        return result
    
    def execute_direct(self, result: RouterResult) -> str:
        """
        Execute a direct tool call.
        
        Args:
            result: RouterResult from route() with DIRECT_TOOL type
            
        Returns:
            Tool output or error message
        """
        if result.route_type != RouteType.DIRECT_TOOL:
            return f"Error: Cannot execute_direct on {result.route_type.value}"
        
        if not self.tool_registry:
            return "Error: No tool registry configured"
        
        tool_name = result.tool_name
        tool_args = result.tool_args or {}
        
        try:
            output = self.tool_registry.execute(tool_name, tool_args)
            logger.debug(f"Direct execution completed in {result.execution_time_ms:.2f}ms")
            return output
        except Exception as e:
            error_msg = f"Direct execution failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def execute_with_fallback(self, result: RouterResult) -> str:
        """
        Execute with fallback attempts.
        
        Args:
            result: RouterResult from route()
            
        Returns:
            Tool output or error message
        """
        if result.route_type != RouteType.DIRECT_TOOL:
            return f"Error: Cannot execute_with_fallback on {result.route_type.value}"
        
        if not self.tool_registry:
            return "Error: No tool registry configured"
        
        tool_name = result.tool_name
        tool_args = result.tool_args or {}
        
        # Try primary tool
        try:
            output = self.tool_registry.execute(tool_name, tool_args)
            if not output.startswith("Error:"):
                return output
        except Exception as e:
            logger.debug(f"Primary tool failed: {e}")
        
        # Try alternative: detect_project -> try different test commands
        if tool_name == "detect_project":
            alternatives = [
                ("filesystem", {"action": "run", "target": "pytest"}),
                ("filesystem", {"action": "run", "target": "npm test"}),
                ("filesystem", {"action": "run", "target": "python -m pytest"}),
            ]
            for alt_tool, alt_args in alternatives:
                try:
                    output = self.tool_registry.execute(alt_tool, alt_args)
                    if not output.startswith("Error:"):
                        return output
                except Exception:
                    continue
        
        # All fallbacks failed
        return f"Error: Could not execute command. No fallback available."
    
    def execute_chain(self, result: RouterResult, user_input: str | None = None) -> str:
        """
        Execute a chain request.
        
        Args:
            result: RouterResult from route() with CHAIN type
            user_input: Original user input for custom chains
            
        Returns:
            Chain execution result
        """
        if result.route_type != RouteType.CHAIN:
            return f"Error: Cannot execute_chain on {result.route_type.value}"
        
        try:
            from brain.chains import TaskChain
            
            chain = TaskChain(
                agent=self.tool_registry.llm if self.tool_registry else None,
                tool_registry=self.tool_registry,
            )
            
            # Use template or custom steps
            if result.chain_name:
                template = chain.get_template(result.chain_name)
                if not template:
                    return f"Error: Template '{result.chain_name}' not found"
                steps = template
            elif result.chain_steps:
                steps = result.chain_steps
            elif user_input:
                # Parse from user input
                parsed = chain.parse_chain_request(user_input)
                steps = [{"action": s.action, "input": s.input} for s in parsed]
            else:
                return "Error: No chain steps or template provided"
            
            # Execute the chain
            chain_result = chain.execute_chain(steps)
            return chain_result.final_output
            
        except Exception as e:
            error_msg = f"Chain execution failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def get_stats(self) -> CommandStats:
        """Get router statistics."""
        return self._stats
    
    def reset_stats(self) -> None:
        """Reset router statistics."""
        self._stats = CommandStats()
        logger.info("Router statistics reset")


def create_router(tool_registry=None) -> CommandRouter:
    """
    Factory function to create a command router.
    
    Args:
        tool_registry: Optional ToolRegistry instance
        
    Returns:
        Configured CommandRouter instance
    """
    return CommandRouter(tool_registry=tool_registry)


__all__ = [
    "CommandRouter",
    "RouteType", 
    "RouterResult",
    "CommandStats",
    "create_router",
]

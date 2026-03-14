"""
JARVIS Brain Layer - Prompt Builder Module

Assembles prompts with system instructions, memory context, and conversation history.
"""

from typing import TYPE_CHECKING, Any

from loguru import logger

# Import ContextInjector only for type hints (avoid circular import)
if TYPE_CHECKING:
    from context.injector import ContextInjector


SYSTEM_PROMPT = """You are JARVIS, a helpful AI assistant.

IMPORTANT: 
- Use tools to get REAL-TIME or CURRENT information that you don't have in your training data
- For stock prices, weather, current news, current events - ALWAYS use search_web tool
- For current time/date - use get_time or get_date tool

## Tool Format
When you need real-time or current information, respond with:
Thought: I need to search for current information about [topic]
Action: search_web: {"query": "your search query"}

For time/date:
Thought: I need the current time/date
Action: get_time OR get_date

Then provide your answer based on the observation."""


class PromptBuilder:
    """Builds prompts with context from memory and conversation history."""

    def __init__(
        self,
        system_prompt: str | None = None,
        max_history: int = 10,
        context_injector: "ContextInjector | None" = None,
    ):
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.max_history = max_history
        self.conversation_history: list[dict[str, str]] = []
        self._context_injector = context_injector

    @property
    def context_injector(self) -> "ContextInjector | None":
        """Get the context injector."""
        return self._context_injector

    def set_context_injector(self, injector: "ContextInjector") -> None:
        """Set the context injector for automatic context injection."""
        self._context_injector = injector

    def get_context_injector(self) -> "ContextInjector | None":
        """Get the current context injector (alias for context_injector property)."""
        return self._context_injector

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        if role not in ("user", "assistant", "system"):
            logger.warning(f"Unknown message role: {role}, treating as user")
            role = "user"
        
        self.conversation_history.append({"role": role, "content": content})
        
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []

    def build(
        self,
        user_input: dict[str, str] | None = None,
        memory_context: str = "",
        vector_context: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """
        Build complete message list for LLM.
        
        Args:
            user_input: User message dict with 'role' and 'content'
            memory_context: Content from MEMORY.md (from Phase 5)
            vector_context: Relevant memories from vector store (from Phase 5)
        
        Returns:
            List of message dicts ready for LLM
        """
        messages: list[dict[str, str]] = []
        
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # Inject context if context_injector is set
        if self._context_injector is not None:
            context_summary = self._context_injector.get_context_summary()
            messages.append({
                "role": "system",
                "content": f"## Environment Context\n{context_summary}"
            })
        
        if memory_context:
            messages.append({
                "role": "system",
                "content": f"## Memory Context\n{memory_context}"
            })
        
        if vector_context:
            context_str = "\n".join(f"- {ctx}" for ctx in vector_context)
            messages.append({
                "role": "system",
                "content": f"## Relevant Context\n{context_str}"
            })
        
        for msg in self.conversation_history:
            if msg["role"] != "system":
                messages.append(msg)
        
        if user_input:
            if user_input.get("role") != "user":
                messages.append({"role": "user", "content": user_input["content"]})
            else:
                messages.append(user_input)
        
        return messages

    def build_simple(self, user_input: str) -> list[dict[str, str]]:
        """Build simple prompt with just system message and user input."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]


__all__ = ["PromptBuilder", "SYSTEM_PROMPT"]

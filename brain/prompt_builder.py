"""
JARVIS Brain Layer - Prompt Builder Module

Assembles prompts with system instructions, memory context, and conversation history.
"""

from typing import Any

from loguru import logger


SYSTEM_PROMPT = """You are JARVIS, a helpful AI voice assistant that runs entirely locally on Windows.

## Your Capabilities
- You can answer questions and have conversations
- You can use tools to perform actions like searching the web, running commands, and more
- You have access to memory from previous conversations

## Communication Style
- Be concise and helpful
- Respond naturally as if speaking to the user
- Use markdown sparingly for readability

## Tool Usage
When you need to use a tool, respond in this format:
Thought: [your reasoning about what to do next]
Action: tool_name: [arguments in JSON format]

For example:
Thought: I need to check the current time.
Action: get_time

After executing a tool, you will receive an observation with the result, then continue reasoning or provide your final answer.

## Important
- If you don't need to use any tools, just provide your answer directly
- If a tool fails, acknowledge the error and try an alternative approach
- Always prioritize user privacy - don't log or share personal information
"""


class PromptBuilder:
    """Builds prompts with context from memory and conversation history."""

    def __init__(
        self,
        system_prompt: str | None = None,
        max_history: int = 10,
    ):
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.max_history = max_history
        self.conversation_history: list[dict[str, str]] = []

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

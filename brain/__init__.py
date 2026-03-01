# JARVIS Brain Module
# LLM client, ReAct agent, and tool execution

from brain.client import OllamaClient, OllamaConnectionError
from brain.prompt_builder import PromptBuilder
from brain.agent import ReActAgent
from brain.tools import ToolRegistry, ToolExecutionError, create_default_registry
from brain.errors import (
    MalformedOutputError,
    AgentError,
    ToolError,
    retry_on_error,
    handle_malformed_output,
    ErrorHandler,
)

__all__ = [
    "OllamaClient",
    "OllamaConnectionError",
    "PromptBuilder",
    "ReActAgent",
    "ToolRegistry",
    "ToolExecutionError",
    "create_default_registry",
    "MalformedOutputError",
    "AgentError",
    "ToolError",
    "retry_on_error",
    "handle_malformed_output",
    "ErrorHandler",
]

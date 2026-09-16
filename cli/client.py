"""
JARVIS CLI Client — Direct agent access, no server needed.
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import load_config
from core.hardware import detect_hardware
from brain.agent import ReActAgent
from brain.router import CommandRouter, RouteType
from brain.tools import create_tools_registry
from memory import MemoryManager


class JarvisClient:
    """Direct client that talks to the agent in-process."""

    def __init__(self):
        hw = detect_hardware()
        self.config = load_config(hw.vram_total_mb)
        self.memory = MemoryManager(self.config)
        self.tool_registry = create_tools_registry()
        self.agent = ReActAgent(tool_registry=self.tool_registry)
        self.router = CommandRouter(tool_registry=self.tool_registry)

    def chat(self, message: str) -> str:
        memory_context = self.memory.format_context_for_prompt(message)

        route_result = self.router.route(message)
        if route_result.route_type == RouteType.DIRECT_TOOL:
            response = self.router.execute_direct(route_result)
        elif route_result.route_type == RouteType.CHAIN:
            response = self.router.execute_chain(route_result, message)
        else:
            response = self.agent.run(message, memory_context=memory_context)

        self.memory.save_conversation(message, response)
        return response

    def get_memories(self, limit: int = 50) -> dict:
        results = self.memory.get_vector_context("recent", n_results=limit)
        return {"memories": results}

    def search_memory(self, query: str, limit: int = 10) -> dict:
        results = self.memory.get_vector_context(query, n_results=limit)
        return {"results": results}

    def get_memory_stats(self) -> dict:
        return self.memory.get_stats()

    def clear_memories(self) -> dict:
        count = self.memory.delete_session("default")
        return {"deleted": count}

    def get_stats(self) -> dict:
        from tools.system_monitor import SystemMonitorTool
        monitor = SystemMonitorTool()
        return monitor.execute(action="all")

    def health_check(self) -> bool:
        return True

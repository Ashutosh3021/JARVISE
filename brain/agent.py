"""
JARVIS Brain Layer - ReAct Agent Module

Implements the ReAct (Reasoning + Acting) agent loop with learning capabilities.
"""

import re
from typing import Generator, Callable

from loguru import logger

from brain.client import OllamaClient, OllamaConnectionError
from brain.prompt_builder import PromptBuilder
from brain.tools import ToolRegistry, ToolExecutionError


class ReActAgent:
    """ReAct agent that reasons and acts to fulfill user requests."""

    MAX_ITERATIONS = 10

    def __init__(
        self,
        llm_client: OllamaClient | None = None,
        tool_registry: ToolRegistry | None = None,
        prompt_builder: PromptBuilder | None = None,
        max_iterations: int = MAX_ITERATIONS,
    ):
        self.llm = llm_client or OllamaClient()
        self.tools = tool_registry or ToolRegistry()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.max_iterations = max_iterations

    def run(
        self,
        user_input: str,
        memory_context: str | None = None,
        stream_callback: Callable[[str], None] | None = None
    ) -> str:
        """
        Run the ReAct agent on user input.
        
        Args:
            user_input: The user's input text
            memory_context: Optional memory context to prepend to the prompt
            stream_callback: Optional callback for streaming responses
            
        Returns:
            Final response from the agent
        """
        raw_user_input = user_input
        messages = self.prompt_builder.build(
            user_input={"role": "user", "content": raw_user_input},
            memory_context=memory_context or "",
        )
        
        # Add tools to the user message (not as a separate system message - 
        # having 2 system messages causes llama to return empty!)
        tool_schema = self.tools.get_tool_schema()
        if tool_schema and tool_schema != "No tools available.":
            # Append tools info to the last user message
            for msg in reversed(messages):
                if msg["role"] == "user":
                    msg["content"] = f"{msg['content']}\n\n{tool_schema}"
                    break
        
        full_response = ""
        tool_calls = 0
        max_tool_calls = 10  # Limit tool calls to prevent infinite loops
        
        for iteration in range(self.max_iterations):
            logger.debug(f"ReAct iteration {iteration + 1}/{self.max_iterations}")
            
            try:
                response = self.llm.chat(messages)
                content = response.get("message", {}).get("content", "")
                
                if not content:
                    logger.warning("Empty response from LLM")
                    break
                
                full_response = content
                
                if stream_callback:
                    stream_callback(content)
                
                thought, action_name, action_args = self.tools.parse_action(content)
                
                if action_name is None:
                    logger.info("No action detected, returning final answer")
                    # Clean up response - remove Thought/Action lines for user
                    full_response = self._clean_response(content)
                    break
                
                # Check if we've exceeded max tool calls
                if tool_calls >= max_tool_calls:
                    logger.warning(f"Max tool calls ({max_tool_calls}) reached, requesting final answer")
                    # Don't clean — content is just Thought:/Action: lines (empty after cleaning).
                    # Ask LLM for a natural final answer instead.
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": "Please give your final answer now without using any more tools."})
                    final = self.llm.chat(messages)
                    full_response = final.get("message", {}).get("content", "")
                    full_response = self._clean_response(full_response)
                    break
                
                logger.info(f"Executing tool: {action_name}")
                observation = self.tools.execute(action_name, action_args)
                tool_calls += 1
                
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
                
                # Continue loop to let LLM process the observation and formulate response
                logger.info(f"Tool executed, continuing with observation")
                continue
                
            except OllamaConnectionError as e:
                error_msg = f"Connection error: {str(e)}"
                logger.error(error_msg)
                return f"Sorry, I'm having trouble connecting to the language model. {error_msg}"
            except Exception as e:
                logger.error(f"Error in ReAct loop: {e}")
                return f"An error occurred: {str(e)}"
        
        self.prompt_builder.add_message("user", raw_user_input)
        self.prompt_builder.add_message("assistant", full_response)
        
        return full_response

    def stream_run(
        self,
        user_input: str,
        memory_context: str | None = None,
    ) -> Generator[tuple[str, bool], None, None]:
        """
        Run the ReAct agent with streaming responses.
        
        Args:
            user_input: The user's input text
            memory_context: Optional memory context for the prompt
            
        Yields:
            Tuples of (token, is_final) where is_final indicates end of response
        """
        raw_user_input = user_input
        messages = self.prompt_builder.build(
            user_input={"role": "user", "content": raw_user_input},
            memory_context=memory_context or "",
        )
        
        # Add tools to the user message (not as a separate system message)
        tool_schema = self.tools.get_tool_schema()
        if tool_schema and tool_schema != "No tools available.":
            for msg in reversed(messages):
                if msg["role"] == "user":
                    msg["content"] = f"{msg['content']}\n\n{tool_schema}"
                    break
        
        full_response = ""
        tool_calls = 0
        max_tool_calls = 10  # Limit tool calls to prevent infinite loops
        
        for iteration in range(self.max_iterations):
            logger.debug(f"ReAct iteration {iteration + 1}/{self.max_iterations}")
            
            try:
                content_parts: list[str] = []
                for chunk in self.llm.stream_chat(messages):
                    content_parts.append(chunk)
                    yield chunk, False
                content = "".join(content_parts)
                
                if not content:
                    logger.warning("Empty response from LLM")
                    break
                
                full_response = content
                
                thought, action_name, action_args = self.tools.parse_action(content)
                
                if action_name is None:
                    logger.info("No action detected, returning final answer")
                    yield "", True
                    break
                
                # Check if we've exceeded max tool calls
                if tool_calls >= max_tool_calls:
                    logger.warning(f"Max tool calls ({max_tool_calls}) reached, requesting final answer")
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": "Please give your final answer now without using any more tools."})
                    final_parts: list[str] = []
                    for chunk in self.llm.stream_chat(messages):
                        final_parts.append(chunk)
                        yield chunk, False
                    final_content = self._clean_response("".join(final_parts))
                    full_response = final_content
                    yield "", True
                    break
                
                logger.info(f"Executing tool: {action_name}")
                observation = self.tools.execute(action_name, action_args)
                tool_calls += 1
                
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
                
                # Continue loop to let LLM process the observation and formulate response
                logger.info(f"Tool executed, continuing with observation")
                continue
                
            except OllamaConnectionError as e:
                error_msg = f"Connection error: {str(e)}"
                logger.error(error_msg)
                yield f"Sorry, I'm having trouble connecting to the language model. {error_msg}", True
                break
            except Exception as e:
                logger.error(f"Error in ReAct loop: {e}")
                yield f"An error occurred: {str(e)}", True
                break
        
        self.prompt_builder.add_message("user", raw_user_input)
        self.prompt_builder.add_message("assistant", self._clean_response(full_response))

    def _clean_response(self, response: str) -> str:
        """Remove Thought/Action lines from response for user-facing output."""
        import re
        # Remove Thought: lines
        cleaned = re.sub(r'^Thought:.*$', '', response, flags=re.MULTILINE)
        # Remove Action: lines
        cleaned = re.sub(r'^Action:.*$', '', cleaned, flags=re.MULTILINE)
        # Clean up extra whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()
    
    def reset(self) -> None:
        """Reset the agent's conversation history."""
        self.prompt_builder.clear_history()
    
    # ========== Learning Methods ==========
    
    def on_user_correction(self, user_input: str, last_action: str | None = None) -> dict | None:
        """
        Detect and learn from user corrections.
        
        Detects patterns like:
        - "no, open *"
        - "I meant *"
        - "not that, *"
        - "wrong, *"
        
        Args:
            user_input: The user's correction input
            last_action: The last action the agent took (optional)
            
        Returns:
            Dictionary with learned preference or None if no correction detected
        """
        # Import preference store lazily to avoid circular imports
        try:
            from memory.preference_store import PreferenceStore
        except ImportError:
            return None
        
        correction_patterns = [
            (r"no[,\s]+(?:open|run|start|use)\s+(\w+)", "app_aliases"),
            (r"i\s+meant\s+(?:open|run|start|use)\s+(\w+)", "app_aliases"),
            (r"not\s+(?:that|this|it)[,\s]+(?:but|open|run|start|use)\s+(\w+)", "app_aliases"),
            (r"wrong[,\s]+(?:open|run|start|use)\s+(\w+)", "app_aliases"),
            (r"use\s+(\w+)\s+instead", "app_aliases"),
            (r"(\w+)\s+not\s+(\w+)", "command_patterns"),
        ]
        
        user_input_lower = user_input.lower()
        
        for pattern, category in correction_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                # Extract the correction
                if len(match.groups()) >= 1:
                    key = match.group(1) if last_action is None else last_action
                    value = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    
                    # Store the preference
                    store = PreferenceStore()
                    category_prefs = store.get_category(category)
                    category_prefs[key] = value
                    store.set_category(category, category_prefs)
                    
                    logger.info(f"Learned preference: {key} -> {value} (category: {category})")
                    
                    return {
                        "key": key,
                        "value": value,
                        "category": category
                    }
        
        return None
    
    def apply_learned_preferences(self, user_input: str) -> str:
        """
        Apply learned preferences to modify user input before processing.
        
        Args:
            user_input: Original user input
            
        Returns:
            Modified user input with preferences applied
        """
        try:
            from memory.preference_store import PreferenceStore
        except ImportError:
            return user_input
        
        store = PreferenceStore()
        modified = user_input
        
        # Apply app aliases
        app_aliases = store.get_category("app_aliases")
        for alias, actual in app_aliases.items():
            # Replace alias with actual app name
            pattern = re.compile(rf'\b{re.escape(alias)}\b', re.IGNORECASE)
            modified = pattern.sub(actual, modified)
        
        # Apply command patterns
        command_patterns = store.get_category("command_patterns")
        for pattern, replacement in command_patterns.items():
            if pattern.lower() in modified.lower():
                modified = modified.replace(pattern, replacement)
        
        return modified


__all__ = ["ReActAgent"]

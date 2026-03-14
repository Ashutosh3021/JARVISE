"""
JARVIS Brain Layer - ReAct Agent Module

Implements the ReAct (Reasoning + Acting) agent loop.
"""

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

    def run(self, user_input: str, stream_callback: Callable[[str], None] | None = None) -> str:
        """
        Run the ReAct agent on user input.
        
        Args:
            user_input: The user's input text
            stream_callback: Optional callback for streaming responses
            
        Returns:
            Final response from the agent
        """
        messages = self.prompt_builder.build(
            user_input={"role": "user", "content": user_input}
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
        max_tool_calls = 3  # Limit tool calls to prevent infinite loops
        
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
                    logger.warning(f"Max tool calls ({max_tool_calls}) reached, returning current response")
                    full_response = self._clean_response(content)
                    break
                
                logger.info(f"Executing tool: {action_name}")
                observation = self.tools.execute(action_name, action_args)
                tool_calls += 1
                
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
                
                # After getting observation, provide final answer without further tool calls
                logger.info("Tool executed, returning final answer")
                # Include observation in cleaned response
                full_response = f"{observation}"
                break
                
            except OllamaConnectionError as e:
                error_msg = f"Connection error: {str(e)}"
                logger.error(error_msg)
                return f"Sorry, I'm having trouble connecting to the language model. {error_msg}"
            except Exception as e:
                logger.error(f"Error in ReAct loop: {e}")
                return f"An error occurred: {str(e)}"
        
        self.prompt_builder.add_message("user", user_input)
        self.prompt_builder.add_message("assistant", full_response)
        
        return full_response

    def stream_run(
        self,
        user_input: str,
    ) -> Generator[tuple[str, bool], None, None]:
        """
        Run the ReAct agent with streaming responses.
        
        Args:
            user_input: The user's input text
            
        Yields:
            Tuples of (token, is_final) where is_final indicates end of response
        """
        messages = self.prompt_builder.build(
            user_input={"role": "user", "content": user_input}
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
        max_tool_calls = 3  # Limit tool calls to prevent infinite loops
        
        for iteration in range(self.max_iterations):
            logger.debug(f"ReAct iteration {iteration + 1}/{self.max_iterations}")
            
            try:
                response = self.llm.chat(messages)
                content = response.get("message", {}).get("content", "")
                
                if not content:
                    logger.warning("Empty response from LLM")
                    break
                
                full_response = content
                
                thought, action_name, action_args = self.tools.parse_action(content)
                
                if action_name is None:
                    logger.info("No action detected, returning final answer")
                    yield content, True
                    break
                
                # Check if we've exceeded max tool calls
                if tool_calls >= max_tool_calls:
                    logger.warning(f"Max tool calls ({max_tool_calls}) reached, returning current response")
                    yield content, True
                    break
                
                logger.info(f"Executing tool: {action_name}")
                observation = self.tools.execute(action_name, action_args)
                tool_calls += 1
                
                yield content, False
                
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
                
                # After getting observation, provide final answer
                logger.info("Tool executed, returning final answer")
                yield observation, True
                break
                
            except OllamaConnectionError as e:
                error_msg = f"Connection error: {str(e)}"
                logger.error(error_msg)
                yield f"Sorry, I'm having trouble connecting to the language model. {error_msg}", True
                break
            except Exception as e:
                logger.error(f"Error in ReAct loop: {e}")
                yield f"An error occurred: {str(e)}", True
                break
        
        self.prompt_builder.add_message("user", user_input)
        self.prompt_builder.add_message("assistant", full_response)

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


__all__ = ["ReActAgent"]

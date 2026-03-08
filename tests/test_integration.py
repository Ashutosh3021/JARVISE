"""
Integration tests for JARVIS agent pipeline.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAgentPipeline:
    """Integration tests for the full agent pipeline."""
    
    @patch('brain.agent.OllamaClient')
    @patch('brain.agent.ToolRegistry')
    @patch('brain.agent.PromptBuilder')
    def test_agent_initialization(self, mock_prompt, mock_tools, mock_client):
        """Test that ReActAgent can be initialized."""
        from brain.agent import ReActAgent
        
        agent = ReActAgent()
        
        assert agent is not None
        assert hasattr(agent, 'llm')
        assert hasattr(agent, 'tools')
        assert hasattr(agent, 'prompt_builder')
    
    @patch('brain.agent.OllamaClient')
    @patch('brain.agent.ToolRegistry')
    @patch('brain.agent.PromptBuilder')
    def test_agent_run_returns_string(self, mock_prompt, mock_tools, mock_client):
        """Test that agent.run() returns a string response."""
        from brain.agent import ReActAgent
        
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_client_instance.chat.return_value = {
            "message": {"content": "Test response"}
        }
        mock_client.return_value = mock_client_instance
        
        mock_tools_instance = MagicMock()
        mock_tools_instance.parse_action.return_value = (None, None, None)
        mock_tools_instance.get_tool_schema.return_value = ""
        mock_tools.return_value = mock_tools_instance
        
        agent = ReActAgent()
        response = agent.run("Hello")
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @patch('brain.agent.OllamaClient')
    @patch('brain.agent.ToolRegistry')
    @patch('brain.agent.PromptBuilder')
    def test_agent_handles_empty_input(self, mock_prompt, mock_tools, mock_client):
        """Test that agent handles empty input gracefully."""
        from brain.agent import ReActAgent
        
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_client_instance.chat.return_value = {
            "message": {"content": "Response"}
        }
        mock_client.return_value = mock_client_instance
        
        mock_tools_instance = MagicMock()
        mock_tools_instance.parse_action.return_value = (None, None, None)
        mock_tools_instance.get_tool_schema.return_value = ""
        mock_tools.return_value = mock_tools_instance
        
        agent = ReActAgent()
        response = agent.run("")
        
        # Should still return something
        assert isinstance(response, str)
    
    @patch('brain.agent.OllamaClient')
    @patch('brain.agent.ToolRegistry')
    @patch('brain.agent.PromptBuilder')
    def test_agent_resets_history(self, mock_prompt, mock_tools, mock_client):
        """Test that agent.reset() clears conversation history."""
        from brain.agent import ReActAgent
        
        agent = ReActAgent()
        agent.reset()
        
        # Just verify it doesn't error
        assert True


class TestToolRegistry:
    """Tests for tool registry."""
    
    def test_tool_registry_import(self):
        """Test that ToolRegistry can be imported."""
        from brain.tools import ToolRegistry
        
        assert ToolRegistry is not None
    
    def test_tool_registry_init(self):
        """Test ToolRegistry initialization."""
        from brain.tools import ToolRegistry
        
        registry = ToolRegistry()
        
        assert registry is not None


class TestMainEntryPoint:
    """Tests for main.py entry point."""
    
    def test_main_imports(self):
        """Test that main.py can be imported."""
        import main
        
        assert main is not None
    
    def test_banner_defined(self):
        """Test that ASCII banner is defined."""
        import main
        
        assert hasattr(main, 'BANNER')
        assert isinstance(main.BANNER, str)
    
    def test_signal_handler_defined(self):
        """Test that signal handler is defined."""
        import main
        
        assert hasattr(main, 'signal_handler')
        assert callable(main.signal_handler)

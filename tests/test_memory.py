"""
Unit tests for memory system.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMemoryManager:
    """Tests for MemoryManager."""
    
    @patch('memory.MemoryManager.VectorStore')
    @patch('memory.MemoryManager.MemoryFileController')
    def test_memory_manager_init(self, mock_file, mock_store):
        """Test MemoryManager initialization."""
        from core.config import load_config
        from memory import MemoryManager
        
        config = load_config(0)
        manager = MemoryManager(config)
        
        assert manager is not None
        assert manager.config == config
    
    @patch('memory.MemoryManager.VectorStore')
    @patch('memory.MemoryManager.MemoryFileController')
    def test_save_conversation(self, mock_file, mock_store):
        """Test saving conversation to memory."""
        from core.config import load_config
        from memory import MemoryManager
        
        config = load_config(0)
        
        # Setup mocks
        mock_store_instance = MagicMock()
        mock_store_instance.save_conversation.return_value = "test_id_123"
        mock_store.return_value = mock_store_instance
        
        manager = MemoryManager(config)
        manager._vector_store = mock_store_instance
        
        # Test save
        result = manager.save_conversation("Hello", "Hi there!")
        
        assert result == "test_id_123"
        mock_store_instance.save_conversation.assert_called_once()
    
    @patch('memory.MemoryManager.VectorStore')
    @patch('memory.MemoryManager.MemoryFileController')
    def test_get_context(self, mock_file, mock_store):
        """Test retrieving context from memory."""
        from core.config import load_config
        from memory import MemoryManager
        
        config = load_config(0)
        
        # Setup mocks
        mock_store_instance = MagicMock()
        mock_store_instance.get_context.return_value = [
            {"document": "User: Hello\nAssistant: Hi", "metadata": {}}
        ]
        mock_store.return_value = mock_store_instance
        
        manager = MemoryManager(config)
        manager._vector_store = mock_store_instance
        
        # Test get context
        context = manager.get_context("Hello")
        
        assert len(context) > 0
        mock_store_instance.get_context.assert_called()
    
    @patch('memory.MemoryManager.VectorStore')
    @patch('memory.MemoryManager.MemoryFileController')
    def test_save_fact(self, mock_file, mock_store):
        """Test saving fact to memory."""
        from core.config import load_config
        from memory import MemoryManager
        
        config = load_config(0)
        
        # Setup mocks
        mock_file_instance = MagicMock()
        mock_file.return_value = mock_file_instance
        
        manager = MemoryManager(config)
        manager._memory_file = mock_file_instance
        
        # Test save fact
        manager.save_fact("User prefers dark mode")
        
        mock_file_instance.save_fact.assert_called_once_with("User prefers dark mode")
    
    @patch('memory.MemoryManager.VectorStore')
    @patch('memory.MemoryManager.MemoryFileController')
    def test_get_preferences(self, mock_file, mock_store):
        """Test retrieving preferences from memory."""
        from core.config import load_config
        from memory import MemoryManager
        
        config = load_config(0)
        
        # Setup mocks
        mock_file_instance = MagicMock()
        mock_file_instance.get_preferences.return_value = {}
        mock_file.return_value = mock_file_instance
        
        manager = MemoryManager(config)
        manager._memory_file = mock_file_instance
        
        # Test get preferences (returns dict)
        prefs = manager.get_preferences()
        
        assert isinstance(prefs, dict)


class TestVectorStore:
    """Tests for VectorStore (with mocking)."""
    
    def test_vector_store_import(self):
        """Test that VectorStore can be imported."""
        from memory import VectorStore
        
        assert VectorStore is not None
    
    def test_vector_store_init(self):
        """Test VectorStore initialization."""
        from memory.chroma_store import VectorStore
        
        # Just verify it can be instantiated with temp dir
        store = VectorStore(persist_directory=":memory:")
        
        assert store is not None
        assert store.COLLECTION_NAME == "conversations"

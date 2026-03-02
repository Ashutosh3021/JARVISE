"""
JARVIS ChromaDB Vector Store

Provides persistent vector storage for conversation embeddings using ChromaDB.
"""

from datetime import datetime, timezone
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer


class VectorStore:
    """
    Vector store for storing and retrieving conversation embeddings.
    
    Uses ChromaDB with PersistentClient for local storage and
    sentence-transformers for embedding generation.
    """
    
    COLLECTION_NAME = "conversations"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    def __init__(self, persist_directory: str = "./data/chromadb"):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        self.persist_directory = persist_directory
        self._embedding_model = None
        self._client = None
        self._collection = None
    
    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)
        return self._embedding_model
    
    @property
    def client(self) -> chromadb.PersistentClient:
        """Lazy-initialize the ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
        return self._client
    
    @property
    def collection(self) -> chromadb.Collection:
        """Lazy-initialize the conversations collection."""
        if self._collection is None:
            # Get or create collection with the embedding function
            self._collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "JARVIS conversation embeddings"}
            )
        return self._collection
    
    def _embed(self, text: str) -> list[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embedding_model.encode(text, convert_to_numpy=True).tolist()
    
    def _generate_id(self, session_id: str, timestamp: datetime) -> str:
        """Generate a unique ID for a conversation entry."""
        return f"{session_id}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
    
    def save_conversation(
        self,
        user_query: str,
        assistant_response: str,
        session_id: str = "default",
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Save a conversation exchange to the vector store.
        
        Args:
            user_query: The user's query/input
            assistant_response: The assistant's response
            session_id: Identifier for the conversation session
            metadata: Optional additional metadata
            
        Returns:
            The ID of the stored conversation entry
        """
        timestamp = datetime.now(timezone.utc)
        
        # Combine user query and assistant response for embedding
        combined_text = f"User: {user_query}\nAssistant: {assistant_response}"
        
        # Create metadata
        entry_metadata = {
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "user_query": user_query,
            "assistant_response": assistant_response,
        }
        
        # Add any additional metadata
        if metadata:
            entry_metadata.update(metadata)
        
        # Generate unique ID
        entry_id = self._generate_id(session_id, timestamp)
        
        # Get embedding
        embedding = self._embed(combined_text)
        
        # Store in ChromaDB
        self.collection.add(
            ids=[entry_id],
            embeddings=[embedding],
            documents=[combined_text],
            metadatas=[entry_metadata]
        )
        
        return entry_id
    
    def get_context(
        self,
        query: str,
        n_results: int = 3,
        session_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant context from past conversations.
        
        Args:
            query: Query to search for relevant context
            n_results: Number of results to return
            session_id: Optional filter for specific session
            
        Returns:
            List of relevant conversation entries with metadata
        """
        # Generate embedding for the query
        query_embedding = self._embed(query)
        
        # Build where clause for filtering
        where = {"session_id": session_id} if session_id else None
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        context = []
        if results["ids"] and results["ids"][0]:
            for i, entry_id in enumerate(results["ids"][0]):
                context.append({
                    "id": entry_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None,
                })
        
        return context
    
    def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get conversation history for a specific session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of entries to return
            
        Returns:
            List of conversation entries for the session
        """
        results = self.collection.get(
            where={"session_id": session_id},
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        history = []
        if results["ids"]:
            for i, entry_id in enumerate(results["ids"]):
                history.append({
                    "id": entry_id,
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i],
                })
        
        return history
    
    def delete_session(self, session_id: str) -> int:
        """
        Delete all entries for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of entries deleted
        """
        # Get all IDs for the session
        results = self.collection.get(
            where={"session_id": session_id},
            include=["ids"]
        )
        
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])
        
        return 0
    
    def clear_all(self) -> None:
        """Clear all data from the collection."""
        self.collection.delete(where={})
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with store statistics
        """
        return {
            "collection_name": self.COLLECTION_NAME,
            "total_entries": self.collection.count(),
            "persist_directory": self.persist_directory,
            "embedding_model": self.EMBEDDING_MODEL,
        }


# Export public API
__all__ = ["VectorStore"]

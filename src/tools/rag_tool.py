"""RAG (Retrieval-Augmented Generation) tool for news retrieval."""
from typing import List, Dict, Optional
from config.settings import RAG_PERSIST_DIRECTORY, RAG_COLLECTION_NAME


class RAGTool:
    """Tool for semantic search and retrieval of financial news."""
    
    def __init__(
        self,
        persist_directory: str = RAG_PERSIST_DIRECTORY,
        collection_name: str = RAG_COLLECTION_NAME
    ):
        """Initialize RAG tool.
        
        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Collection name for news storage
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._vector_db = None  # Lazy load when needed
    
    def _get_vector_db(self):
        """Get vector database instance (lazy initialization)."""
        if self._vector_db is False:
            return None  # Previously failed to initialize
        
        if self._vector_db is None:
            try:
                from data.vector_db import VectorDatabase
                self._vector_db = VectorDatabase(
                    persist_directory=self.persist_directory,
                    collection_name=self.collection_name
                )
            except Exception as e:
                print(f"[WARN] VectorDatabase initialization failed: {e}")
                self._vector_db = False  # Mark as failed
                return None
        
        return self._vector_db
    
    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """Query news database.
        
        Args:
            query_text: Query string
            top_k: Number of results to return
            
        Returns:
            List of relevant news articles
        """
        vector_db = self._get_vector_db()
        if not vector_db:
            return []
        
        try:
            results = vector_db.query(query_text, top_k=top_k)
            if results:
                print(f"(RAG) Found {len(results)} results for query: '{query_text}'")
            else:
                print(f"(RAG) No results found for query: '{query_text}'")
            return results
        except Exception as e:
            print(f"[WARN] RAG query failed: {e}")
            return []
    
    def add_documents(self, texts: List[str], metadatas: List[Dict]):
        """Add documents to news database.
        
        Args:
            texts: List of article texts
            metadatas: List of metadata dictionaries
        """
        vector_db = self._get_vector_db()
        if not vector_db:
            print("[WARN] Cannot add documents: RAG not available")
            return
        
        try:
            vector_db.add_documents(texts, metadatas)
            print(f"(RAG) Added {len(texts)} documents to collection")
        except Exception as e:
            print(f"[WARN] RAG add_documents failed: {e}")
    
    def retrieve_context(self, query_text: str, top_k: int = 3) -> str:
        """Retrieve context text for LLM.
        
        Args:
            query_text: Query string
            top_k: Number of results to include
            
        Returns:
            Formatted context string
        """
        results = self.query(query_text, top_k=top_k)
        if not results:
            return ""
        
        context_parts = []
        for r in results:
            text = r.get("text", "")
            meta = r.get("metadata", {})
            snippet = text[:800] + "..." if len(text) > 800 else text
            context_parts.append(f"- ({meta.get('symbol', 'N/A')}) {snippet}")
        
        return "\n".join(context_parts)


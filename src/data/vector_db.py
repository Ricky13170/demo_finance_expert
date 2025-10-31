"""
Vector Database - Lưu trữ và tìm kiếm tin tức bằng ChromaDB

Chức năng:
- Lưu tin tức vào vector database
- Tìm kiếm tin tức bằng semantic search
- Tự động tạo embedding cho text
"""
# Tắt telemetry của ChromaDB TRƯỚC KHI import để tránh lỗi
import os
os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

# Suppress ChromaDB warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")

import uuid
from typing import List, Dict, Optional
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from chromadb.config import Settings
from config.settings import (
    RAG_PERSIST_DIRECTORY,
    RAG_COLLECTION_NAME,
    RAG_EMBEDDING_MODEL
)


class VectorDatabase:
    """Vector database wrapper for ChromaDB."""
    
    def __init__(
        self,
        persist_directory: str = RAG_PERSIST_DIRECTORY,
        collection_name: str = RAG_COLLECTION_NAME,
        embedding_model: str = RAG_EMBEDDING_MODEL
    ):
        """Initialize vector database.
        
        Args:
            persist_directory: Directory to persist database
            collection_name: Name of the collection
            embedding_model: Embedding model name
        """
        os.makedirs(persist_directory, exist_ok=True)
        
        # Khởi tạo ChromaDB client (đã tắt telemetry ở trên)
        self.client = PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        self.embedding_model = embedding_model
        self.embedding_fn = None  # Lazy load when needed
        self.collection_name = collection_name
        self.collection = None  # Lazy load when needed
    
    def _ensure_embedding_fn(self):
        """Initialize embedding function (lazy loading)."""
        if self.embedding_fn is None:
            try:
                self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model
                )
            except (ValueError, ImportError) as e:
                error_msg = str(e)
                if "sentence_transformers" in error_msg.lower():
                    print(f"[ERROR] sentence-transformers package not installed!")
                    print(f"[ERROR] Please run: pip install sentence-transformers")
                    raise ImportError(
                        "sentence-transformers package is required for RAG functionality. "
                        "Please install it with: pip install sentence-transformers"
                    ) from e
                raise
    
    def _ensure_collection(self):
        """Initialize collection (lazy loading)."""
        if self.collection is None:
            self._ensure_embedding_fn()
            existing_collections = [c.name for c in self.client.list_collections()]
            if self.collection_name not in existing_collections:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_fn
                )
                print(f"Created new collection '{self.collection_name}'")
            else:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_fn
                )
                print(f"Loaded existing collection '{self.collection_name}'")
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add documents to the collection.
        
        Args:
            texts: List of text documents
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs
        """
        if not texts:
            return
        
        self._ensure_collection()
        
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]
        
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
        print(f"Added {len(texts)} documents to ChromaDB")
    
    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """Query the collection.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries with text, metadata, and score
        """
        if not query_text:
            return []
        
        self._ensure_collection()
        
        results = self.collection.query(query_texts=[query_text], n_results=top_k)
        
        if not results or not results.get("documents") or not results["documents"][0]:
            return []
        
        retrieved = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            retrieved.append({
                "text": doc,
                "metadata": meta,
                "score": 1 - dist
            })
        return retrieved
    
    def clear_collection(self):
        """Delete all documents in the collection."""
        self._ensure_collection()
        self.collection.delete(where={})
        print("Collection cleared")


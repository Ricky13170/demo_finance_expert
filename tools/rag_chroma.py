import os
os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

import uuid
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from chromadb.config import Settings
from typing import List, Dict, Optional


class RAGChroma:
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "financial_knowledge",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        RAG layer using ChromaDB (v0.5.23+) for local semantic retrieval.
        """
        os.makedirs(persist_directory, exist_ok=True)

        self.client = PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )

        existing_collections = [c.name for c in self.client.list_collections()]
        if collection_name not in existing_collections:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
            print(f"Created new collection '{collection_name}'")
        else:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
            print(f"Loaded existing collection '{collection_name}'")

        print(f"ChromaDB path: {persist_directory}")

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None):
        if not texts:
            return
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]

        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
        print(f"✅ Added {len(texts)} documents to ChromaDB")


    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        if not query_text:
            return []

        results = self.collection.query(query_texts=[query_text], n_results=top_k)

        if not results or not results.get("documents") or not results["documents"][0]:
            return []

        retrieved = []
        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            retrieved.append({
                "text": doc,
                "metadata": meta,
                "score": 1 - dist
            })
        return retrieved

    def clear_collection(self):
        """Delete all documents in the collection."""
        self.collection.delete(where={})
        print("🗑️ Collection cleared")


if __name__ == "__main__":
    rag = RAGChroma()
    docs = [
        "Cổ phiếu FPT tăng mạnh nhờ kết quả kinh doanh quý 3 vượt kỳ vọng.",
        "Thị trường chứng khoán Việt Nam giảm điểm do lo ngại lãi suất Mỹ tăng.",
        "Ngân hàng Vietcombank công bố lợi nhuận kỷ lục năm 2025."
    ]
    metadata = [
        {"source": "cafef.vn", "date": "2025-10-27"},
        {"source": "vneconomy.vn", "date": "2025-10-26"},
        {"source": "vietstock.vn", "date": "2025-10-25"}
    ]
    rag.add_documents(docs, metadata)
    res = rag.query("Cổ phiếu FPT")
    print(res)

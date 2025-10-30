import os
from typing import List
from tools.rag_chroma import RAGChroma


class RagEngine:
    """
    RAG Engine tích hợp với ChromaDB.
    - Dùng RAGChroma để truy vấn & thêm dữ liệu tin tức.
    - Cung cấp các hàm query(), add_documents(), retrieve_context().
    """

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "finance_news"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        self.rag = RAGChroma(
            persist_directory=self.persist_directory,
            collection_name=self.collection_name
        )

        print(f"ChromaDB collection '{self.collection_name}' initialized at {self.persist_directory}")

    def query(self, query_text: str, top_k: int = 3) -> List[dict]:
        """
        Tìm kiếm tin tức trong ChromaDB theo câu truy vấn.
        Trả về danh sách dict gồm text + metadata.
        """
        try:
            results = self.rag.query(query_text, top_k=top_k)
            if results:
                print(f"(RAG) Tìm thấy {len(results)} kết quả liên quan đến truy vấn: '{query_text}'")
            else:
                print(f"(RAG) Không tìm thấy kết quả cho truy vấn: '{query_text}'")
            return results
        except Exception as e:
            print(f"[WARN] RAG query failed: {e}")
            return []

    def add_documents(self, texts: List[str], metadatas: List[dict]):
        """
        Thêm tài liệu mới vào ChromaDB.
        """
        try:
            self.rag.add_documents(texts, metadatas)
            print(f"(RAG) Đã thêm {len(texts)} tài liệu mới vào collection '{self.collection_name}'.")
        except Exception as e:
            print(f"[WARN] RAG add_documents failed: {e}")

    def retrieve_context(self, query_text: str, top_k: int = 3) -> str:
        """
        Trả về context text (kết hợp nhiều đoạn tin) cho LLM.
        Dùng để bổ sung thông tin ngữ cảnh khi tạo phản hồi.
        """
        results = self.query(query_text, top_k=top_k)
        if not results:
            return ""

        # Ghép các đoạn text lại làm ngữ cảnh
        context_parts = []
        for r in results:
            text = r.get("text", "")
            meta = r.get("metadata", {})
            snippet = text[:800] + "..." if len(text) > 800 else text
            context_parts.append(f"- ({meta.get('symbol', 'N/A')}) {snippet}")

        return "\n".join(context_parts)

# rag/rag_engine.py
import os
import json
import glob
import pandas as pd
from typing import List, Optional
from dataclasses import dataclass

# nhẹ: local Document-like dataclass (không phụ thuộc langchain)
@dataclass
class SimpleDoc:
    page_content: str
    metadata: dict

class RagEngine:
    """
    RAG Engine (placeholder)
    - Không gọi API embeddings (tạm thời)
    - Đọc file data/* (csv, xlsx, xls, txt)
    - Lưu "raw_docs.json" để dùng sau khi bạn implement embeddings
    - retrieve_context() trả về các đoạn tương đối liên quan bằng fuzzy substring match (fallback)
    - Sau này: implement build_index() để tạo embeddings + FAISS/Chroma...
    """

    def __init__(self, data_dir: str = "data", index_path: str = "rag_index", raw_dump: str = "rag_raw_docs.json"):
        self.data_dir = data_dir
        self.index_path = index_path
        self.raw_dump = raw_dump
        self.raw_docs: List[SimpleDoc] = []
        self.vectorstore = None  # future place to hold FAISS/Chroma object
        # load existing raw dump if exists
        if os.path.exists(self.raw_dump):
            try:
                with open(self.raw_dump, "r", encoding="utf-8") as f:
                    arr = json.load(f)
                    self.raw_docs = [SimpleDoc(page_content=d["page_content"], metadata=d.get("metadata", {})) for d in arr]
            except Exception:
                self.raw_docs = []

    # -------------------------
    def _read_files_to_docs(self) -> List[SimpleDoc]:
        docs: List[SimpleDoc] = []
        if not os.path.exists(self.data_dir):
            return docs

        for path in glob.glob(os.path.join(self.data_dir, "*")):
            fname = os.path.basename(path)
            try:
                if fname.lower().endswith((".csv",)):
                    df = pd.read_csv(path)
                    for _, row in df.iterrows():
                        content = " ".join([str(v) for v in row.values if pd.notna(v)])
                        if content.strip():
                            docs.append(SimpleDoc(page_content=content, metadata={"source": fname}))
                elif fname.lower().endswith((".xlsx", ".xls")):
                    # read via pandas (user must have xlrd/openpyxl installed)
                    df = pd.read_excel(path)
                    for _, row in df.iterrows():
                        content = " ".join([str(v) for v in row.values if pd.notna(v)])
                        if content.strip():
                            docs.append(SimpleDoc(page_content=content, metadata={"source": fname}))
                elif fname.lower().endswith((".txt", ".md")):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read().strip()
                        if text:
                            docs.append(SimpleDoc(page_content=text, metadata={"source": fname}))
                else:
                    # ignore other files
                    continue
            except Exception as e:
                print(f"[WARN] Không đọc được file {fname}: {e}")
        return docs

    # -------------------------
    def build_index(self, force_reload: bool = False):
        """
        Placeholder:
        - đọc files và lưu ra raw_dump (json)
        - nếu bạn muốn hiện tại build vectorstore, override / extend this
        """
        print("📊 (RAG) build_index: đọc file raw và lưu ra raw dump (tạm).")
        docs = self._read_files_to_docs()
        if not docs:
            print("[WARN] Không tìm thấy tài liệu nào để build (data dir empty).")
            self.raw_docs = []
            return

        self.raw_docs = docs
        try:
            with open(self.raw_dump, "w", encoding="utf-8") as f:
                json.dump([{"page_content": d.page_content, "metadata": d.metadata} for d in docs], f, ensure_ascii=False, indent=2)
            print(f"✅ Đã lưu {len(docs)} đoạn raw docs vào {self.raw_dump}. Khi bạn thêm embeddings, chạy lại để build index.")
        except Exception as e:
            print("[WARN] Không thể lưu raw dump:", e)

    # -------------------------
    def load_index(self):
        """
        Nếu bạn lưu vectorstore (FAISS/...), load vào self.vectorstore ở đây.
        Hiện placeholder trả về None.
        """
        if self.vectorstore is not None:
            return self.vectorstore
        # Future: implement loading FAISS/Chroma etc.
        print("[RAG] load_index: chưa có vectorstore (placeholder).")
        return None

    # -------------------------
    def set_vectorstore(self, vs):
        """
        Cho phép external code set vectorstore object (FAISS/Chroma).
        """
        self.vectorstore = vs

    # -------------------------
    def get_relevant_docs(self, query: str, k: int = 3) -> List[SimpleDoc]:
        """
        Trả về danh sách SimpleDoc. Nếu vectorstore được set -> dùng nó.
        Nếu chưa -> fallback: substring scoring on raw_docs.
        """
        if self.vectorstore:
            # future: call vectorstore.similarity_search(query, k=k) and adapt to SimpleDoc
            try:
                hits = self.vectorstore.similarity_search(query, k=k)
                # hits might be langchain Documents; normalize
                result = []
                for h in hits:
                    text = getattr(h, "page_content", str(h))
                    meta = getattr(h, "metadata", {})
                    result.append(SimpleDoc(page_content=text, metadata=meta))
                return result
            except Exception as e:
                print("[WARN] vectorstore search failed:", e)
                # fall through to fallback

        # fallback simple substring score
        scores = []
        q_lower = query.lower()
        for d in self.raw_docs:
            txt = d.page_content.lower()
            score = 0
            if q_lower in txt:
                score += 10
            # add some simple heuristics: number of query tokens present
            tokens = [t for t in q_lower.split() if len(t) > 2]
            hits = sum(1 for t in tokens if t in txt)
            score += hits
            if score > 0:
                scores.append((score, d))
        scores.sort(key=lambda x: x[0], reverse=True)
        top = [d for _, d in scores[:k]]
        return top

    # -------------------------
    def retrieve_context(self, query: str, k: int = 3) -> str:
        """
        Return concatenated snippets for LLM prompt. Empty string if nothing.
        """
        docs = self.get_relevant_docs(query, k=k)
        if not docs:
            return ""
        parts = []
        for d in docs:
            snippet = d.page_content
            if len(snippet) > 800:
                snippet = snippet[:800] + "..."
            parts.append(f"- ({d.metadata.get('source','')}) {snippet}")
        return "\n".join(parts)

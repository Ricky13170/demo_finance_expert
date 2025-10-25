# file: rag/build_index.py
import os
from dotenv import load_dotenv   # 🟢 thêm dòng này
from rag.rag_engine import RagEngine

if __name__ == "__main__":
    # 🟢 nạp file .env trước khi khởi tạo RagEngine
    load_dotenv()

    data_dir = "data"

    print("🔧 Khởi tạo và nạp dữ liệu RAG...")
    rag = RagEngine(data_dir=data_dir)
    rag.build_index()  # tạo embeddings và lưu lại

    print("✅ Hoàn tất! RAG index đã được lưu và sẵn sàng sử dụng.")

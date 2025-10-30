import os
from dotenv import load_dotenv 
from rag.rag_engine import RagEngine

if __name__ == "__main__":
    load_dotenv()

    data_dir = "data"

    print("🔧 Khởi tạo và nạp dữ liệu RAG...")
    rag = RagEngine(data_dir=data_dir)
    rag.build_index()  

    print("Hoàn tất! RAG index đã được lưu và sẵn sàng sử dụng.")

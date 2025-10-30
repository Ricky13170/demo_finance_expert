import os
from chromadb import PersistentClient

persist_directory = "./chroma_db"

client = PersistentClient(path=persist_directory)

collections = client.list_collections()
print("Danh sách collections trong ChromaDB:")
for c in collections:
    print(f" - {c.name}")

collection = client.get_or_create_collection("finance_news")

data = collection.get(limit=10)

print(f"\nTổng số tài liệu hiện có: {len(data['ids'])}")
if data["documents"]:
    print("\n5 tin đầu tiên trong collection:")
    for i, doc in enumerate(data["documents"][:5]):
        meta = data["metadatas"][i]
        print(f"{i+1}. {doc[:120]}... |  {meta}")
else:
    print("Chưa có tin tức nào trong collection.")

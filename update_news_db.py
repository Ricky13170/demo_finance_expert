import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"  

from datetime import datetime
from tools.rag_chroma import RAGChroma
from agents.news_agent import NewsAgent

COLLECTION_NAME = "finance_news"     
SAVE_DIR = "./chroma_db"         
STOCK_SYMBOLS = ["FPT", "VCB", "VNM", "MWG", "HPG", "VIN"]   


def update_finance_news():
    print(f"🚀 Bắt đầu cập nhật tin tức tài chính ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    # Khởi tạo RAG và NewsAgent
    rag = RAGChroma(
        persist_directory=SAVE_DIR,
        collection_name=COLLECTION_NAME
    )
    agent = NewsAgent(max_articles_per_source=5)

    total_added = 0

    # Crawl tin tức cho từng mã cổ phiếu
    for symbol in STOCK_SYMBOLS:
        print(f"📡 Đang lấy tin tức cho mã: {symbol} ...")
        try:
            results = agent.run(symbol)
            articles = results.get("articles", [])
            if not articles:
                print(f"⚠️ Không tìm thấy tin mới cho {symbol}.")
                continue

            texts = [f"{a['title']} - {a['description']}" for a in articles]
            metas = [
                {
                    "symbol": symbol,
                    "source": a["source"],
                    "url": a["url"],
                    "date": a["date"],
                    "sentiment": a["sentiment"]
                }
                for a in articles
            ]

            # Thêm vào ChromaDB
            rag.add_documents(texts, metas)
            total_added += len(texts)
            print(f"✅ Đã thêm {len(texts)} tin cho {symbol}\n")

        except Exception as e:
            print(f"❌ Lỗi khi crawl {symbol}: {e}")

    print("=============================================")
    print(f"🎯 Hoàn tất cập nhật! Tổng số tin đã thêm: {total_added}")
    print(f"📦 Database: {os.path.join(SAVE_DIR, 'chroma.sqlite3')}")
    print("=============================================\n")

    sample_query = "Tình hình cổ phiếu FPT hôm nay"
    print(f"🔍 Kiểm tra truy vấn mẫu: '{sample_query}'\n")
    results = rag.query(sample_query)
    for i, r in enumerate(results, 1):
        meta = r["metadata"]
        print(f"{i}. {r['text']}")
        print(f"   📅 {meta.get('date')} | 🌐 {meta.get('source')} | 💬 {meta.get('sentiment')}")
        print(f"   🔗 {meta.get('url')}\n")

if __name__ == "__main__":
    update_finance_news()

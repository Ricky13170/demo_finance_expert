import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import logging
import textwrap
from tools.rag_chroma import RAGChroma

class NewsAgent:
    """Agent tìm kiếm và tóm tắt tin tức tài chính từ nhiều nguồn (Cafef, VnExpress, VietStock)."""

    def __init__(self, max_articles_per_source: int = 3):
        self.rag = RAGChroma(collection_name="finance_news")
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.max_articles_per_source = max_articles_per_source
        self.results = {}
        self.last_query = None

    # === Entry point chính ===
    def run(self, symbol: str) -> Dict:
        """Tìm tin tức và tạo tóm tắt cho mã cổ phiếu"""
        self.last_query = symbol.upper()
        all_articles = []
        all_articles.extend(self.search_cafef(symbol))
        # all_articles.extend(self.search_vnexpress(symbol))
        # all_articles.extend(self.search_vietstock(symbol))

        for a in all_articles:
            a["sentiment"] = self.get_sentiment_from_title(a["title"])

        summary_text = self.create_summary(symbol, all_articles)
        self.results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "articles": all_articles,
            "summary": summary_text
        }
        return self.results

    # === Crawl tin từ CafeF ===
    def search_cafef(self, symbol: str) -> List[Dict]:
        try:
            url = f"https://cafef.vn/tim-kiem.chn?keywords={symbol}"
            soup = BeautifulSoup(requests.get(url, headers=self.headers, timeout=10).content, 'html.parser')
            items = soup.find_all('div', class_='item', limit=self.max_articles_per_source)
            results = []
            for item in items:
                title_tag = item.find('h3')
                link_tag = item.find('a')
                desc_tag = item.find('p')
                if title_tag and link_tag:
                    results.append({
                        "source": "CafeF",
                        "title": title_tag.get_text(strip=True),
                        "url": 'https://cafef.vn' + link_tag['href'] if link_tag['href'].startswith('/') else link_tag['href'],
                        "description": desc_tag.get_text(strip=True) if desc_tag else '',
                        "date": datetime.now().strftime('%Y-%m-%d')
                    })
            return results
        except Exception as e:
            logging.warning(f"[CafeF] Lỗi crawl: {e}")
            return []

    # === Phân tích cảm xúc đơn giản ===
    def get_sentiment_from_title(self, title: str) -> str:
        pos = ['tăng', 'lợi nhuận', 'khả quan', 'vượt', 'kỷ lục']
        neg = ['giảm', 'lỗ', 'sụt', 'rủi ro', 'thất bại']
        t = title.lower()
        pos_count = sum(w in t for w in pos)
        neg_count = sum(w in t for w in neg)
        return 'positive' if pos_count > neg_count else 'negative' if neg_count > pos_count else 'neutral'

    # === Sinh tóm tắt dài (200–300 chữ) ===
    def create_summary(self, symbol: str, articles: List[Dict]) -> str:
        if not articles:
            return f"Không tìm thấy tin tức mới về {symbol.upper()} gần đây."

        pos = sum(a['sentiment'] == 'positive' for a in articles)
        neg = sum(a['sentiment'] == 'negative' for a in articles)
        overview = "📈 Xu hướng tích cực" if pos > neg else "📉 Xu hướng tiêu cực" if neg > pos else "➡️ Trung tính"

        body = ""
        for i, a in enumerate(articles, 1):
            emoji = {'positive':'✅','negative':'❌','neutral':'ℹ️'}[a['sentiment']]
            body += f"{i}. {emoji} {a['title']} ({a['source']})\n"
            if a['description']:
                body += f"   {a['description']}\n"
            body += f"   🔗 {a['url']}\n\n"

        full_text = f"📰 Tin tức mới nhất về {symbol.upper()} ({overview})\n\n{body.strip()}"
        return textwrap.shorten(full_text, width=300, placeholder="...")

    # === Mở rộng thông tin khi người dùng hỏi tiếp ===
    def expand_summary(self, article_index: int = None) -> str:
        """Cung cấp thêm chi tiết về tin tức trước đó"""
        if not self.results or "articles" not in self.results:
            return "⚠️ Hiện chưa có dữ liệu tin tức trước đó. Hãy hỏi tôi về một mã cổ phiếu trước nhé!"

        articles = self.results["articles"]
        if article_index is not None and 1 <= article_index <= len(articles):
            a = articles[article_index - 1]
            detail = f"📰 Chi tiết tin #{article_index}: {a['title']}\n📅 Ngày: {a['date']}\n🔗 {a['url']}\n"
            detail += f"Mô tả: {a['description'] or 'Không có mô tả chi tiết.'}"
            return detail
        else:
            # Nếu không chỉ định tin cụ thể → mở rộng toàn bộ danh sách
            full_list = "\n".join([
                f"{i+1}. {a['title']} ({a['source']}) - {a['url']}"
                for i, a in enumerate(articles)
            ])
            return f"📖 Đây là danh sách đầy đủ các tin đã thu thập:\n\n{full_list}"

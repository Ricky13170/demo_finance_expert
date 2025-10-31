"""News agent for retrieving and summarizing financial news."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import logging
import textwrap
from tools.rag_tool import RAGTool
from config.settings import MAX_ARTICLES_PER_SOURCE


class NewsAgent:
    """Agent for searching and summarizing financial news from multiple sources."""
    
    def __init__(self, max_articles_per_source: int = MAX_ARTICLES_PER_SOURCE):
        """Initialize news agent.
        
        Args:
            max_articles_per_source: Maximum articles to fetch per source
        """
        self.rag_tool = None  # Lazy load when needed
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.max_articles_per_source = max_articles_per_source
        self.results = {}
        self.last_query = None
    
    def _get_rag_tool(self):
        """Get RAG tool instance (lazy initialization)."""
        if self.rag_tool is None:
            try:
                self.rag_tool = RAGTool()
            except Exception as e:
                print(f"[WARN] Could not initialize RAG tool: {e}")
                self.rag_tool = False  # Mark as failed
        return self.rag_tool if self.rag_tool else None
    
    def run(self, symbol: str) -> Dict:
        """Search news and create summary for stock symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary containing articles and summary
        """
        self.last_query = symbol.upper()
        all_articles = []
        
        # Search multiple sources
        all_articles.extend(self.search_cafef(symbol))
        # all_articles.extend(self.search_vnexpress(symbol))
        # all_articles.extend(self.search_vietstock(symbol))
        
        # Add sentiment analysis
        for article in all_articles:
            article["sentiment"] = self.get_sentiment_from_title(article["title"])
        
        summary_text = self.create_summary(symbol, all_articles)
        
        self.results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "articles": all_articles,
            "summary": summary_text
        }
        
        return self.results
    
    def search_cafef(self, symbol: str) -> List[Dict]:
        """Search news from CafeF website.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of article dictionaries
        """
        try:
            url = f"https://cafef.vn/tim-kiem.chn?keywords={symbol}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', class_='item', limit=self.max_articles_per_source)
            
            results = []
            for item in items:
                title_tag = item.find('h3')
                link_tag = item.find('a')
                desc_tag = item.find('p')
                
                if title_tag and link_tag:
                    href = link_tag['href']
                    full_url = 'https://cafef.vn' + href if href.startswith('/') else href
                    
                    results.append({
                        "source": "CafeF",
                        "title": title_tag.get_text(strip=True),
                        "url": full_url,
                        "description": desc_tag.get_text(strip=True) if desc_tag else '',
                        "date": datetime.now().strftime('%Y-%m-%d')
                    })
            
            return results
        except Exception as e:
            logging.warning(f"[CafeF] Crawl error: {e}")
            return []
    
    def get_sentiment_from_title(self, title: str) -> str:
        """Analyze sentiment from article title.
        
        Args:
            title: Article title
            
        Returns:
            Sentiment: positive, negative, or neutral
        """
        positive_words = ['tang', 'loi nhuan', 'kha quan', 'vuot', 'ky luc', 'increase', 'profit', 'surpass']
        negative_words = ['giam', 'lo', 'sut', 'rui ro', 'that bai', 'decrease', 'loss', 'risk', 'failure']
        
        title_lower = title.lower()
        pos_count = sum(word in title_lower for word in positive_words)
        neg_count = sum(word in title_lower for word in negative_words)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
    
    def create_summary(self, symbol: str, articles: List[Dict]) -> str:
        """Create summary from articles.
        
        Args:
            symbol: Stock symbol
            articles: List of article dictionaries
            
        Returns:
            Summary text
        """
        if not articles:
            return f"No recent news found for {symbol.upper()}."
        
        # Calculate sentiment overview
        pos_count = sum(a['sentiment'] == 'positive' for a in articles)
        neg_count = sum(a['sentiment'] == 'negative' for a in articles)
        
        if pos_count > neg_count:
            overview = "Positive trend"
        elif neg_count > pos_count:
            overview = "Negative trend"
        else:
            overview = "Neutral"
        
        # Build summary body
        body = ""
        for i, article in enumerate(articles, 1):
            sentiment_marker = {
                'positive': '[+]',
                'negative': '[-]',
                'neutral': '[=]'
            }[article['sentiment']]
            
            body += f"{i}. {sentiment_marker} {article['title']} ({article['source']})\n"
            if article['description']:
                body += f"   {article['description']}\n"
            body += f"   Link: {article['url']}\n\n"
        
        full_text = f"Latest news about {symbol.upper()} ({overview})\n\n{body.strip()}"
        return textwrap.shorten(full_text, width=300, placeholder="...")
    
    def expand_summary(self, article_index: int = None) -> str:
        """Expand summary with more details.
        
        Args:
            article_index: Specific article index (1-based), or None for all
            
        Returns:
            Expanded summary text
        """
        if not self.results or "articles" not in self.results:
            return "No previous news data available. Please query a stock symbol first."
        
        articles = self.results["articles"]
        
        if article_index is not None and 1 <= article_index <= len(articles):
            article = articles[article_index - 1]
            detail = (
                f"Article #{article_index}: {article['title']}\n"
                f"Date: {article['date']}\n"
                f"Link: {article['url']}\n"
                f"Description: {article['description'] or 'No detailed description available.'}"
            )
            return detail
        else:
            # Expand full list
            full_list = "\n".join([
                f"{i+1}. {a['title']} ({a['source']}) - {a['url']}"
                for i, a in enumerate(articles)
            ])
            return f"Complete list of collected articles:\n\n{full_list}"


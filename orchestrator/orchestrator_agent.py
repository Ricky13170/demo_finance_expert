import os
import asyncio
from dotenv import load_dotenv
from typing import Optional
from openai import AsyncOpenAI

# --- Import agents ---
from agents.stock_agent import StockAgent
from agents.advice_agent import analyze_stock
from agents.news_agent import NewsAgent

# --- Import RAG + Memory ---
from rag.rag_engine import RagEngine
from memory.conversation_memory import ConversationMemory
from tools.rag_chroma import RAGChroma


class OrchestratorAgent:
    def __init__(
        self,
        model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct",
        rag_engine: Optional[RagEngine] = None,
        memory: Optional[ConversationMemory] = None,
    ):
        """Khởi tạo Orchestrator Agent"""
        load_dotenv()
        self.model_name = model_name
        self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError("❌ Thiếu GROQ_API_KEY trong .env")

        # --- Khởi tạo client LLM ---
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )

        # --- Các agent phụ ---
        self.stock_agent = StockAgent()
        self.news_agent = NewsAgent()
        self.rag_engine = rag_engine or RagEngine()
        self.memory = memory or ConversationMemory()

        # --- Kiểm tra RAG database ---
        if hasattr(self.rag_engine, "rag_db") and not getattr(self.rag_engine.rag_db, "collection", None):
            print("⚠️ RAG engine chưa khởi tạo collection, đang khởi tạo lại...")
            self.rag_engine.rag_db = RAGChroma()

    #Hàm gọi LLM Groq async
    async def _call_llm(self, prompt: str) -> str:
        """Gọi LLM Groq với prompt truyền vào"""
        try:
            resp = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=500,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print("[WARN] Groq LLM call failed:", e)
            return ""

    # Hàm chính xử lý query từ user
    async def handle_query(self, query: str, user_id: str = "default") -> str:
        """Xử lý câu hỏi từ người dùng"""

        # Lưu hội thoại user
        self.memory.add_message(user_id, "user", query)

        # Lấy lại lịch sử hội thoại gần nhất
        recent_history = self.memory.get_recent(user_id, n=6)
        conversation_context = "\n".join([
            f"{m['role']}: {m['text']}" for m in recent_history
        ])

        # Gọi LLM để xác định intent
        routing_prompt = f"""
        Lịch sử hội thoại gần đây:
        {conversation_context}

        Câu hỏi mới:
        {query}

        Hãy xác định loại yêu cầu của người dùng (intent chính):
        - Nếu hỏi về giá cổ phiếu → "price"
        - Nếu hỏi tư vấn đầu tư hoặc phân tích cổ phiếu → "advice"
        - Nếu hỏi tin tức hoặc xu hướng thị trường → "news"
        - Nếu chào hỏi hoặc trò chuyện chung → "chat"
        Trả về đúng 1 từ trong các loại trên.
        """

        try:
            routing_text = await self._call_llm(routing_prompt)
        except Exception:
            routing_text = ""

        rd = (routing_text or "").lower().strip()
        lower = query.lower()

        # Xác định intent
        if "advice" in rd or any(k in lower for k in ["mua", "bán", "phân tích", "khuyến nghị", "đầu tư"]):
            intent = "advice_query"
        elif "price" in rd or any(k in lower for k in ["giá", "bao nhiêu", "tăng", "giảm", "hôm nay", "hôm qua"]):
            intent = "price_query"
        elif "news" in rd or any(k in lower for k in ["tin tức", "thị trường", "vĩ mô", "xu hướng", "báo cáo"]):
            intent = "news_query"
        else:
            intent = "chat"

        # Lấy context từ RAG (nếu có)
        try:
            context_text = self.rag_engine.retrieve_context(query)
            if context_text:
                print(f"📚 RAG context len: {len(context_text)} chars")
        except Exception as e:
            print("[WARN] RAG retrieval failed:", e)
            context_text = ""

        # Gọi agent tương ứng
        if intent == "price_query":
            response = self.stock_agent.handle_request(query)

        elif intent == "advice_query":
            response = analyze_stock(query)

        elif intent == "news_query":
            symbol = self.stock_agent.extract_symbol(query)
            if not symbol:
                response = "Không tìm thấy mã cổ phiếu hợp lệ trong câu hỏi. Ví dụ: 'tin tức về FPT'."
            else:
                rag_results = []
                try:
                    rag_results = self.rag_engine.query(query)
                except Exception as e:
                    print("[WARN] RAG query failed:", e)

                if rag_results:
                    print(f"📚 Found {len(rag_results)} results from local RAG DB")
                    response = "\n".join([
                        f"- {r['text']} ({r['metadata'].get('source')}, {r['metadata'].get('date')})"
                        for r in rag_results[:3]
                    ])
                else:
                    print("🌐 No local data found → crawling news...")
                    data = self.news_agent.run(symbol)
                    if data and "articles" in data:
                        texts = [f"{a['title']} - {a['description']}" for a in data["articles"]]
                        metas = [
                            {
                                "symbol": symbol,
                                "source": a["source"],
                                "url": a["url"],
                                "date": a["date"],
                                "sentiment": a["sentiment"]
                            }
                            for a in data["articles"]
                        ]
                        self.rag_engine.add_documents(texts, metas)
                        print(f"✅ Saved {len(texts)} new articles for {symbol} to RAG")

                    response = data.get("summary", "Không tìm thấy tin tức mới.")
        else:
            response = "🤖 Xin chào! Mình là trợ lý tài chính. Bạn có thể hỏi về giá cổ phiếu, tư vấn đầu tư, hoặc tin tức thị trường."

        # Tạo prompt tổng hợp phản hồi thân thiện
        recent = self.memory.get_recent(user_id, n=6)
        recent_text = "\n".join([f"{m['role']}: {m['text']}" for m in recent])

        final_prompt = f"""
        Ngữ cảnh RAG (nếu có):
        {context_text}

        Lịch sử hội thoại gần nhất:
        {recent_text}

        Phản hồi từ hệ thống nội bộ:
        {response}

        👉 Hãy trả lời lại bằng tiếng Việt, ngắn gọn, tự nhiên, thân thiện và có thể thêm emoji phù hợp.
        """

        try:
            final_text = await self._call_llm(final_prompt)
        except Exception as e:
            print("[WARN] LLM formatting failed:", e)
            final_text = ""

        if not final_text:
            final_text = response if isinstance(response, str) else str(response)

        # Lưu phản hồi vào memory
        self.memory.add_message(user_id, "assistant", final_text)

        return final_text

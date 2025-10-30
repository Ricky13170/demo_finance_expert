"""
Orchestrator Agent - Điều phối viên chính

Nhiệm vụ:
- Nhận câu hỏi từ người dùng
- Phân loại câu hỏi (giá cổ phiếu / tư vấn / tin tức / chat)
- Gửi đến agent phù hợp để xử lý
- Trả về câu trả lời đã được format
"""
from typing import Optional
from services.llm_service import LLMService
from agents.stock_agent import StockAgent
from agents.news_agent import NewsAgent
from agents.advice_agent import analyze_stock
from data.memory import ConversationMemory
from config.settings import DEFAULT_MODEL, RAG_PERSIST_DIRECTORY, RAG_COLLECTION_NAME


class OrchestratorAgent:
    """
    Điều phối viên chính - Router quản lý các agent chuyên biệt
    
    Các agent:
    - StockAgent: Tra cứu giá cổ phiếu
    - NewsAgent: Tìm tin tức tài chính
    - AdviceAgent: Phân tích và tư vấn đầu tư
    """
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        rag_tool: Optional[object] = None,
        memory: Optional[ConversationMemory] = None,
    ):
        """
        Khởi tạo OrchestratorAgent
        
        Args:
            model_name: Tên model LLM để sử dụng
            rag_tool: Tool RAG (tìm kiếm ngữ nghĩa) - để None sẽ tự động load khi cần
            memory: Bộ nhớ lưu lịch sử hội thoại
        """
        self.model_name = model_name
        self.llm_service = LLMService(model_name=model_name)
        
        # Khởi tạo các agent chuyên biệt
        self.stock_agent = StockAgent()  # Tra cứu giá cổ phiếu
        self.news_agent = NewsAgent()   # Tìm tin tức
        
        # Lazy load RAG tool - chỉ load khi cần (vì load chậm)
        self._rag_tool = rag_tool
        self._rag_tool_init_error = None
        
        # Bộ nhớ lưu lịch sử hội thoại của từng user
        self.memory = memory or ConversationMemory()
    
    def _get_rag_tool(self):
        """
        Lấy RAG tool instance (lazy loading)
        
        RAG tool dùng để tìm kiếm tin tức đã lưu trong database
        Chỉ load khi thực sự cần vì import chậm
        """
        if self._rag_tool is False:
            return None  # Đã thử load nhưng thất bại
        
        if self._rag_tool is None:
            try:
                from tools.rag_tool import RAGTool
                self._rag_tool = RAGTool(
                    persist_directory=RAG_PERSIST_DIRECTORY,
                    collection_name=RAG_COLLECTION_NAME
                )
            except Exception as e:
                print(f"[WARN] Không thể khởi tạo RAG tool: {e}")
                print("[INFO] Tiếp tục mà không có chức năng RAG")
                self._rag_tool = False  # Đánh dấu đã thất bại
                return None
        
        return self._rag_tool
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Gọi LLM API để xử lý prompt
        
        Args:
            prompt: Câu hỏi hoặc prompt cần xử lý
            
        Returns:
            Câu trả lời từ LLM
        """
        return await self.llm_service.complete(prompt)
    
    async def handle_query(self, query: str, user_id: str = "default") -> str:
        """
        Xử lý câu hỏi từ người dùng - Hàm chính
        
        Quy trình:
        1. Lưu câu hỏi vào memory
        2. Phân loại câu hỏi (giá cổ phiếu / tư vấn / tin tức / chat)
        3. Gửi đến agent phù hợp
        4. Format câu trả lời bằng LLM
        5. Lưu câu trả lời vào memory
        
        Args:
            query: Câu hỏi từ người dùng
            user_id: ID người dùng (để lưu lịch sử)
            
        Returns:
            Câu trả lời đã được format
        """
        # Bước 1: Lưu câu hỏi vào memory
        self.memory.add_message(user_id, "user", query)
        
        # Bước 2: Lấy lịch sử hội thoại gần đây
        recent_history = self.memory.get_recent(user_id, n=6)
        conversation_context = "\n".join([
            f"{m['role']}: {m['text']}" for m in recent_history
        ])
        
        # Bước 3: Phân loại câu hỏi bằng LLM
        routing_prompt = f"""
        Lịch sử hội thoại gần đây:
        {conversation_context}

        Câu hỏi mới:
        {query}

        Xác định loại câu hỏi:
        - Hỏi về giá cổ phiếu → "price"
        - Hỏi tư vấn đầu tư hoặc phân tích cổ phiếu → "advice"
        - Hỏi về tin tức hoặc xu hướng thị trường → "news"
        - Chào hỏi hoặc chat chung → "chat"
        Trả về đúng 1 từ trong các loại trên.
        """
        
        try:
            routing_text = await self._call_llm(routing_prompt)
        except Exception:
            routing_text = ""
        
        routing_decision = (routing_text or "").lower().strip()
        query_lower = query.lower()
        
        # Bước 4: Xác định intent với logic fallback (nếu LLM không trả lời)
        if "advice" in routing_decision or any(k in query_lower for k in ["mua", "ban", "phan tich", "khuyen nghi", "dau tu", "buy", "sell", "analyze", "advice"]):
            intent = "advice_query"
        elif "price" in routing_decision or any(k in query_lower for k in ["gia", "bao nhieu", "tang", "giam", "hom nay", "hom qua", "price", "how much", "today", "yesterday"]):
            intent = "price_query"
        elif "news" in routing_decision or any(k in query_lower for k in ["tin tuc", "thi truong", "vi mo", "xu huong", "bao cao", "news", "market", "trend"]):
            intent = "news_query"
        else:
            intent = "chat"
        
        # Bước 5: Lấy context từ RAG nếu có (để bổ sung thông tin)
        context_text = ""
        rag_tool = self._get_rag_tool()
        if rag_tool:
            try:
                context_text = rag_tool.retrieve_context(query)
                if context_text:
                    print(f"RAG context length: {len(context_text)} chars")
            except Exception as e:
                print(f"[WARN] RAG retrieval failed: {e}")
                context_text = ""
        
        # Bước 6: Gửi đến agent phù hợp để xử lý
        if intent == "price_query":
            # Hỏi về giá cổ phiếu → dùng StockAgent
            response = self.stock_agent.handle_request(query)
        
        elif intent == "advice_query":
            # Hỏi tư vấn đầu tư → dùng AdviceAgent
            response = analyze_stock(query)
        
        elif intent == "news_query":
            # Hỏi về tin tức → dùng NewsAgent
            symbol = self.stock_agent.extract_symbol(query)
            if not symbol:
                response = "Không tìm thấy mã cổ phiếu hợp lệ trong câu hỏi. Ví dụ: 'tin tức về FPT'."
            else:
                # Thử tìm trong RAG database trước
                rag_results = []
                if rag_tool:
                    try:
                        rag_results = rag_tool.query(query)
                    except Exception as e:
                        print(f"[WARN] RAG query failed: {e}")
                
                if rag_results:
                    # Tìm thấy trong database → trả về kết quả
                    print(f"Found {len(rag_results)} results from local RAG database")
                    response = "\n".join([
                        f"- {r['text']} ({r['metadata'].get('source')}, {r['metadata'].get('date')})"
                        for r in rag_results[:3]
                    ])
                else:
                    # Không tìm thấy → crawl tin tức mới từ web
                    print("No local data found → crawling news...")
                    data = self.news_agent.run(symbol)
                    if data and "articles" in data:
                        # Lưu vào RAG database để dùng sau
                        if rag_tool:
                            try:
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
                                rag_tool.add_documents(texts, metas)
                                print(f"Saved {len(texts)} new articles for {symbol} to RAG")
                            except Exception as e:
                                print(f"[WARN] Failed to save to RAG: {e}")
                    
                    response = data.get("summary", "No new news found.")
        else:
            # Chat chung
            response = "Xin chào! Tôi là trợ lý tài chính. Bạn có thể hỏi tôi về giá cổ phiếu, tư vấn đầu tư, hoặc tin tức thị trường."
        
        # Bước 7: Format câu trả lời bằng LLM để tự nhiên hơn
        recent = self.memory.get_recent(user_id, n=6)
        recent_text = "\n".join([f"{m['role']}: {m['text']}" for m in recent])
        
        final_prompt = f"""
        RAG context (nếu có):
        {context_text}

        Lịch sử hội thoại gần đây:
        {recent_text}

        Câu trả lời từ system:
        {response}

        Vui lòng trả lời bằng tiếng Việt, ngắn gọn, tự nhiên và thân thiện.
        """
        
        try:
            final_text = await self._call_llm(final_prompt)
        except Exception as e:
            print(f"[WARN] LLM formatting failed: {e}")
            final_text = ""
        
        # Fallback nếu LLM không trả lời
        if not final_text:
            final_text = response if isinstance(response, str) else str(response)
        
        # Bước 8: Lưu câu trả lời vào memory
        self.memory.add_message(user_id, "assistant", final_text)
        
        return final_text


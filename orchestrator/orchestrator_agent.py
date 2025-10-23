import os
import asyncio
from dotenv import load_dotenv
from google import genai
from orchestrator.prompt_templates import ORCHESTRATOR_PROMPT
from agents.stock_agent import StockAgent
from agents.advice_agent import analyze_stock


class OrchestratorAgent:
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        Orchestrator chịu trách nhiệm:
        - Định tuyến câu hỏi (routing) bằng Gemini
        - Gọi agent phù hợp (stock_agent hoặc advice_agent)
        - Dùng Gemini format lại câu trả lời cho thân thiện
        """
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY chưa được thiết lập trong .env hoặc môi trường.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.stock_agent = StockAgent()

    async def _run_llm_stream(self, prompt: str) -> str:
        """
        Gọi Gemini API (không dùng LiteLlm), lấy text từ stream.
        """
        text_out = ""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            if hasattr(response, "text") and response.text:
                text_out = response.text
            elif hasattr(response, "candidates"):
                for cand in response.candidates:
                    if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                        for p in cand.content.parts:
                            if hasattr(p, "text"):
                                text_out += p.text

        except Exception as e:
            print(f"[WARN] LLM call failed: {e}")

        return text_out.strip()

    async def handle_query(self, query: str) -> str:
        """
        Main entry: định tuyến -> gọi agent -> format -> trả về text.
        """
        # 🧭 1️⃣ Routing prompt
        routing_prompt = ORCHESTRATOR_PROMPT.format(query=query)

        try:
            routing_text = await self._run_llm_stream(routing_prompt)
        except Exception as e:
            print("[WARN] LLM routing failed:", e)
            routing_text = ""

        # ✅ 2️⃣ Xác định intent
        rd = routing_text.strip().lower()
        if "advice" in rd or "tư vấn" in rd or "khuyến nghị" in rd:
            intent = "advice_query"
        elif "price" in rd or "giá" in rd or "price_query" in rd:
            intent = "price_query"
        else:
            lower = query.lower()
            if any(k in lower for k in ["giá", "hôm nay", "hôm qua", "bao nhiêu", "tăng", "giảm"]):
                intent = "price_query"
            elif any(k in lower for k in ["có nên", "mua", "bán", "phân tích", "đầu tư", "dự đoán"]):
                intent = "advice_query"
            else:
                intent = "chat"

        # ⚙️ 3️⃣ Gọi agent tương ứng
        if intent == "price_query":
            response = self.stock_agent.handle_request(query)
        elif intent == "advice_query":
            response = analyze_stock(query)
        else:
            response = (
                "🤖 Xin chào! Mình là trợ lý tài chính. "
                "Bạn có thể hỏi mình về giá cổ phiếu hoặc nên mua/bán mã nào nhé!"
            )

        # 💬 4️⃣ Format lại kết quả
        final_prompt = f"""
Dưới đây là phản hồi từ hệ thống tài chính:
---
{response}
---
Hãy diễn giải lại bằng tiếng Việt ngắn gọn, thân thiện, dễ hiểu.
Thêm biểu tượng cảm xúc nếu phù hợp.
"""

        try:
            final_text = await self._run_llm_stream(final_prompt)
        except Exception as e:
            print("[WARN] LLM formatting failed:", e)
            return str(response)

        return final_text.strip() or str(response)

# orchestrator_agent.py (phiên bản Groq-compatible)

import os
import json
import asyncio
from dotenv import load_dotenv
from typing import Optional
from openai import AsyncOpenAI

from orchestrator.prompt_templates import ORCHESTRATOR_PROMPT
from agents.stock_agent import StockAgent
from agents.advice_agent import analyze_stock
from rag.rag_engine import RagEngine
from memory.conversation_memory import ConversationMemory


class OrchestratorAgent:
    def __init__(
        self,
        model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct",
        rag_engine: Optional[RagEngine] = None,
        memory: Optional[ConversationMemory] = None,
    ):
        load_dotenv()
        self.model_name = model_name
        self.api_key = os.getenv("GROQ_API_KEY")
        self.stock_agent = StockAgent()
        self.rag_engine = rag_engine or RagEngine()
        self.memory = memory or ConversationMemory()

        if not self.api_key:
            raise ValueError("❌ Thiếu GROQ_API_KEY trong .env")

        # Groq client theo chuẩn OpenAI
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    async def _call_llm(self, prompt: str) -> str:
        """Gọi Groq API (OpenAI-compatible async call)"""
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

    async def handle_query(self, query: str, user_id: str = "default") -> str:
        # --- 1️⃣ Lưu lịch sử hội thoại
        self.memory.add_message(user_id, "user", query)

        # --- 2️⃣ Định tuyến (intent routing)
        routing_prompt = ORCHESTRATOR_PROMPT.format(query=query)
        try:
            routing_text = await self._call_llm(routing_prompt)
        except Exception:
            routing_text = ""

        rd = (routing_text or "").lower()
        if any(k in rd for k in ["advice", "tư vấn", "khuyến nghị"]):
            intent = "advice_query"
        elif any(k in rd for k in ["price", "giá", "price_query"]):
            intent = "price_query"
        else:
            lower = query.lower()
            if any(k in lower for k in ["giá", "hôm nay", "hôm qua", "bao nhiêu", "tăng", "giảm"]):
                intent = "price_query"
            elif any(k in lower for k in ["có nên", "mua", "bán", "phân tích", "đầu tư", "dự đoán"]):
                intent = "advice_query"
            else:
                intent = "chat"

        # --- 3️⃣ Truy xuất context từ RAG (placeholder)
        try:
            context_text = self.rag_engine.retrieve_context(query)
            if context_text:
                print(f"📚 RAG context len: {len(context_text)} chars")
        except Exception as e:
            print("[WARN] RAG retrieval failed:", e)
            context_text = ""

        # --- 4️⃣ Gọi agent tương ứng
        if intent == "price_query":
            response = self.stock_agent.handle_request(query)
        elif intent == "advice_query":
            response = analyze_stock(query)
        else:
            response = "🤖 Xin chào! Mình là trợ lý tài chính. Bạn có thể hỏi về giá cổ phiếu hoặc tư vấn."

        # --- 5️⃣ Chuẩn bị prompt để LLM tổng hợp lại
        recent = self.memory.get_recent(user_id, n=6)
        recent_text = "\n".join([f"{m['role']}: {m['text']}" for m in recent])

        final_prompt = f"""
Ngữ cảnh RAG (nếu có):
{context_text}

Lịch sử hội thoại (gần nhất):
{recent_text}

Phản hồi hệ thống:
{response}

Hãy diễn giải lại bằng tiếng Việt, ngắn gọn, thân thiện, dùng emoji nếu phù hợp.
"""

        try:
            final_text = await self._call_llm(final_prompt)
        except Exception as e:
            print("[WARN] LLM formatting failed:", e)
            final_text = ""

        if not final_text:
            final_text = response if isinstance(response, str) else str(response)

        # --- 6️⃣ Lưu phản hồi vào memory
        self.memory.add_message(user_id, "assistant", final_text)
        return final_text

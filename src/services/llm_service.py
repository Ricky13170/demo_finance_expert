"""
LLM Service - Dịch vụ gọi API Groq để xử lý ngôn ngữ tự nhiên

Chức năng:
- Gọi API Groq để phân loại câu hỏi
- Format câu trả lời tự nhiên hơn
"""
import os
from openai import AsyncOpenAI
from config.settings import GROQ_API_KEY, DEFAULT_MODEL, GROQ_BASE_URL


class LLMService:
    """
    Service để gọi API Groq LLM
    
    Sử dụng model Llama để phân tích và trả lời câu hỏi
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Khởi tạo LLM Service
        
        Args:
            model_name: Tên model để sử dụng (mặc định: Llama 4 Scout)
        """
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY không tìm thấy trong biến môi trường!")
        
        self.model_name = model_name
        self.client = AsyncOpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL
        )
    
    async def complete(self, prompt: str, temperature: float = 0.6, max_tokens: int = 500) -> str:
        """
        Gọi API để tạo câu trả lời từ prompt
        
        Args:
            prompt: Câu hỏi hoặc prompt cần xử lý
            temperature: Độ sáng tạo (0.0-1.0), cao hơn = sáng tạo hơn
            max_tokens: Số ký tự tối đa trong câu trả lời
            
        Returns:
            Câu trả lời từ LLM (hoặc chuỗi rỗng nếu lỗi)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[WARN] Gọi LLM API thất bại: {e}")
            return ""


"""
Conversation Memory - Quản lý lịch sử hội thoại

Chức năng:
- Lưu lịch sử chat của từng user
- Lấy lịch sử gần đây để tạo context
- Tự động giới hạn số lượng tin nhắn để tránh quá tải
"""
import os
import json
from typing import List, Dict
from config.settings import MEMORY_STORAGE_PATH, MEMORY_MAX_TURNS


class ConversationMemory:
    """
    Quản lý lịch sử hội thoại - lưu vào file JSON
    
    Mỗi user có một lịch sử riêng để bot nhớ context
    """
    
    def __init__(self, storage_path: str = MEMORY_STORAGE_PATH, max_turns: int = MEMORY_MAX_TURNS):
        """
        Khởi tạo ConversationMemory
        
        Args:
            storage_path: Đường dẫn file lưu lịch sử
            max_turns: Số lượng tin nhắn tối đa lưu cho mỗi user
        """
        self.storage_path = storage_path
        self.max_turns = max_turns
        self._history = {}  # Dictionary: {user_id: [messages]}
        self._load()  # Load lịch sử từ file
    
    def _load(self):
        """Load lịch sử từ file JSON"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
            except Exception as e:
                print(f"[WARN] Không thể load lịch sử hội thoại: {e}")
                self._history = {}
    
    def _save(self):
        """Lưu lịch sử vào file JSON"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Không thể lưu lịch sử hội thoại: {e}")
    
    def add_message(self, user_id: str, role: str, text: str):
        """
        Thêm tin nhắn vào lịch sử
        
        Args:
            user_id: ID của user (ví dụ: telegram user ID)
            role: Vai trò ("user" hoặc "assistant")
            text: Nội dung tin nhắn
        """
        if user_id not in self._history:
            self._history[user_id] = []
        
        # Thêm tin nhắn mới
        self._history[user_id].append({"role": role, "text": text})
        
        # Giữ chỉ N tin nhắn gần nhất (tránh file quá lớn)
        if len(self._history[user_id]) > self.max_turns:
            self._history[user_id] = self._history[user_id][-self.max_turns:]
        
        self._save()  # Lưu vào file
    
    def get_recent(self, user_id: str, n: int = 6) -> List[Dict]:
        """
        Lấy N tin nhắn gần nhất của user
        
        Args:
            user_id: ID của user
            n: Số lượng tin nhắn cần lấy
            
        Returns:
            Danh sách tin nhắn gần nhất
        """
        if user_id not in self._history:
            return []
        return self._history[user_id][-n:]
    
    def clear_history(self, user_id: str):
        """Xóa lịch sử của một user"""
        if user_id in self._history:
            del self._history[user_id]
            self._save()
    
    def get_all(self) -> Dict:
        """Lấy toàn bộ lịch sử (dùng để debug)"""
        return self._history.copy()

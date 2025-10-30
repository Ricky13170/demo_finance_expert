import os
import json
from typing import List, Dict

DEFAULT_HISTORY_FILE = "conversation_history.json"

class ConversationMemory:
    """
    Simple file-backed conversation memory for multi-user.
    - history structure: { user_id: [ {role: "user"/"assistant"/"system", "text": "...", "ts": 123456}, ... ] }
    """

    def __init__(self, storage_path: str = DEFAULT_HISTORY_FILE, max_turns: int = 20):
        self.storage_path = storage_path
        self.max_turns = max_turns
        self._history = {}
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
            except Exception:
                self._history = {}

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print("[WARN] ConversationMemory save failed:", e)

    def add_message(self, user_id: str, role: str, text: str, ts: float = None):
        if user_id not in self._history:
            self._history[user_id] = []
        entry = {"role": role, "text": text}
        if ts is not None:
            entry["ts"] = ts
        self._history[user_id].append(entry)
        # keep last N turns
        if len(self._history[user_id]) > self.max_turns:
            self._history[user_id] = self._history[user_id][-self.max_turns :]
        self._save()

    def get_recent(self, user_id: str, n: int = 6) -> List[Dict]:
        if user_id not in self._history:
            return []
        return self._history[user_id][-n:]

    def clear_history(self, user_id: str):
        if user_id in self._history:
            del self._history[user_id]
            self._save()

    def dump_all(self) -> Dict:
        return self._history.copy()

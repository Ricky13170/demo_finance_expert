# main.py
import asyncio
from orchestrator.orchestrator_agent import OrchestratorAgent
from rag.rag_engine import RagEngine
from memory.conversation_memory import ConversationMemory

async def main():
    rag = RagEngine(data_dir="data")
    memory = ConversationMemory()
    orchestrator = OrchestratorAgent(rag_engine=rag, memory=memory)

    print("🤖 Trợ lý tài chính (local mode). Gõ 'exit' để thoát.")
    while True:
        q = input("Nhập câu hỏi: ").strip()
        if q.lower() in ["exit", "quit"]:
            break
        resp = await orchestrator.handle_query(q, user_id="me")
        print("\n💬", resp, "\n")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from orchestrator.orchestrator_agent import OrchestratorAgent

async def main():

    orchestrator = OrchestratorAgent()

    print("🤖 Trợ lý tài chính khởi động (Gemini SDK version). Gõ 'exit' để thoát.\n")

    while True:
        question = input("Nhập câu hỏi tài chính: ").strip()
        if question.lower() in ["exit", "quit"]:
            print("👋 Tạm biệt! Hẹn gặp lại.")
            break
        
        response = await orchestrator.handle_query(question)
        print("\n💬", response, "\n")

if __name__ == "__main__":
    asyncio.run(main())



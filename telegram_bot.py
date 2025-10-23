import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from orchestrator.orchestrator_agent import OrchestratorAgent
from google.adk.models.lite_llm import LiteLlm

llm = LiteLlm(model="gemini-2.0-flash")
orchestrator = OrchestratorAgent(llm)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Xin chào! Mình là Trợ lý Tài chính TSNN. Hãy hỏi mình về giá cổ phiếu hoặc tư vấn đầu tư nhé!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    response = await orchestrator.handle_query(user_message)
    await update.message.reply_text(response)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Chưa có TELEGRAM_BOT_TOKEN trong .env")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot đang chạy... Nhấn Ctrl+C để dừng.")
    app.run_polling()

if __name__ == "__main__":
    main()

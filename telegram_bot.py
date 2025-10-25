import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from orchestrator.orchestrator_agent import OrchestratorAgent


# ✅ Dùng model Groq Llama mới nhất (đã test hoạt động)
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Khởi tạo Orchestrator (đã hỗ trợ Groq API)
orchestrator = OrchestratorAgent(model_name=DEFAULT_MODEL)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Xin chào! Mình là Trợ lý Tài chính amazingtech. "
        "Bạn có thể hỏi mình về giá cổ phiếu, phân tích hoặc tư vấn đầu tư nhé!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    response = await orchestrator.handle_query(user_message, user_id=str(update.effective_user.id))
    await update.message.reply_text(response)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Chưa có TELEGRAM_BOT_TOKEN trong .env")
        return

    print(f"🚀 Bot tài chính khởi động (Groq model: {DEFAULT_MODEL})...")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()

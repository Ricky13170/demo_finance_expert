import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from orchestrator.orchestrator_agent import OrchestratorAgent

DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Xin chào! Mình là Trợ lý Tài chính amazingtech. "
        "Bạn có thể hỏi mình về giá cổ phiếu, phân tích hoặc tư vấn đầu tư nhé!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orchestrator: OrchestratorAgent = context.bot_data["orchestrator"]
    user_message = update.message.text.strip()

    response = await orchestrator.handle_query(
        user_message,
        user_id=str(update.effective_user.id)
    )

    if len(response) > 4000:
        response = response[:4000] + "\n\n[⚠️ Tin nhắn bị cắt bớt do giới hạn Telegram]"

    await update.message.reply_text(response)


def main():
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Chưa có TELEGRAM_BOT_TOKEN trong .env")
        return

    print(f"🚀 Bot tài chính khởi động (Groq model: {DEFAULT_MODEL})...")

    # Tạo app Telegram
    app = ApplicationBuilder().token(token).build()

    orchestrator = OrchestratorAgent(model_name=DEFAULT_MODEL)
    app.bot_data["orchestrator"] = orchestrator

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Bắt đầu polling (đồng bộ event loop chính xác)
    app.run_polling(stop_signals=None)


if __name__ == "__main__":
    # Fix cho Windows nếu cần
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()

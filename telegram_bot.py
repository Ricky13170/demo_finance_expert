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


def get_orchestrator(context: ContextTypes.DEFAULT_TYPE) -> OrchestratorAgent:
    """Lấy Orchestrator từ context.bot_data (nếu chưa có thì khởi tạo)."""
    if "orchestrator" not in context.bot_data:
        context.bot_data["orchestrator"] = OrchestratorAgent(model_name=DEFAULT_MODEL)
        print("✅ OrchestratorAgent đã được khởi tạo trong bot_data")
    return context.bot_data["orchestrator"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Xin chào! Mình là Trợ lý Tài chính amazingtech.\n"
        "Bạn có thể hỏi mình về giá cổ phiếu, tin tức, hoặc tư vấn đầu tư nhé! 💹"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn người dùng gửi đến bot."""
    orchestrator = get_orchestrator(context)
    user_message = update.message.text.strip()
    user_id = str(update.effective_user.id)

    try:
        response = await orchestrator.handle_query(user_message, user_id=user_id)

        if len(response) > 4000:
            response = response[:4000] + "\n\n[⚠️ Tin nhắn bị cắt bớt do giới hạn Telegram]"

        await update.message.reply_text(response)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Lỗi xử lý yêu cầu: {e}")
        print("❌ Lỗi trong handle_message:", e)


def main():
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Chưa có TELEGRAM_BOT_TOKEN trong .env")
        return

    print(f"🚀 Bot tài chính khởi động (Groq model: {DEFAULT_MODEL})...")

    app = ApplicationBuilder().token(token).build()

    # Thêm handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(stop_signals=None)


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()

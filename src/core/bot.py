"""
Telegram Bot Handler - Xử lý bot Telegram

Nhiệm vụ:
- Khởi tạo bot Telegram
- Xử lý các lệnh (/start)
- Xử lý tin nhắn từ người dùng
- Gửi câu trả lời về Telegram
"""
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
from core.orchestrator import OrchestratorAgent
from config.settings import TELEGRAM_BOT_TOKEN, DEFAULT_MODEL, MAX_MESSAGE_LENGTH


def get_orchestrator(context: ContextTypes.DEFAULT_TYPE) -> OrchestratorAgent:
    """
    Lấy OrchestratorAgent từ context (khởi tạo nếu chưa có)
    
    Lưu trong bot_data để dùng lại giữa các tin nhắn
    """
    if "orchestrator" not in context.bot_data:
        context.bot_data["orchestrator"] = OrchestratorAgent(model_name=DEFAULT_MODEL)
        print("OrchestratorAgent initialized in bot_data")
    return context.bot_data["orchestrator"]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Xử lý lệnh /start - Khi người dùng bắt đầu chat với bot
    """
    await update.message.reply_text(
        "Xin chào! Tôi là Trợ lý Tài chính.\n"
        "Bạn có thể hỏi tôi về giá cổ phiếu, tin tức, hoặc tư vấn đầu tư."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Xử lý tin nhắn từ người dùng - Hàm chính
    
    Quy trình:
    1. Lấy orchestrator từ context
    2. Lấy tin nhắn từ người dùng
    3. Gửi đến orchestrator để xử lý
    4. Gửi câu trả lời về Telegram
    """
    orchestrator = get_orchestrator(context)
    user_message = update.message.text.strip()
    user_id = str(update.effective_user.id)  # ID của user trên Telegram
    
    try:
        # Xử lý câu hỏi và lấy câu trả lời
        response = await orchestrator.handle_query(user_message, user_id=user_id)
        
        # Cắt ngắn nếu vượt quá giới hạn của Telegram (4096 ký tự)
        if len(response) > MAX_MESSAGE_LENGTH:
            response = response[:MAX_MESSAGE_LENGTH] + "\n\n[Tin nhắn bị cắt do giới hạn Telegram]"
        
        # Gửi câu trả lời về Telegram
        await update.message.reply_text(response)
    
    except Exception as e:
        # Xử lý lỗi nếu có
        await update.message.reply_text(f"Lỗi khi xử lý yêu cầu: {e}")
        print(f"Error in handle_message: {e}")


def create_bot():
    """
    Tạo và cấu hình Telegram bot application
    
    Returns:
        Application instance đã được cấu hình
    """
    # Kiểm tra token
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_token_here" or "your_telegram_bot" in TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN không tìm thấy hoặc không hợp lệ.\n"
            "Vui lòng tạo file .env với Telegram Bot Token hợp lệ.\n"
            "Lấy token từ @BotFather trên Telegram."
        )
    
    print(f"Bot đang khởi động (Groq model: {DEFAULT_MODEL})...")
    
    # Tạo bot application
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Thêm các handler
    app.add_handler(CommandHandler("start", start_command))  # Xử lý lệnh /start
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Xử lý tin nhắn text
    
    return app


def main():
    """
    Hàm chính để chạy bot Telegram
    
    Bot sẽ chạy và lắng nghe tin nhắn từ Telegram
    """
    app = create_bot()
    app.run_polling(stop_signals=None)  # Chạy bot và chờ tin nhắn


if __name__ == "__main__":
    # Sửa lỗi event loop trên Windows
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()


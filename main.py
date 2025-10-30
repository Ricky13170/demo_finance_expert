"""
File chính để chạy bot - Main entry point

Cách chạy:
1. Chạy Telegram bot: python main.py
2. Chạy CLI để test: python main.py --cli
3. Xem hướng dẫn: python main.py --help
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

# Tắt telemetry của ChromaDB TRƯỚC KHI import bất kỳ module nào
os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

# Thêm thư mục src vào Python path để có thể import các module
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))


async def cli_mode():
    """
    Chế độ CLI - Chạy bot qua terminal để test
    
    Sử dụng khi muốn test bot mà không cần Telegram
    """
    # Import các module cần thiết
    from core.orchestrator import OrchestratorAgent
    from config.settings import DEFAULT_MODEL
    
    # Hiển thị thông tin chào mừng
    print("=" * 60)
    print("Finance Expert Bot - CLI Mode")
    print("=" * 60)
    print("Gõ câu hỏi về cổ phiếu, tin tức, hoặc tư vấn đầu tư.")
    print("Gõ 'exit' hoặc 'quit' để thoát.\n")
    
    # Khởi tạo orchestrator - thành phần chính xử lý câu hỏi
    orchestrator = OrchestratorAgent(model_name=DEFAULT_MODEL)
    
    # Vòng lặp chính - nhận câu hỏi và trả lời
    while True:
        try:
            # Nhận câu hỏi từ người dùng
            query = input("\nBạn: ").strip()
            
            # Bỏ qua nếu không có câu hỏi
            if not query:
                continue
            
            # Thoát nếu người dùng gõ exit
            if query.lower() in ['exit', 'quit', 'q', 'thoat']:
                print("\nTạm biệt!")
                break
            
            # Xử lý câu hỏi và in câu trả lời
            print("\nBot: ", end="", flush=True)
            response = await orchestrator.handle_query(query, user_id="cli_user")
            print(response)
            
        except KeyboardInterrupt:
            # Xử lý khi người dùng nhấn Ctrl+C
            print("\n\nTạm biệt!")
            break
        except Exception as e:
            # In lỗi nếu có
            print(f"\nLỗi: {e}")


def main():
    """
    Hàm chính - Xử lý lựa chọn chế độ chạy
    
    Có 2 chế độ:
    - telegram: Chạy bot trên Telegram (mặc định)
    - cli: Chạy bot qua terminal để test
    """
    # Tạo parser để đọc tham số dòng lệnh
    parser = argparse.ArgumentParser(
        description="Finance Expert Bot - Telegram hoặc CLI mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python main.py              # Chạy Telegram bot (mặc định)
  python main.py --telegram   # Chạy Telegram bot
  python main.py --cli        # Chạy CLI mode để test
        """
    )
    
    # Thêm các tham số dòng lệnh
    parser.add_argument(
        '--mode',
        choices=['telegram', 'cli'],
        default='telegram',
        help='Chế độ chạy: telegram (mặc định) hoặc cli'
    )
    
    parser.add_argument(
        '--telegram',
        action='store_true',
        help='Chạy Telegram bot (chế độ mặc định)'
    )
    
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Chạy CLI mode để test'
    )
    
    # Đọc tham số từ dòng lệnh
    args = parser.parse_args()
    
    # Xác định chế độ chạy
    if args.cli:
        mode = 'cli'
    elif args.telegram:
        mode = 'telegram'
    else:
        mode = args.mode
    
    # Sửa lỗi event loop trên Windows
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Chạy theo chế độ đã chọn
    if mode == 'cli':
        asyncio.run(cli_mode())
    else:
        telegram_mode()


def telegram_mode():
    """
    Chế độ Telegram - Chạy bot trên Telegram
    
    Yêu cầu có file .env với TELEGRAM_BOT_TOKEN
    """
    try:
        # Import bot Telegram (chỉ khi cần)
        from core.bot import main as telegram_main
        telegram_main()
    except ImportError as e:
        # Hiển thị lỗi nếu thiếu package
        print(f"[ERROR] Chế độ Telegram cần package python-telegram-bot.")
        print(f"[ERROR] Cài đặt bằng: pip install python-telegram-bot")
        print(f"[ERROR] Hoặc dùng CLI mode: python main.py --cli")
        sys.exit(1)


if __name__ == "__main__":
    main()

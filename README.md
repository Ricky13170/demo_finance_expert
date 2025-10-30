# Finance Expert Bot - Bot Telegram Tài Chính

Bot Telegram thông minh giúp tra cứu giá cổ phiếu, phân tích đầu tư và tin tức tài chính Việt Nam.

## Tính năng

- Tra cứu giá cổ phiếu real-time của các mã cổ phiếu VN
- Phân tích đầu tư tự động dựa trên dữ liệu thị trường
- Tìm kiếm và tóm tắt tin tức tài chính từ CafeF
- Lưu trữ lịch sử hội thoại để nhớ context
- Tìm kiếm tin tức thông minh bằng RAG (semantic search)

## Tech Stack

- Python 3.11
- python-telegram-bot - Framework Telegram Bot
- Groq API - LLM inference (Llama 4 Scout 17B)
- ChromaDB - Vector database cho semantic search
- vnstock - Thư viện lấy dữ liệu chứng khoán VN
- Docker - Containerization (tùy chọn)

## Yêu cầu

- Python 3.10+ hoặc Docker Desktop
- Telegram Bot Token từ [@BotFather](https://t.me/BotFather)
- Groq API Key từ [groq.com](https://groq.com)

## Cài đặt và Chạy

### Cách 1: Chạy bằng Python (Đơn giản nhất)

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Tạo file .env
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
echo "GROQ_API_KEY=your_key_here" >> .env

# Chạy bot
python main.py              # Chạy Telegram bot
python main.py --cli        # Test bằng CLI (không cần Telegram)
```

### Cách 2: Chạy với uv (Nhanh hơn)

```bash
# Cài đặt dependencies
uv pip install -r requirements.txt

# Tạo file .env và chạy
python main.py
```

### Cách 3: Chạy với Docker

**Lưu ý:** Cần Docker Desktop đang chạy!

```bash
# Tạo file .env ở thư mục gốc
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
echo "GROQ_API_KEY=your_key_here" >> .env

# Build và chạy bot
docker-compose -f deployment/docker-compose.yml up -d

# Xem logs
docker-compose -f deployment/docker-compose.yml logs -f

# Dừng bot
docker-compose -f deployment/docker-compose.yml down
```

**Hoặc vào thư mục deployment:**
```bash
cd deployment
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Cấu trúc Project

```
demo_finance_expert/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── .env                       # API keys (tạo file này)
│
├── src/                       # Source code
│   ├── agents/               # Các agent chuyên biệt
│   │   ├── stock_agent.py    # Tra cứu giá cổ phiếu
│   │   ├── news_agent.py     # Tìm tin tức
│   │   └── advice_agent.py  # Phân tích đầu tư
│   │
│   ├── core/                 # Core logic
│   │   ├── orchestrator.py   # Điều phối viên chính
│   │   └── bot.py            # Handler Telegram bot
│   │
│   ├── data/                 # Data layer
│   │   ├── memory.py         # Lưu lịch sử chat
│   │   └── vector_db.py       # ChromaDB cho RAG
│   │
│   ├── services/             # Services
│   │   └── llm_service.py    # Gọi API Groq
│   │
│   ├── tools/                # Tools
│   │   └── rag_tool.py       # RAG tool
│   │
│   └── config/               # Configuration
│       └── settings.py       # Cấu hình
│
└── deployment/               # Docker files
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md
```

## Test Bot

### Test bằng CLI (không cần Telegram)

```bash
python main.py --cli
```

Sau đó gõ các câu hỏi như:
- "Giá cổ phiếu FPT hôm nay bao nhiêu?"
- "Có nên mua VCB không?"
- "Tin tức về MWG"

### Test trên Telegram

1. Tạo bot với [@BotFather](https://t.me/BotFather) trên Telegram
2. Lấy token và điền vào `.env`
3. Chạy `python main.py`
4. Tìm bot trên Telegram và chat thử

Xem file `questions.txt` để có danh sách câu hỏi mẫu.

## Cấu hình

Chỉnh sửa `src/config/settings.py` để tùy chỉnh:

- Model LLM: Đổi model Groq nếu muốn
- RAG: Cấu hình database vector
- Mã cổ phiếu: Thêm/bớt mã theo dõi

## Troubleshooting

### Lỗi thiếu dependencies

```bash
pip install -r requirements.txt
# hoặc
uv pip install -r requirements.txt
```

### Lỗi thiếu API key

Kiểm tra file `.env` có đầy đủ:
- `TELEGRAM_BOT_TOKEN` - Token từ @BotFather
- `GROQ_API_KEY` - Key từ groq.com

### Bot không phản hồi

```bash
# Xem logs
python main.py              # Chạy và xem lỗi trong terminal
docker-compose -f deployment/docker-compose.yml logs -f  # Nếu dùng Docker
```

### Lỗi Docker

- "cannot find file specified" → Khởi động Docker Desktop trước
- "No such file or directory" → Kiểm tra file `.env` có tồn tại không
- Build timeout → Chạy lại, Docker sẽ tiếp tục từ package đã tải

## License

MIT

"""Configuration settings for the application."""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# LLM Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# RAG Configuration
RAG_PERSIST_DIRECTORY = "./chroma_db"
RAG_COLLECTION_NAME = "finance_news"
RAG_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Memory Configuration
MEMORY_STORAGE_PATH = "conversation_history.json"
MEMORY_MAX_TURNS = 20

# News Agent Configuration
DEFAULT_STOCK_SYMBOLS = ["FPT", "VCB", "VNM", "MWG", "HPG", "VIN"]
MAX_ARTICLES_PER_SOURCE = 5

# Telegram Message Limits
MAX_MESSAGE_LENGTH = 4000


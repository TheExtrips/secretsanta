import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env из корневой директории проекта
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not found. Please check your .env file")
    raise ValueError("BOT_TOKEN environment variable is required")

DATABASE_URL = "sqlite:///./secret_santa.db"
DATA_RETENTION_DAYS = 2

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print(f"✅ BOT_TOKEN loaded successfully: {BOT_TOKEN[:10]}...")
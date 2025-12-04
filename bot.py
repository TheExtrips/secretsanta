import logging
import os
from datetime import datetime
from telegram.ext import Application

from app.config import BOT_TOKEN
from app.models.database import Base, engine
from app.handlers.start import setup_handlers as setup_start_handlers
from app.handlers.rooms import setup_handlers as setup_rooms_handlers
from app.handlers.wishlist import setup_handlers as setup_wishlist_handlers
from app.handlers.messages import setup_handlers as setup_messages_handlers

# Настройка логирования
# Создаем директории для логов
logs_dir = 'data/logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Логи в файл внутри папки data/logs
        logging.FileHandler(f'{logs_dir}/bot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    try:
        # Убедимся, что папка data существует
        if not os.path.exists('data'):
            os.makedirs('data', exist_ok=True)
            logger.info("Created 'data' directory")

        # Создание таблиц
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Создание приложения
        application = Application.builder().token(BOT_TOKEN).build()
        logger.info("Bot application created")

        # Настройка обработчиков
        setup_start_handlers(application)
        setup_rooms_handlers(application)
        setup_wishlist_handlers(application)
        setup_messages_handlers(application)  # Должен быть ПОСЛЕДНИМ!
        logger.info("All handlers setup completed")

        # Запуск бота
        logger.info("Starting bot polling...")
        application.run_polling()

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == '__main__':
    main()
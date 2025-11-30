import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.user_service import get_or_create_user
from app.utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db: Session = next(get_db())
        user = get_or_create_user(
            db,
            update.effective_user.id,
            update.effective_user.full_name,
            update.effective_user.username
        )

        text = "🎄 *Добро пожаловать в Тайного Санту!* 🎅\n\nВыберите действие:"
        reply_markup = main_menu_keyboard()

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info(f"User {user.id} started the bot")

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🎅 *Помощь по командам:*

/start - Главное меню
/help - Эта справка
/cancel - Отмена текущей операции

*Основные функции:*
• 🎯 *Мои комнаты* - просмотр комнат, в которых вы участвуете
• ➕ *Создать комнату* - создать новую игру Тайного Санты
• 🎁 *Мой вишлист* - управление вашим списком пожеланий
• 🎄 *Присоединиться к комнате* - вступить в игру по ID комнаты

*Как играть:*
1. Создайте комнату или присоединитесь к существующей
2. Заполните свой вишлист
3. Дождитесь начала игры администратором
4. Получите имя своего получателя и его вишлист!

🎄 *Удачной игры!*
    """
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(help_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(help_text, parse_mode='Markdown')


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Принудительно сбрасываем все состояния
    context.user_data.clear()

    text = "🎄 *Главное меню Тайного Санты* 🎅\n\nВыберите действие:"
    reply_markup = main_menu_keyboard()

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для отмены текущей операции"""
    context.user_data.clear()

    text = "✅ Все операции отменены. Возврат в главное меню."
    reply_markup = main_menu_keyboard()

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))  # ← ДОБАВЛЯЕМ ЭТУ СТРОКУ
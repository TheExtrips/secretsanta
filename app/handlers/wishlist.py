import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.user_service import get_or_create_user
from app.services.wishlist_service import get_or_create_wishlist, update_wishlist
from app.utils.keyboards import wishlist_keyboard, back_to_main_keyboard
from app.utils.formatters import format_wishlist
from app.utils.telegram_formatter import TelegramFormatter

logger = logging.getLogger(__name__)


async def my_wishlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        logger.info(f"User {update.effective_user.id} requested wishlist")
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        wishlist = get_or_create_wishlist(db, user.id)
        text = format_wishlist(wishlist.content)
        reply_markup = wishlist_keyboard()

        # Используем HTML парсинг для надежности
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        logger.info(f"Wishlist displayed for user {user.id}")

    except Exception as e:
        logger.error(f"Error in my_wishlist: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке вишлиста.")


async def edit_wishlist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        logger.info(f"User {update.effective_user.id} started editing wishlist")

        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        wishlist = get_or_create_wishlist(db, user.id)
        current_content = wishlist.content or ""

        # Безопасно отображаем текущий контент
        safe_current_content = TelegramFormatter.safe_text(current_content, 'HTML')

        # Устанавливаем состояние редактирования вишлиста
        context.user_data['editing_wishlist'] = True
        logger.info(f"Set editing_wishlist state for user {update.effective_user.id}")

        text = f"""✏️ <b>Редактирование вишлиста</b>

Текущий вишлист:
{safe_current_content}

Отправьте новый текст вишлиста (поддерживаются ссылки):"""
        reply_markup = back_to_main_keyboard()

        # Используем HTML парсинг
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        logger.info(f"Edit wishlist interface shown for user {update.effective_user.id}")

    except Exception as e:
        logger.error(f"Error in edit_wishlist_start: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def edit_wishlist_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сохранения вишлиста"""
    new_content = update.message.text
    logger.info(f"User {update.effective_user.id} saving wishlist: {new_content[:50]}...")

    try:
        db: Session = next(get_db())
        user = get_or_create_user(db, update.effective_user.id, update.effective_user.full_name,
                                  update.effective_user.username)

        logger.info(f"Updating wishlist for user {user.id}")
        updated_wishlist = update_wishlist(db, user.id, new_content)
        logger.info(f"Wishlist updated successfully for user {user.id}")

        # Сбрасываем состояние
        context.user_data.pop('editing_wishlist', None)
        logger.info(f"Cleared editing_wishlist state for user {user.id}")

        text = f"""✅ <b>Вишлист обновлен!</b>

Ваш вишлист сохранен. Теперь ваш Тайный Санта сможет увидеть ваши пожелания."""
        reply_markup = back_to_main_keyboard()

        # Используем HTML парсинг
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        logger.info(f"Success message sent to user {user.id}")

    except Exception as e:
        logger.error(f"Error in edit_wishlist_save for user {update.effective_user.id}: {e}")
        await update.message.reply_text("❌ Произошла ошибка при сохранении вишлиста.")


def setup_handlers(application):
    # Обработчики callback queries
    application.add_handler(CallbackQueryHandler(my_wishlist, pattern="^my_wishlist$"))
    application.add_handler(CallbackQueryHandler(edit_wishlist_start, pattern="^edit_wishlist$"))
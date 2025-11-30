import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.user_service import get_or_create_user
from app.services.wishlist_service import get_or_create_wishlist, update_wishlist
from app.utils.keyboards import wishlist_keyboard, back_to_main_keyboard
from app.utils.formatters import format_wishlist

logger = logging.getLogger(__name__)


async def my_wishlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        wishlist = get_or_create_wishlist(db, user.id)
        text = format_wishlist(wishlist.content)
        reply_markup = wishlist_keyboard()

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in my_wishlist: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке вишлиста.")


async def edit_wishlist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        wishlist = get_or_create_wishlist(db, user.id)
        current_content = wishlist.content or ""

        # Устанавливаем состояние редактирования вишлиста
        context.user_data['editing_wishlist'] = True

        text = f"""✏️ *Редактирование вишлиста*

Текущий вишлист:
{current_content}

Отправьте новый текст вишлиста (поддерживаются ссылки):"""
        reply_markup = back_to_main_keyboard()

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in edit_wishlist_start: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def edit_wishlist_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, находимся ли мы в состоянии редактирования вишлиста
    if not context.user_data.get('editing_wishlist'):
        return

    new_content = update.message.text

    try:
        db: Session = next(get_db())
        user = get_or_create_user(db, update.effective_user.id, update.effective_user.full_name,
                                  update.effective_user.username)

        update_wishlist(db, user.id, new_content)

        # Сбрасываем состояние
        context.user_data.pop('editing_wishlist', None)

        text = f"""✅ *Вишлист обновлен!*

Ваш вишлист сохранен. Теперь ваш Тайный Санта сможет увидеть ваши пожелания."""
        reply_markup = back_to_main_keyboard()

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in edit_wishlist_save: {e}")
        await update.message.reply_text("❌ Произошла ошибка при сохранении вишлиста.")


async def handle_wishlist_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для вишлиста"""
    if context.user_data.get('editing_wishlist'):
        await edit_wishlist_save(update, context)


def setup_handlers(application):
    application.add_handler(CallbackQueryHandler(my_wishlist, pattern="^my_wishlist$"))
    application.add_handler(CallbackQueryHandler(edit_wishlist_start, pattern="^edit_wishlist$"))

    # Обработчик сообщений для вишлиста
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wishlist_messages))
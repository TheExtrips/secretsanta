import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

logger = logging.getLogger(__name__)


async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик всех текстовых сообщений"""
    logger.info(f"Main message handler received message from user {update.effective_user.id}")
    logger.info(f"User data state: {context.user_data}")

    # Проверяем состояния в порядке приоритета

    # 1. Обработка вишлиста (высший приоритет)
    if context.user_data.get('editing_wishlist'):
        logger.info("Processing as wishlist edit")
        from .wishlist import edit_wishlist_save
        await edit_wishlist_save(update, context)
        return

    # 2. Обработка подтверждения удаления комнаты
    if context.user_data.get('deleting_room_id'):
        logger.info("Processing as room deletion confirmation")
        from .rooms import delete_room_confirm
        await delete_room_confirm(update, context)
        return

    # 3. Обработка подтверждения выхода из комнаты ← ДОБАВЛЯЕМ
    if context.user_data.get('leaving_room_id'):
        logger.info("Processing as room leave confirmation")
        from .rooms import leave_room_confirm
        await leave_room_confirm(update, context)
        return

    # 4. Обработка редактирования описания комнаты
    if context.user_data.get('editing_description'):
        logger.info("Processing as room description edit")
        from .rooms import edit_description_save
        await edit_description_save(update, context)
        return

    # 5. Обработка создания комнаты
    if context.user_data.get('awaiting_room_name'):
        logger.info("Processing as room creation")
        from .rooms import create_room_name
        await create_room_name(update, context)
        return

    # 6. Обработка присоединения к комнате
    if context.user_data.get('awaiting_room_id'):
        logger.info("Processing as room join")
        from .rooms import join_room_id
        await join_room_id(update, context)
        return

    # 7. Если нет активных состояний, игнорируем сообщение
    logger.info("No active states, ignoring message")


def setup_handlers(application):
    # Один главный обработчик для всех текстовых сообщений
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_all_messages
    ))
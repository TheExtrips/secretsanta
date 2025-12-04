import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton  # ← ДОБАВЛЯЕМ ИМПОРТЫ
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.participant import Participant
from app.models.user import User
from app.services.user_service import get_or_create_user
from app.services.room_service import (
    create_room, get_user_rooms, get_room_by_id,
    get_room_participants, shuffle_room, is_user_admin,
    add_participant, update_room_description, remove_participant,
    delete_room, leave_room, delete_empty_room
)
from app.services.wishlist_service import get_wishlist_by_user_id
from app.services.assignment_service import get_assignment_for_santa
from app.utils.keyboards import (
    rooms_list_keyboard, room_management_keyboard,
    participants_keyboard, back_to_main_keyboard, main_menu_keyboard
)
from app.utils.formatters import format_room_info, format_participants_list
from app.utils.telegram_formatter import TelegramFormatter

logger = logging.getLogger(__name__)


async def edit_description_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало редактирования описания комнаты"""
    query = update.callback_query
    await query.answer()

    try:
        room_id = int(query.data.split('_')[2])
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        # Проверяем права администратора
        if not is_user_admin(db, user.id, room_id):
            await query.edit_message_text("❌ Только администратор может изменять описание.")
            return

        room = get_room_by_id(db, room_id)
        if not room:
            await query.edit_message_text("❌ Комната не найдена.")
            return

        # Сохраняем ID комнаты для использования при сохранении
        context.user_data['editing_room_id'] = room_id
        context.user_data['editing_description'] = True

        current_description = room.description or "Описание пока не добавлено"

        text = f"""✏️ *Редактирование описания комнаты*

Текущее описание:
{current_description}

Введите новое описание:"""
        reply_markup = back_to_main_keyboard()

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in edit_description_start: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def edit_description_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение нового описания комнаты"""
    try:
        room_id = context.user_data.get('editing_room_id')
        if not room_id:
            await update.message.reply_text("❌ Ошибка: не найден ID комнаты.")
            return

        new_description = update.message.text

        db: Session = next(get_db())
        user = get_or_create_user(db, update.effective_user.id, update.effective_user.full_name,
                                  update.effective_user.username)

        # Проверяем права администратора
        if not is_user_admin(db, user.id, room_id):
            await update.message.reply_text("❌ Только администратор может изменять описание.")
            return

        # Обновляем описание
        room = update_room_description(db, room_id, new_description)

        if not room:
            await update.message.reply_text("❌ Комната не найдена.")
            return

        # Очищаем состояние
        context.user_data.pop('editing_room_id', None)
        context.user_data.pop('editing_description', None)

        # Безопасно обрабатываем данные
        safe_room_name = TelegramFormatter.safe_text(room.name, 'HTML')
        safe_new_description = TelegramFormatter.safe_text(new_description, 'HTML')

        text = f"""✅ <b>Описание обновлено!</b>

Новое описание комнаты '{safe_room_name}':
{safe_new_description}"""
        reply_markup = back_to_main_keyboard()

        # Используем HTML парсинг
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in edit_description_save: {e}")
        await update.message.reply_text("❌ Произошла ошибка при сохранении описания.")

async def my_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)
        rooms = get_user_rooms(db, user.id)

        if not rooms:
            text = "🎄 *Ваши комнаты*\n\nУ вас пока нет активных комнат. Создайте новую или присоединитесь к существующей!"
            reply_markup = back_to_main_keyboard()
        else:
            text = "🎄 *Ваши комнаты*\n\nВыберите комнату для управления:"
            reply_markup = rooms_list_keyboard(rooms, user.id)  # ← Передаем ID пользователя

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in my_rooms: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке комнат.")


async def room_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        room_id = int(query.data.split('_')[1])
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        room = get_room_by_id(db, room_id)
        if not room:
            await query.edit_message_text("❌ Комната не найдена.")
            return

        participants = get_room_participants(db, room_id)
        is_admin_user = is_user_admin(db, user.id, room_id)
        game_started = room.status.value == "closed"

        text = format_room_info(room, participants, is_admin_user, game_started)
        reply_markup = room_management_keyboard(room_id, is_admin_user, game_started)

        # Используем HTML парсинг
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in room_detail: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке комнаты.")

async def create_room_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Сохраняем состояние в user_data
    context.user_data['awaiting_room_name'] = True
    context.user_data['awaiting_room_id'] = False  # Сбрасываем другое состояние

    text = "🎄 *Создание новой комнаты*\n\nВведите название для новой комнаты:\n\n(Для отмены нажмите /cancel)"
    reply_markup = back_to_main_keyboard()

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def create_room_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_room_name'):
        return

    room_name = update.message.text

    try:
        db: Session = next(get_db())
        user = get_or_create_user(db, update.effective_user.id, update.effective_user.full_name,
                                  update.effective_user.username)

        room = create_room(db, room_name, user.id)

        # Очищаем состояние
        context.user_data.pop('awaiting_room_name', None)

        # Безопасно обрабатываем название комнаты
        safe_room_name = TelegramFormatter.safe_text(room.name, 'HTML')

        text = f"""🎄 <b>Комната создана!</b>

<b>Название:</b> {safe_room_name}
<b>ID комнаты:</b> <code>{room.id}</code>

Поделитесь ID комнаты с друзьями, чтобы они могли присоединиться!"""
        reply_markup = back_to_main_keyboard()

        # Используем HTML парсинг
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in create_room_name: {e}")
        await update.message.reply_text("❌ Произошла ошибка при создании комнаты.")


async def join_room_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Сохраняем состояние в user_data
    context.user_data['awaiting_room_id'] = True
    context.user_data['awaiting_room_name'] = False  # Сбрасываем другое состояние

    text = "🎄 *Присоединение к комнате*\n\nВведите ID комнаты:\n\n(Для отмены нажмите /cancel)"
    reply_markup = back_to_main_keyboard()

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def join_room_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, ожидаем ли мы ID комнаты
    if not context.user_data.get('awaiting_room_id'):
        return

    try:
        room_id = int(update.message.text)
        db: Session = next(get_db())
        user = get_or_create_user(db, update.effective_user.id, update.effective_user.full_name,
                                  update.effective_user.username)

        room = get_room_by_id(db, room_id)
        if not room:
            await update.message.reply_text("❌ Комната с таким ID не найдена.")
            context.user_data.pop('awaiting_room_id', None)
            return

        if room.status.value == "closed":
            await update.message.reply_text("❌ Регистрация в этой комнате уже закрыта.")
            context.user_data.pop('awaiting_room_id', None)
            return

        # Проверяем, не является ли пользователь уже участником
        existing_participant = db.query(Participant).filter(
            Participant.user_id == user.id,
            Participant.room_id == room_id
        ).first()

        if existing_participant:
            await update.message.reply_text("❌ Вы уже являетесь участником этой комнаты.")
            context.user_data.pop('awaiting_room_id', None)
            return

        # Добавляем пользователя в комнату
        add_participant(db, user.id, room_id)

        # Очищаем состояние
        context.user_data.pop('awaiting_room_id', None)

        # Получаем информацию об администраторе
        admin = room.admin

        text = f"""✅ *Вы присоединились к комнате!*

*Название:* {room.name}
*Администратор:* {admin.full_name}{f" (@{admin.username})" if admin.username else ""}

Теперь вы можете настроить свой вишлист и ждать начала игры!"""
        reply_markup = back_to_main_keyboard()

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID. ID должен быть числом.")
    except Exception as e:
        logger.error(f"Error in join_room_id: {e}")
        await update.message.reply_text("❌ Произошла ошибка при присоединении к комнате.")


async def show_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        room_id = int(query.data.split('_')[1])
        db: Session = next(get_db())

        participants = get_room_participants(db, room_id)
        room = get_room_by_id(db, room_id)

        # Безопасно обрабатываем название комнаты
        safe_room_name = TelegramFormatter.safe_text(room.name, 'HTML')

        text = f"👥 <b>Участники комнаты '{safe_room_name}'</b>\n\n"
        text += format_participants_list(participants)
        reply_markup = participants_keyboard(room_id)

        # Используем HTML парсинг
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in show_participants: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке участников.")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        room_id = int(query.data.split('_')[2])
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        # Проверяем права администратора
        if not is_user_admin(db, user.id, room_id):
            await query.edit_message_text("❌ Только администратор может начать игру.")
            return

        room = get_room_by_id(db, room_id)
        participants = get_room_participants(db, room_id)

        if len(participants) < 2:
            await query.edit_message_text("❌ Для начала игры нужно как минимум 2 участника.")
            return

        # Запускаем распределение
        assignments = shuffle_room(db, room_id)

        if not assignments:
            await query.edit_message_text("❌ Не удалось начать игру. Попробуйте еще раз.")
            return

        # Отправляем сообщения всем участникам
        successful_sends = 0
        for assignment in assignments:
            receiver_wishlist = ""
            wishlist = get_wishlist_by_user_id(db, assignment.receiver_id)
            if wishlist and wishlist.content:
                receiver_wishlist = wishlist.content
            else:
                receiver_wishlist = "🎁 Вишлист пока не заполнен"

            # Безопасно обрабатываем данные
            safe_receiver_full_name = TelegramFormatter.safe_text(assignment.receiver.full_name, 'HTML')
            safe_receiver_wishlist = TelegramFormatter.safe_text(receiver_wishlist, 'HTML')

            message_text = f"""🎅 <b>Тайный Санта начался!</b>

Вы дарите подарок: <b>{safe_receiver_full_name}</b>

🎁 <b>Вишлист получателя:</b>
{safe_receiver_wishlist}

<b>Совет:</b> Вы всегда можете посмотреть эту информацию в разделе "Мои комнаты" → выберите комнату → "Кому я дарю подарок"

Удачи в выборе подарка! 🎄"""

            try:
                await context.bot.send_message(
                    chat_id=assignment.santa.telegram_id,
                    text=message_text,
                    parse_mode='HTML'
                )
                successful_sends += 1
            except Exception as e:
                logger.error(f"Error sending message to user {assignment.santa_id}: {e}")

        # Обновляем сообщение администратора
        text = f"""✅ <b>Игра начата!</b>

Участники получили свои задания. 
Успешно отправлено: {successful_sends}/{len(assignments)} уведомлений.

Теперь участники могут в любой момент посмотреть информацию о своих получателях через меню комнаты.

🎄 <b>Удачной игры!</b>"""
        reply_markup = back_to_main_keyboard()

        # Используем HTML парсинг
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in start_game: {e}")
        await query.edit_message_text("❌ Произошла ошибка при начале игры.")

async def view_receiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает пользователю, кому он дарит подарок и его вишлист"""
    query = update.callback_query
    await query.answer()

    try:
        room_id = int(query.data.split('_')[2])
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        room = get_room_by_id(db, room_id)
        if not room:
            await query.edit_message_text("❌ Комната не найдена.")
            return

        # Проверяем, что игра начата
        if room.status.value != "closed":
            await query.edit_message_text("❌ Игра еще не начата. Дождитесь начала игры администратором.")
            return

        # Получаем назначение для текущего пользователя (санты)
        assignment = get_assignment_for_santa(db, user.id, room_id)
        if not assignment:
            await query.edit_message_text("❌ Не найдено ваше назначение в этой комнате.")
            return

        # Получаем информацию о получателе и его вишлист
        receiver = assignment.receiver
        receiver_wishlist = get_wishlist_by_user_id(db, receiver.id)

        wishlist_content = receiver_wishlist.content if receiver_wishlist and receiver_wishlist.content else "🎁 Вишлист пока не заполнен"

        # Безопасно обрабатываем данные
        safe_receiver_full_name = TelegramFormatter.safe_text(receiver.full_name, 'HTML')
        safe_receiver_username = TelegramFormatter.safe_text(receiver.username, 'HTML') if receiver.username else None
        safe_wishlist_content = TelegramFormatter.safe_text(wishlist_content, 'HTML')

        # Формируем сообщение
        text = f"""🎅 <b>Ваш получатель подарка:</b>

<b>Имя:</b> {safe_receiver_full_name}
<b>Username:</b> {'@' + safe_receiver_username if safe_receiver_username else 'Не указан'}

🎁 <b>Вишлист получателя:</b>
{safe_wishlist_content}

Удачи в выборе подарка! 🎄"""

        # Отправляем сообщение с HTML парсингом
        await context.bot.send_message(
            chat_id=user.telegram_id,
            text=text,
            parse_mode='HTML'
        )

        # Обновляем исходное сообщение
        await query.edit_message_text(
            "✅ Информация о вашем получателе отправлена вам в личные сообщения! 🎅",
            reply_markup=back_to_main_keyboard()
        )

    except Exception as e:
        logger.error(f"Error in view_receiver: {e}")
        await query.edit_message_text("❌ Произошла ошибка при получении информации о получателе.")

async def delete_room_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса удаления комнаты с подтверждением"""
    query = update.callback_query
    await query.answer()

    try:
        room_id = int(query.data.split('_')[2])
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        room = get_room_by_id(db, room_id)
        if not room:
            await query.edit_message_text("❌ Комната не найдена.")
            return

        # Проверяем права администратора
        if not is_user_admin(db, user.id, room_id):
            await query.edit_message_text("❌ Только администратор может удалить комнату.")
            return

        # Проверяем, что игра уже начата (комната закрыта)
        if room.status.value != "closed":
            await query.edit_message_text("❌ Можно удалять только комнаты, в которых игра уже завершена.")
            return

        participants = get_room_participants(db, room_id)

        # Сохраняем ID комнаты для подтверждения
        context.user_data['deleting_room_id'] = room_id

        text = f"""⚠️ *Подтверждение удаления комнаты*

Вы собираетесь удалить комнату:
*{room.name}*

📊 *Статистика комнаты:*
• Участников: {len(participants)}
• Игра начата: Да
• Создана: {room.created_at.strftime('%d.%m.%Y %H:%M')}

❗ *Внимание:* Это действие нельзя отменить!
Все данные комнаты будут безвозвратно удалены.

Для подтверждения введите: *ДА, УДАЛИТЬ*"""

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Отмена", callback_data=f"room_{room_id}")]
        ])

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in delete_room_start: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def delete_room_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение и выполнение удаления комнаты"""
    try:
        room_id = context.user_data.get('deleting_room_id')
        if not room_id:
            await update.message.reply_text("❌ Ошибка: не найден ID комнаты для удаления.")
            return

        confirmation_text = update.message.text.strip().upper()

        if confirmation_text != "ДА, УДАЛИТЬ":
            await update.message.reply_text("❌ Удаление отменено. Комната не удалена.")
            context.user_data.pop('deleting_room_id', None)
            return

        db: Session = next(get_db())
        user = get_or_create_user(db, update.effective_user.id, update.effective_user.full_name,
                                  update.effective_user.username)

        # Выполняем удаление
        room = get_room_by_id(db, room_id)
        if not room:
            await update.message.reply_text("❌ Комната не найдена.")
            context.user_data.pop('deleting_room_id', None)
            return

        room_name = room.name

        success = delete_room(db, room_id, user.id)

        # Очищаем состояние
        context.user_data.pop('deleting_room_id', None)

        if success:
            text = f"""✅ *Комната удалена!*

Комната *{room_name}* была успешно удалена.

Все данные (участники, назначения, описания) были удалены безвозвратно."""
            reply_markup = back_to_main_keyboard()

            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Не удалось удалить комнату. Возможно, у вас нет прав администратора.")

    except Exception as e:
        logger.error(f"Error in delete_room_confirm: {e}")
        await update.message.reply_text("❌ Произошла ошибка при удалении комнаты.")


async def leave_room_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса выхода из комнаты с подтверждением"""
    query = update.callback_query
    await query.answer()

    try:
        room_id = int(query.data.split('_')[2])
        db: Session = next(get_db())
        user = get_or_create_user(db, query.from_user.id, query.from_user.full_name, query.from_user.username)

        room = get_room_by_id(db, room_id)
        if not room:
            await query.edit_message_text("❌ Комната не найдена.")
            return

        # Проверяем, является ли пользователь участником комнаты
        is_participant = any(p.user_id == user.id for p in room.participants)
        if not is_participant:
            await query.edit_message_text("❌ Вы не являетесь участником этой комнаты.")
            return

        is_admin = is_user_admin(db, user.id, room_id)
        game_started = room.status.value == "closed"
        participants_count = len(room.participants)

        # Сохраняем информацию для подтверждения
        context.user_data['leaving_room_id'] = room_id

        # Формируем текст подтверждения
        if is_admin:
            admin_warning = "\n⚠️ *Вы администратор этой комнаты!* Если вы выйдете, комната может быть удалена."
        else:
            admin_warning = ""

        if game_started:
            game_warning = "\n🎅 *Игра уже начата!* Выйдя из комнаты, вы не сможете получить информацию о своем получателе."
        else:
            game_warning = ""

        text = f"""🚪 *Подтверждение выхода из комнаты*

Вы собираетесь выйти из комнаты:
*{room.name}*

📊 *Информация о комнате:*
• Участников: {participants_count}
• Статус: {'Игра начата' if game_started else 'Регистрация открыта'}
• Ваша роль: {'Администратор' if is_admin else 'Участник'}{admin_warning}{game_warning}

Для подтверждения введите: *ДА, ВЫЙТИ*"""

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Отмена", callback_data=f"room_{room_id}")]
        ])

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in leave_room_start: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def leave_room_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение и выполнение выхода из комнаты"""
    try:
        room_id = context.user_data.get('leaving_room_id')
        if not room_id:
            await update.message.reply_text("❌ Ошибка: не найден ID комнаты для выхода.")
            return

        confirmation_text = update.message.text.strip().upper()

        if confirmation_text != "ДА, ВЫЙТИ":
            await update.message.reply_text("❌ Выход отменен.")
            context.user_data.pop('leaving_room_id', None)
            return

        db: Session = next(get_db())
        user = get_or_create_user(db, update.effective_user.id, update.effective_user.full_name,
                                  update.effective_user.username)

        # Получаем информацию о комнате перед выходом
        room = get_room_by_id(db, room_id)
        if not room:
            await update.message.reply_text("❌ Комната не найдена.")
            context.user_data.pop('leaving_room_id', None)
            return

        room_name = room.name
        was_admin = is_user_admin(db, user.id, room_id)

        # Выполняем выход из комнаты
        room_became_empty = leave_room(db, user.id, room_id)

        # Очищаем состояние
        context.user_data.pop('leaving_room_id', None)

        if room_became_empty:
            # Если комната стала пустой, удаляем ее
            delete_empty_room(db, room_id)
            text = f"""✅ *Вы вышли из комнаты!*

Комната *{room_name}* была удалена, так как в ней не осталось участников."""
        else:
            text = f"""✅ *Вы вышли из комнаты!*

Вы больше не являетесь участником комнаты *{room_name}*."""

            if was_admin:
                text += "\n\nℹ️ *Примечание:* Так как вы были администратором, теперь администратором стал создатель комнаты."

        reply_markup = back_to_main_keyboard()

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in leave_room_confirm: {e}")
        await update.message.reply_text("❌ Произошла ошибка при выходе из комнаты.")


async def handle_rooms_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик текстовых сообщений для комнат"""
    logger.info(f"Rooms handler received message from user {update.effective_user.id}")
    logger.info(f"Rooms user data: {context.user_data}")

    # Если активно состояние редактирования вишлиста, пропускаем сообщение
    if context.user_data.get('editing_wishlist'):
        logger.info("Message is for wishlist, skipping rooms handler")
        return

    # Проверяем состояния в user_data
    if context.user_data.get('awaiting_room_name'):
        await create_room_name(update, context)
    elif context.user_data.get('awaiting_room_id'):
        await join_room_id(update, context)
    else:
        # Если нет активных состояний, игнорируем сообщение
        logger.info("No active states in rooms handler, ignoring message")


def setup_handlers(application):
    application.add_handler(CallbackQueryHandler(my_rooms, pattern="^my_rooms$"))
    application.add_handler(CallbackQueryHandler(room_detail, pattern="^room_"))
    application.add_handler(CallbackQueryHandler(show_participants, pattern="^participants_"))
    application.add_handler(CallbackQueryHandler(start_game, pattern="^start_game_"))
    application.add_handler(CallbackQueryHandler(create_room_start, pattern="^create_room$"))
    application.add_handler(CallbackQueryHandler(join_room_start, pattern="^join_room$"))
    application.add_handler(CallbackQueryHandler(edit_description_start, pattern="^edit_desc_"))
    application.add_handler(CallbackQueryHandler(view_receiver, pattern="^view_receiver_"))
    application.add_handler(CallbackQueryHandler(delete_room_start, pattern="^delete_room_"))
    application.add_handler(CallbackQueryHandler(leave_room_start, pattern="^leave_room_"))  # ← ДОБАВЛЯЕМ
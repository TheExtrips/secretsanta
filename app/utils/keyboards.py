from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎯 Мои комнаты", callback_data="my_rooms")],
        [InlineKeyboardButton("➕ Создать комнату", callback_data="create_room")],
        [InlineKeyboardButton("🎁 Мой вишлист", callback_data="my_wishlist")],
        [InlineKeyboardButton("🎄 Присоединиться к комнате", callback_data="join_room")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]  # ← callback_data="help"
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 На главную", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


def room_management_keyboard(room_id: int, is_admin: bool = False, game_started: bool = False):
    """Клавиатура управления комнатой"""
    keyboard = []

    if game_started:
        # После начала игры показываем кнопку для просмотра получателя
        keyboard.append([InlineKeyboardButton("🎁 Кому я дарю подарок", callback_data=f"view_receiver_{room_id}")])

    if is_admin:
        if not game_started:
            # До начала игры админ видит кнопки управления
            keyboard.extend([
                [InlineKeyboardButton("✏️ Изменить описание", callback_data=f"edit_desc_{room_id}")],
                [InlineKeyboardButton("🎅 Начать игру", callback_data=f"start_game_{room_id}")],
            ])
        else:
            # После начала игры админ может удалить комнату
            keyboard.append([InlineKeyboardButton("🗑️ Удалить комнату", callback_data=f"delete_room_{room_id}")])

        keyboard.append([InlineKeyboardButton("👥 Участники", callback_data=f"participants_{room_id}")])
    else:
        if not game_started:
            # Обычные участники до начала игры видят только участников
            keyboard.append([InlineKeyboardButton("👥 Участники", callback_data=f"participants_{room_id}")])

    # Кнопка выхода из комнаты для всех участников
    keyboard.append([InlineKeyboardButton("🚪 Выйти из комнаты", callback_data=f"leave_room_{room_id}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="my_rooms")])
    return InlineKeyboardMarkup(keyboard)


def wishlist_keyboard():
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить вишлист", callback_data="edit_wishlist")],
        [InlineKeyboardButton("🔙 На главную", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def rooms_list_keyboard(rooms, current_user_id=None):
    """Создает клавиатуру списка комнат с указанием роли пользователя"""
    keyboard = []
    for room in rooms:
        # Определяем роль пользователя в комнате
        if current_user_id is not None:
            user_role = "(Админ)" if room.admin_id == current_user_id else "(Участник)"
        else:
            # Резервный вариант для обратной совместимости
            user_role = ""

        room_status = "🔴" if room.status.value == "closed" else "🟢"

        keyboard.append([InlineKeyboardButton(
            f"{room_status} {room.name} {user_role}",
            callback_data=f"room_{room.id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 На главную", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)


def participants_keyboard(room_id: int):
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=f"room_{room_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


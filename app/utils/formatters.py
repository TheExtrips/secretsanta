from .telegram_formatter import TelegramFormatter


def format_room_info(room, participants, is_admin=False, game_started=False):
    """Форматирует информацию о комнате с безопасным парсингом"""
    # Безопасно обрабатываем название и описание
    safe_room_name = TelegramFormatter.safe_text(room.name, 'HTML')
    safe_description = TelegramFormatter.safe_text(room.description,
                                                   'HTML') if room.description else 'Описание пока не добавлено'

    admin_text = " (Вы администратор)" if is_admin else ""
    status_emoji = "🔴" if room.status.value == "closed" else "🟢"

    if game_started:
        status_text = "🎅 <b>Игра начата!</b> Проверьте, кому вы дарите подарок!"
    else:
        status_text = "Регистрация открыта ✅"

    text = f"""🎄 <b>{safe_room_name}</b>{admin_text}

{status_emoji} <b>Статус:</b> {status_text}

📝 <b>Описание:</b>
{safe_description}

👥 <b>Участники:</b> {len(participants)}
"""
    return text


def format_participants_list(participants):
    """Форматирует список участников с безопасным парсингом"""
    if not participants:
        return "👥 В комнате пока нет участников"

    text = "👥 <b>Участники комнаты:</b>\n\n"
    for i, participant in enumerate(participants, 1):
        safe_name, username_display = TelegramFormatter.format_user_info(
            participant.full_name,
            participant.username
        )
        text += f"{i}. {safe_name}{username_display}\n"

    return text


def format_wishlist(wishlist_content):
    """Форматирует вишлист с безопасным парсингом"""
    if not wishlist_content:
        return "🎁 <b>Ваш вишлист пока пуст</b>\n\nНажмите 'Изменить вишлист', чтобы добавить свои пожелания!"

    safe_content = TelegramFormatter.safe_text(wishlist_content, 'HTML')

    return f"""🎁 <b>Ваш вишлист:</b>

{safe_content}

<b>Не забудьте сохранить изменения!</b>"""
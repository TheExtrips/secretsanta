def format_room_info(room, participants, is_admin=False, game_started=False):
    status_emoji = "🔴" if room.status.value == "closed" else "🟢"
    admin_text = " (Вы администратор)" if is_admin else ""

    if game_started:
        status_text = "🎅 *Игра начата!* Проверьте, кому вы дарите подарок!"
    else:
        status_text = "Регистрация открыта ✅"

    text = f"""🎄 *{room.name}*{admin_text}

{status_emoji} *Статус:* {status_text}

📝 *Описание:*
{room.description or 'Описание пока не добавлено'}

👥 *Участники:* {len(participants)}
"""
    return text


def format_participants_list(participants):
    if not participants:
        return "👥 В комнате пока нет участников"

    text = "👥 *Участники комнаты:*\n\n"
    for i, participant in enumerate(participants, 1):
        username = f" (@{participant.username})" if participant.username else ""
        text += f"{i}. {participant.full_name}{username}\n"

    return text


def format_wishlist(wishlist_content):
    if not wishlist_content:
        return "🎁 *Ваш вишлист пока пуст*\n\nНажмите 'Изменить вишлист', чтобы добавить свои пожелания!"

    return f"""🎁 *Ваш вишлист:*

{wishlist_content}

*Не забудьте сохранить изменения!*"""
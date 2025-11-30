import re

def validate_room_name(name: str) -> bool:
    """Проверяет валидность названия комнаты"""
    if not name or len(name.strip()) == 0:
        return False
    if len(name) > 100:
        return False
    return True

def validate_room_id(room_id: str) -> bool:
    """Проверяет валидность ID комнаты"""
    try:
        return int(room_id) > 0
    except (ValueError, TypeError):
        return False

def validate_wishlist_content(content: str) -> bool:
    """Проверяет валидность содержимого вишлиста"""
    if content is None:
        return True
    if len(content) > 2000:  # Ограничение длины
        return False
    return True
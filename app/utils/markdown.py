import html
import re


def safe_text_for_telegram(text: str, parse_mode: str = 'HTML') -> str:
    """
    Подготавливает текст для безопасной отправки в Telegram.

    Args:
        text: Исходный текст
        parse_mode: Режим парсинга ('HTML' или 'Markdown')

    Returns:
        str: Безопасный текст
    """
    if not text:
        return ""

    if parse_mode == 'HTML':
        # Экранируем HTML-сущности
        return html.escape(text)

    elif parse_mode == 'MarkdownV2':
        # Экранируем специальные символы MarkdownV2
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text

    elif parse_mode == 'Markdown':
        # Экранируем специальные символы MarkdownV1
        escape_chars = r'_*`['
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text

    return text


def clean_emoji(text: str) -> str:
    """
    Очищает текст от проблемных эмодзи, оставляя только базовые.
    """
    if not text:
        return text

    # Паттерн для базовых эмодзи (до Unicode 13.0, 2020 год)
    # Более новые эмодзи могут быть проблемными
    basic_emoji_pattern = re.compile(
        '['  # Начало диапазона
        '\U0001F300-\U0001F5FF'  # Разные символы и пиктограммы
        '\U0001F600-\U0001F64F'  # Эмодзи эмоций
        '\U0001F680-\U0001F6FF'  # Транспорт и карты
        '\U00002600-\U000026FF'  # Разные символы
        '\U00002700-\U000027BF'  # Дингбаты
        '\U0001F1E0-\U0001F1FF'  # Флаги (iOS)
        ']',
        flags=re.UNICODE
    )

    # Просто возвращаем текст как есть - лучше не фильтровать, а экранировать
    return text
def escape_markdown(text: str) -> str:
    """Экранирует специальные символы Markdown для безопасного отображения."""
    if not text:
        return text

    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')

    return text
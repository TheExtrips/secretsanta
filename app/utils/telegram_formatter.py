import html
import re
from typing import Optional


class TelegramFormatter:
    """Класс для безопасного форматирования текста для Telegram"""

    @staticmethod
    def escape_html(text: str) -> str:
        """Экранирует HTML-сущности"""
        if not text:
            return ""
        return html.escape(text)

    @staticmethod
    def escape_markdown_v2(text: str) -> str:
        """Экранирует специальные символы MarkdownV2"""
        if not text:
            return ""

        # Список символов, которые нужно экранировать для MarkdownV2
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')

        return text

    @staticmethod
    def escape_markdown(text: str) -> str:
        """Экранирует специальные символы Markdown (legacy)"""
        if not text:
            return ""

        # Символы для экранирования в legacy Markdown
        escape_chars = r'_*`['
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')

        return text

    @staticmethod
    def safe_text(text: str, parse_mode: Optional[str] = 'HTML') -> str:
        """
        Безопасно подготавливает текст для отправки в Telegram

        Args:
            text: Исходный текст
            parse_mode: Режим парсинга ('HTML', 'Markdown', 'MarkdownV2' или None)

        Returns:
            Безопасный текст
        """
        if not text:
            return ""

        if parse_mode == 'HTML':
            return TelegramFormatter.escape_html(text)
        elif parse_mode == 'MarkdownV2':
            return TelegramFormatter.escape_markdown_v2(text)
        elif parse_mode == 'Markdown':
            return TelegramFormatter.escape_markdown(text)
        else:
            # Если parse_mode не указан, возвращаем как есть
            return text

    @staticmethod
    def safe_message(text: str, parse_mode: Optional[str] = 'HTML') -> tuple[str, str]:
        """
        Возвращает безопасный текст и рекомендуемый parse_mode

        Returns:
            tuple: (safe_text, recommended_parse_mode)
        """
        # Для надежности используем HTML
        safe_text = TelegramFormatter.safe_text(text, 'HTML')
        return safe_text, 'HTML'

    @staticmethod
    def format_user_info(full_name: str, username: Optional[str] = None) -> tuple[str, str]:
        """
        Форматирует информацию о пользователе

        Returns:
            tuple: (safe_display_name, safe_username_for_display)
        """
        safe_name = TelegramFormatter.safe_text(full_name, 'HTML')

        if username:
            safe_username = TelegramFormatter.safe_text(username, 'HTML')
            display_username = f" (@{safe_username})"
        else:
            display_username = ""

        return safe_name, display_username
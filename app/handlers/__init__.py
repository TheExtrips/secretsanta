from .start import setup_handlers as setup_start_handlers
from .rooms import setup_handlers as setup_rooms_handlers
from .wishlist import setup_handlers as setup_wishlist_handlers
from .messages import setup_handlers as setup_messages_handlers

__all__ = [
    'setup_start_handlers',
    'setup_rooms_handlers',
    'setup_wishlist_handlers',
    'setup_messages_handlers'
]
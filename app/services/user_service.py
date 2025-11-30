from sqlalchemy.orm import Session
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

def get_or_create_user(db: Session, telegram_id: int, full_name: str, username: str = None) -> User:
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {user}")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error in get_or_create_user: {e}")
        raise
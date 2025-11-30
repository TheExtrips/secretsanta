from sqlalchemy.orm import Session
from app.models.wishlist import Wishlist
import logging

logger = logging.getLogger(__name__)


def get_or_create_wishlist(db: Session, user_id: int) -> Wishlist:
    try:
        logger.info(f"Getting or creating wishlist for user {user_id}")
        wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
        if not wishlist:
            logger.info(f"Creating new wishlist for user {user_id}")
            wishlist = Wishlist(user_id=user_id, content="")
            db.add(wishlist)
            db.commit()
            db.refresh(wishlist)
            logger.info(f"Created new wishlist with id {wishlist.id} for user {user_id}")
        else:
            logger.info(f"Found existing wishlist {wishlist.id} for user {user_id}")
        return wishlist
    except Exception as e:
        db.rollback()
        logger.error(f"Error in get_or_create_wishlist for user {user_id}: {e}")
        raise


def update_wishlist(db: Session, user_id: int, content: str) -> Wishlist:
    try:
        logger.info(f"Updating wishlist for user {user_id}")
        wishlist = get_or_create_wishlist(db, user_id)
        logger.info(f"Current wishlist content length: {len(wishlist.content) if wishlist.content else 0}")
        logger.info(f"New wishlist content length: {len(content)}")

        wishlist.content = content
        db.commit()
        db.refresh(wishlist)

        logger.info(f"Successfully updated wishlist for user {user_id}, new content: {content[:100]}...")
        return wishlist
    except Exception as e:
        db.rollback()
        logger.error(f"Error in update_wishlist for user {user_id}: {e}")
        raise


def get_wishlist_by_user_id(db: Session, user_id: int) -> Wishlist:
    logger.info(f"Getting wishlist for user {user_id}")
    return db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
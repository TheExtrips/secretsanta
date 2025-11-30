import random
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.room import Room, RoomStatus
from app.models.participant import Participant
from app.models.assignment import Assignment
from app.models.user import User

logger = logging.getLogger(__name__)


def create_room(db: Session, name: str, admin_id: int, description: str = None) -> Room:
    try:
        room = Room(name=name, admin_id=admin_id, description=description)
        db.add(room)
        db.commit()
        db.refresh(room)

        # Автоматически добавляем администратора как участника
        add_participant(db, admin_id, room.id)

        logger.info(f"Created new room: {room} with admin {admin_id}")
        return room
    except Exception as e:
        db.rollback()
        logger.error(f"Error in create_room: {e}")
        raise


def add_participant(db: Session, user_id: int, room_id: int) -> Participant:
    try:
        # Проверяем, не является ли пользователь уже участником
        existing = db.query(Participant).filter(
            and_(Participant.user_id == user_id, Participant.room_id == room_id)
        ).first()

        if existing:
            return existing

        participant = Participant(user_id=user_id, room_id=room_id)
        db.add(participant)
        db.commit()
        db.refresh(participant)
        logger.info(f"Added participant: {participant}")
        return participant
    except Exception as e:
        db.rollback()
        logger.error(f"Error in add_participant: {e}")
        raise


def get_room_by_id(db: Session, room_id: int) -> Room:
    return db.query(Room).filter(Room.id == room_id).first()


def get_user_rooms(db: Session, user_id: int) -> list[Room]:
    return db.query(Room).join(Participant).filter(Participant.user_id == user_id).all()


def get_room_participants(db: Session, room_id: int) -> list[User]:
    participants = db.query(Participant).filter(Participant.room_id == room_id).all()
    return [p.user for p in participants]


def is_user_admin(db: Session, user_id: int, room_id: int) -> bool:
    """Проверяет, является ли пользователь администратором комнаты"""
    room = db.query(Room).filter(Room.id == room_id).first()
    return room and room.admin_id == user_id

def get_room_admin(db: Session, room_id: int) -> User:
    """Получает администратора комнаты"""
    room = db.query(Room).filter(Room.id == room_id).first()
    return room.admin if room else None


def update_room_description(db: Session, room_id: int, description: str) -> Room:
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            room.description = description
            db.commit()
            db.refresh(room)
            logger.info(f"Updated room description: {room}")
        return room
    except Exception as e:
        db.rollback()
        logger.error(f"Error in update_room_description: {e}")
        raise


def remove_participant(db: Session, user_id: int, room_id: int) -> bool:
    try:
        participant = db.query(Participant).filter(
            and_(Participant.user_id == user_id, Participant.room_id == room_id)
        ).first()

        if participant:
            db.delete(participant)
            db.commit()
            logger.info(f"Removed participant: user_id={user_id}, room_id={room_id}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error in remove_participant: {e}")
        raise


def shuffle_room(db: Session, room_id: int) -> list[Assignment]:
    try:
        room = get_room_by_id(db, room_id)
        if not room or room.status == RoomStatus.CLOSED:
            return []

        participants = db.query(Participant).filter(Participant.room_id == room_id).all()
        user_ids = [p.user_id for p in participants]

        if len(user_ids) < 2:
            return []

        # Простая перетасовка с проверкой, чтобы человек не достался сам себе
        shuffled = user_ids.copy()
        random.shuffle(shuffled)

        # Если есть совпадение, перемешиваем еще раз
        max_attempts = 100
        attempts = 0
        while any(santa == receiver for santa, receiver in zip(user_ids, shuffled)) and attempts < max_attempts:
            random.shuffle(shuffled)
            attempts += 1

        if attempts == max_attempts:
            logger.error(f"Failed to shuffle room {room_id} after {max_attempts} attempts")
            return []

        assignments = []
        for santa_id, receiver_id in zip(user_ids, shuffled):
            assignment = Assignment(room_id=room_id, santa_id=santa_id, receiver_id=receiver_id)
            db.add(assignment)
            assignments.append(assignment)

        room.status = RoomStatus.CLOSED
        db.commit()

        logger.info(f"Successfully shuffled room {room_id} with {len(assignments)} assignments")
        return assignments
    except Exception as e:
        db.rollback()
        logger.error(f"Error in shuffle_room: {e}")
        raise


def delete_room(db: Session, room_id: int, user_id: int) -> bool:
    """Удаляет комнату если пользователь является администратором"""
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            logger.warning(f"Room {room_id} not found for deletion")
            return False

        # Проверяем права администратора
        if room.admin_id != user_id:
            logger.warning(f"User {user_id} is not admin of room {room_id}")
            return False

        # Удаляем комнату (каскадное удаление должно удалить связанные записи)
        db.delete(room)
        db.commit()

        logger.info(f"Room {room_id} deleted by user {user_id}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting room {room_id}: {e}")
        raise


def leave_room(db: Session, user_id: int, room_id: int) -> bool:
    """Удаляет пользователя из комнаты и возвращает True если комната пустая"""
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return False

        # Находим участника
        participant = db.query(Participant).filter(
            Participant.user_id == user_id,
            Participant.room_id == room_id
        ).first()

        if not participant:
            logger.warning(f"User {user_id} is not participant of room {room_id}")
            return False

        was_admin = room.admin_id == user_id

        # Удаляем участника
        db.delete(participant)

        # Если вышел администратор, назначаем нового администратора
        if was_admin:
            # Находим первого оставшегося участника
            new_admin = db.query(Participant).filter(
                Participant.room_id == room_id
            ).first()

            if new_admin:
                room.admin_id = new_admin.user_id
                logger.info(f"Transferred admin rights in room {room_id} to user {new_admin.user_id}")
            # Если участников не осталось, комната будет удалена

        db.commit()

        logger.info(f"User {user_id} left room {room_id}")

        # Проверяем, остались ли участники в комнате
        remaining_participants = db.query(Participant).filter(Participant.room_id == room_id).count()

        return remaining_participants == 0

    except Exception as e:
        db.rollback()
        logger.error(f"Error in leave_room: {e}")
        raise


def delete_empty_room(db: Session, room_id: int):
    """Удаляет комнату если в ней нет участников"""
    try:
        participants_count = db.query(Participant).filter(Participant.room_id == room_id).count()

        if participants_count == 0:
            room = db.query(Room).filter(Room.id == room_id).first()
            if room:
                db.delete(room)
                db.commit()
                logger.info(f"Empty room {room_id} deleted automatically")
                return True

        return False

    except Exception as e:
        db.rollback()
        logger.error(f"Error in delete_empty_room: {e}")
        raise
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.assignment import Assignment

def get_assignment_for_santa(db: Session, santa_id: int, room_id: int) -> Assignment:
    return db.query(Assignment).filter(
        and_(Assignment.santa_id == santa_id, Assignment.room_id == room_id)
    ).first()
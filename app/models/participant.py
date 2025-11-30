from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    room = relationship("Room", back_populates="participants")

    __table_args__ = (UniqueConstraint('user_id', 'room_id', name='_user_room_uc'),)

    def __repr__(self):
        return f"<Participant(user_id={self.user_id}, room_id={self.room_id})>"
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    santa_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room", back_populates="assignments")  # ← ИСПРАВЛЯЕМ НА back_populates
    santa = relationship("User", foreign_keys=[santa_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

    __table_args__ = (UniqueConstraint('room_id', 'santa_id', name='_room_santa_uc'),)

    def __repr__(self):
        return f"<Assignment(room_id={self.room_id}, santa_id={self.santa_id}, receiver_id={self.receiver_id})>"
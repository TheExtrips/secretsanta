from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum


class RoomStatus(enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("User")
    participants = relationship("Participant", back_populates="room", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="room",
                               cascade="all, delete-orphan")  # ← ДОБАВЛЯЕМ ЭТУ СТРОКУ

    def __repr__(self):
        return f"<Room(id={self.id}, name='{self.name}', status={self.status})>"
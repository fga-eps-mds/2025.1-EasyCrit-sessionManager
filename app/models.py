from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.database.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    invites = relationship("Invite", back_populates="session")

class Invite(Base):
    __tablename__ = "invites"

    token = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="invites")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


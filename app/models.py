# app/models.py

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, ForeignKey, String, Integer, Date
from sqlalchemy.orm import relationship
from .database.database import Base


class Session(Base):
  __tablename__ = 'session'
  #__table_args__ = {'schema': 'session_manager'}

  session_id = Column(Integer, primary_key=True, index=True)

  session_name = Column(String, nullable=False)
  description = Column(String)
  map_name = Column(String, nullable=False)
  start_date = Column(Date, nullable=False)
  start_time = Column(DateTime(timezone=True), nullable=False)

  invites = relationship('Invite', back_populates='session')
  user_sessions = relationship('UserSession', back_populates='session')


class Invite(Base):
  __tablename__ = 'invites'
  #__table_args__ = {'schema': 'session_manager'}

  token = Column(String, primary_key=True, default=lambda: str(uuid4()))
  session_id = Column(Integer, ForeignKey('session.session_id'), nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)

  session = relationship('Session', back_populates='invites')


class UserSession(Base):
  __tablename__ = 'user_sessions'
  #__table_args__ = {'schema': 'session_manager'}

  id = Column(String, primary_key=True, default=lambda: str(uuid4()))
  user_id = Column(String, nullable=False)
  session_id = Column(Integer, ForeignKey('session.session_id'), nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)

  session = relationship('Session', back_populates='user_sessions')

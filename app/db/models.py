"""
SQLAlchemy ORM models (database tables).
Separate from Pydantic domain models in app/models/.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RoutineModel(Base):
    """ORM model for the 'routines' table."""

    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    routine_name = Column(String, nullable=False)
    routine_data = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class ChatMessageModel(Base):
    """ORM model for the 'chat_messages' table."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    routine_id = Column(Integer, ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)

"""
Repository for chat message CRUD operations.
"""

from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.sql import select

from app.core.logging import get_logger
from app.db.session import async_session
from app.db.models import ChatMessageModel

logger = get_logger("repositories.chat")


async def save_chat_message(routine_id: int, sender: str, content: str) -> int:
    """Save a chat message linked to a routine."""
    now = datetime.now()

    async with async_session() as session:
        message = ChatMessageModel(
            routine_id=routine_id,
            sender=sender,
            content=content,
            timestamp=now,
        )
        session.add(message)
        await session.commit()
        return message.id


async def get_chat_history(routine_id: int) -> List[Dict[str, Any]]:
    """Get the full chat history for a routine, ordered chronologically."""
    async with async_session() as session:
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.routine_id == routine_id)
            .order_by(ChatMessageModel.timestamp)
        )
        result = await session.execute(stmt)
        messages = result.scalars().all()

        return [{"sender": msg.sender, "content": msg.content} for msg in messages]

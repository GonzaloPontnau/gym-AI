"""
Repository for routine CRUD operations.
Encapsulates all database access for routines.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.sql import select, delete

from app.core.logging import get_logger
from app.db.session import async_session
from app.db.models import RoutineModel
from app.models.models import Routine

logger = get_logger("repositories.routine")


async def save_routine(
    routine: Routine,
    user_id: Optional[int] = None,
    routine_id: Optional[int] = None,
) -> int:
    """
    Save or update a routine in the database.

    Args:
        routine: The routine domain model to persist.
        user_id: Owner user ID (for new routines).
        routine_id: If provided, update the existing routine with this ID.

    Returns:
        The routine ID (new or existing).
    """
    now = datetime.now()
    routine_data = routine.model_dump_json()

    async with async_session() as session:
        try:
            if routine_id:
                return await _update_routine(session, routine, routine_data, now, routine_id)
            else:
                return await _create_routine(session, routine, routine_data, now, user_id)
        except Exception as e:
            await session.rollback()
            logger.error("Failed to save routine: %s", e, exc_info=True)
            raise


async def _update_routine(session, routine, routine_data, now, routine_id):
    """Update an existing routine."""
    stmt = select(RoutineModel).where(RoutineModel.id == routine_id)
    result = await session.execute(stmt)
    routine_model = result.scalar_one_or_none()

    if not routine_model:
        raise ValueError(f"Routine with ID {routine_id} not found")

    routine_model.routine_name = routine.routine_name
    routine_model.routine_data = routine_data
    routine_model.updated_at = now
    await session.commit()
    return routine_id


async def _create_routine(session, routine, routine_data, now, user_id):
    """Create a new routine."""
    user_id = user_id or routine.user_id
    routine_model = RoutineModel(
        user_id=user_id,
        routine_name=routine.routine_name,
        routine_data=routine_data,
        created_at=now,
        updated_at=now,
    )
    session.add(routine_model)
    await session.commit()
    return routine_model.id


async def get_routine(routine_id: int) -> Optional[Routine]:
    """Get a routine by its ID."""
    async with async_session() as session:
        stmt = select(RoutineModel).where(RoutineModel.id == routine_id)
        result = await session.execute(stmt)
        routine_model = result.scalar_one_or_none()

        if routine_model:
            routine_dict = json.loads(routine_model.routine_data)
            routine_dict["id"] = routine_id
            return Routine.model_validate(routine_dict)

        return None


async def get_user_routines(user_id: int) -> List[Dict[str, Any]]:
    """Get all routines for a given user, ordered by most recent update."""
    async with async_session() as session:
        stmt = (
            select(RoutineModel)
            .where(RoutineModel.user_id == user_id)
            .order_by(RoutineModel.updated_at.desc())
        )
        result = await session.execute(stmt)
        routines = result.scalars().all()

        return [
            {"id": r.id, "routine_name": r.routine_name, "updated_at": r.updated_at}
            for r in routines
        ]


async def delete_routine(routine_id: int) -> bool:
    """Delete a routine and its associated chat messages (via CASCADE)."""
    try:
        async with async_session() as session:
            stmt = delete(RoutineModel).where(RoutineModel.id == routine_id)
            await session.execute(stmt)
            await session.commit()
            return True
    except Exception as e:
        logger.error("Failed to delete routine %d: %s", routine_id, e)
        return False

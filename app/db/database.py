"""
Backward-compatible re-exports from the new modular database layer.
Existing code that imports from app.db.database will continue to work.
"""

# Re-export everything from the new modules
from app.db.session import engine, async_session, init_db, get_db_session  # noqa: F401
from app.db.models import Base, RoutineModel, ChatMessageModel  # noqa: F401
from app.repositories.routine_repository import (  # noqa: F401
    save_routine,
    get_routine,
    get_user_routines,
    delete_routine as delete_routine_from_db,
)
from app.repositories.chat_repository import (  # noqa: F401
    save_chat_message,
    get_chat_history,
)
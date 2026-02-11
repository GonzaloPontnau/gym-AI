"""
Database session management and initialization.
"""

from sqlalchemy import inspect, text

from app.core.logging import get_logger
from app.db.engine import create_engine_and_session
from app.db.models import Base

logger = get_logger("db.session")

# Module-level singletons, initialized once
engine, async_session, is_sqlite = create_engine_and_session()


async def get_db_session():
    """Get an async database session."""
    return async_session()


async def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        async with engine.begin() as conn:
            insp = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            return await conn.run_sync(lambda sync_conn: insp.has_table(table_name))
    except Exception as e:
        logger.error("Error checking table '%s': %s", table_name, e)
        return False


async def init_db() -> None:
    """Initialize database tables if they don't exist."""
    try:
        logger.info("Checking database tables...")
        routines_ok = await table_exists("routines")
        chat_ok = await table_exists("chat_messages")

        if routines_ok and chat_ok:
            logger.info("All tables already exist — skipping creation")
            return

        logger.info("Creating database tables...")

        if not is_sqlite:
            # Direct SQL for PostgreSQL (avoids event loop issues in serverless)
            try:
                async with engine.connect() as conn:
                    if not routines_ok:
                        await conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS routines (
                                id SERIAL PRIMARY KEY,
                                user_id INTEGER NOT NULL,
                                routine_name VARCHAR NOT NULL,
                                routine_data TEXT NOT NULL,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL
                            )
                        """))
                    if not chat_ok:
                        await conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS chat_messages (
                                id SERIAL PRIMARY KEY,
                                routine_id INTEGER REFERENCES routines(id) ON DELETE CASCADE,
                                sender VARCHAR NOT NULL,
                                content TEXT NOT NULL,
                                timestamp TIMESTAMP NOT NULL
                            )
                        """))
                    await conn.commit()
                logger.info("Tables created with direct SQL (PostgreSQL)")
                return
            except Exception as e:
                logger.error("Direct SQL table creation failed: %s", e)

        # Fallback: SQLAlchemy metadata
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Tables created with SQLAlchemy metadata")

    except Exception as e:
        logger.error("Database initialization failed: %s", e, exc_info=True)
        raise

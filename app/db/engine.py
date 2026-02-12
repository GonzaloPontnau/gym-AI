"""
Database engine configuration.
Handles SQLite vs PostgreSQL selection and connection setup.
"""

import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("db.engine")


def _resolve_database_url(settings) -> tuple[str, bool]:
    """
    Determine the final database URL and whether it's SQLite.

    Returns:
        (db_url, is_sqlite)
    """
    db_url_env = settings.DATABASE_URL

    # Check asyncpg availability
    asyncpg_available = False
    try:
        import asyncpg  # noqa: F401
        asyncpg_available = True
    except ImportError:
        logger.info("asyncpg not available — falling back to SQLite")

    # Decide: PostgreSQL or SQLite
    use_postgres = (
        db_url_env
        and asyncpg_available
        and not settings.FORCE_SQLITE
        and db_url_env.startswith("postgres")
    )

    if use_postgres:
        temp_url = db_url_env.replace("postgres://", "postgresql+asyncpg://")
        parsed = urlparse(temp_url)
        params = parse_qs(parsed.query)
        params.pop("sslmode", None)
        clean_query = urlencode(params, doseq=True)
        final_url = urlunparse(parsed._replace(query=clean_query))
        logger.info("Using PostgreSQL (Neon Database)")
        return final_url, False

    # SQLite path
    if db_url_env and db_url_env.startswith("sqlite"):
        if "sqlite+aiosqlite://" not in db_url_env:
            path = db_url_env.split("sqlite:///")[-1] if "sqlite:///" in db_url_env else "gym_ai.db"
            final_url = f"sqlite+aiosqlite:///{path}"
        else:
            final_url = db_url_env
        logger.info("Using SQLite from DATABASE_URL")
    else:
        db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "gymAI.db")
        final_url = f"sqlite+aiosqlite:///{db_path}"
        logger.info("Using local SQLite for development: %s", final_url)

    return final_url, True


def create_engine_and_session():
    """
    Create and return SQLAlchemy async engine + session factory.

    Returns:
        (engine, async_session_factory, is_sqlite)
    """
    settings = get_settings()
    db_url, is_sqlite = _resolve_database_url(settings)

    if is_sqlite:
        engine = create_async_engine(db_url, echo=False)

        # SQLite does not enforce foreign keys by default.
        # This listener enables FK enforcement on every new connection,
        # so CASCADE deletes (e.g. chat messages) actually work.
        @event.listens_for(engine.sync_engine, "connect")
        def _enable_foreign_keys(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()
    else:
        engine = create_async_engine(
            db_url,
            echo=False,
            poolclass=NullPool,
            connect_args={"server_settings": {"statement_timeout": "10000"}},
        )

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return engine, session_factory, is_sqlite

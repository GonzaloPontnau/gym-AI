"""
Health check endpoint.
"""

from datetime import datetime

from fastapi import APIRouter

from app.core.logging import get_logger

logger = get_logger("routes.health")

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Application health check endpoint for monitoring / Render."""
    from app.api.dependencies import get_routine_generator
    from app.db.session import engine
    from sqlalchemy import text

    generator = get_routine_generator()

    health_status = {
        "status": "ok",
        "server_time": datetime.now().isoformat(),
        "gemini_available": generator.is_configured,
    }

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)[:100]}"

    return health_status

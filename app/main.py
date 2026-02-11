"""
GymAI — Application entry point.
Uses the app factory pattern with FastAPI lifespan events.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db
from app.api.dependencies import get_routine_generator, get_image_analyzer
from app.api.routes import health, pages, routines
from app.websocket.manager import ConnectionManager
from app.websocket.routes import WebSocketRoutes

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — replaces deprecated @app.on_event."""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)

    logger.info("Starting GymAI...")

    if not settings.is_vercel:
        try:
            await init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.error("Database initialization failed: %s", e, exc_info=True)
            logger.warning("Application will continue without initialized database")
    else:
        logger.info("Skipping DB init (Vercel environment)")

    generator = get_routine_generator()
    logger.info("Gemini available: %s", generator.is_configured)

    yield  # Application runs here

    logger.info("GymAI shutting down")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    application = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
    )

    # --- Middleware ---
    origins = (
        [o.strip() for o in settings.CORS_ORIGINS.split(",")]
        if settings.CORS_ORIGINS != "*"
        else ["*"]
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.CORS_ORIGINS != "*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Static files ---
    if not settings.is_vercel and os.path.exists("static"):
        application.mount("/static", StaticFiles(directory="static"), name="static")

    # --- Routers ---
    application.include_router(health.router)
    application.include_router(pages.router)
    application.include_router(routines.router)
    application.include_router(routines.delete_router)

    # --- WebSocket ---
    manager = ConnectionManager()
    ws_routes = WebSocketRoutes(
        manager=manager,
        routine_generator=get_routine_generator(),
        image_analyzer=get_image_analyzer(),
    )

    @application.websocket("/ws/chat/{routine_id}")
    async def websocket_endpoint(websocket: WebSocket, routine_id: int):
        await ws_routes.handle_websocket(websocket, routine_id)

    return application


# Module-level instance for uvicorn
app = create_app()
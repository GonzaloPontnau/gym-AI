"""
WebSocket route handlers for real-time chat.
Uses repository layer and DI for services.
"""

import json

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.websocket.manager import ConnectionManager
from app.services.gemini_service import GeminiRoutineGenerator
from app.services.image_analysis_service import GeminiImageAnalyzer
from app.repositories import routine_repository, chat_repository

logger = get_logger("websocket.routes")


class WebSocketRoutes:
    """Handles WebSocket connections for routine chat."""

    def __init__(
        self,
        manager: ConnectionManager,
        routine_generator: GeminiRoutineGenerator,
        image_analyzer: GeminiImageAnalyzer,
    ):
        self.manager = manager
        self.routine_generator = routine_generator
        self.image_analyzer = image_analyzer

    async def handle_websocket(self, websocket: WebSocket, routine_id: int):
        """Main WebSocket connection handler."""
        await self.manager.connect(websocket, routine_id)
        try:
            while True:
                data = await websocket.receive()

                if "text" in data:
                    await self._handle_text_message(websocket, routine_id, data["text"])
                elif "bytes" in data:
                    await websocket.send_json(
                        {"error": "Los mensajes binarios directos no están soportados. Utiliza el formato JSON."}
                    )
                else:
                    await websocket.send_json({"error": "Formato de mensaje no reconocido"})

        except WebSocketDisconnect:
            self.manager.disconnect(websocket, routine_id)
        except Exception as e:
            logger.error("WebSocket error (routine_id=%d): %s", routine_id, e)
            try:
                await websocket.send_json({"error": f"Error en el servidor: {e}"})
            except Exception:
                pass
            self.manager.disconnect(websocket, routine_id)

    async def _handle_text_message(self, websocket: WebSocket, routine_id: int, message: str):
        """Process a text message received via WebSocket."""
        try:
            # Try parsing as JSON first
            try:
                data = json.loads(message)

                if isinstance(data, dict) and data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    return

                if isinstance(data, dict) and data.get("type") == "analyze_image":
                    await self._handle_image_analysis(websocket, routine_id, data)
                    return
            except json.JSONDecodeError:
                pass  # Not JSON, treat as plain text

            # Get current routine
            current_routine = await routine_repository.get_routine(routine_id)
            if not current_routine:
                await websocket.send_json({"error": "Rutina no encontrada"})
                return

            # Save user message
            await chat_repository.save_chat_message(routine_id, "user", message)

            # Process with AI
            modified_routine = await self.routine_generator.modify_routine(current_routine, message)
            explanation = await self.routine_generator.explain_routine_changes(
                current_routine, modified_routine, message
            )

            # Persist changes
            await routine_repository.save_routine(modified_routine, routine_id=routine_id)
            await chat_repository.save_chat_message(routine_id, "assistant", explanation)

            # Broadcast update
            await self.manager.broadcast(routine_id, {
                "type": "routine_update",
                "routine": modified_routine.model_dump(),
                "explanation": explanation,
            })

        except Exception as e:
            logger.error("Error processing text message: %s", e)
            await websocket.send_json({"error": f"No se pudo procesar el mensaje: {e}"})

    async def _handle_image_analysis(self, websocket: WebSocket, routine_id: int, data: dict):
        """Handle an image analysis request."""
        try:
            image_data = data.get("image_data")
            exercise_name = data.get("exercise_name")
            action = data.get("action", "analyze_form")

            if not image_data:
                await websocket.send_json({"error": "Datos de imagen no proporcionados"})
                return

            if action == "analyze_form":
                analysis = await self.image_analyzer.analyze_exercise_image(image_data, exercise_name)
            else:
                analysis = await self.image_analyzer.suggest_exercise_variations(image_data)

            await chat_repository.save_chat_message(routine_id, "assistant", analysis)
            await self.manager.broadcast(routine_id, {
                "type": "image_analysis",
                "analysis": analysis,
            })

        except Exception as e:
            logger.error("Image analysis failed: %s", e)
            await websocket.send_json({"error": f"Error al analizar imagen: {e}"})

"""
API routes for routine CRUD operations.
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.logging import get_logger
from app.schemas.routines import RoutineRequest
from app.services.ai_service import RoutineGenerator
from app.repositories import routine_repository, chat_repository
from app.api.dependencies import get_routine_generator

logger = get_logger("routes.routines")

router = APIRouter(prefix="/api", tags=["Routines"])


@router.post("/create_routine")
async def create_routine(
    request: Request,
    generator: RoutineGenerator = Depends(get_routine_generator),
):
    """Create a new AI-generated routine."""
    try:
        if not generator.is_configured:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "El servicio de IA no está disponible."},
            )

        data = await request.json()
        routine_request = RoutineRequest(**data)

        # Generate routine via AI
        routine = await generator.create_initial_routine(routine_request)
        logger.info("Routine generated: %s", routine.routine_name)

        # Persist
        routine_id = await routine_repository.save_routine(routine, user_id=routine_request.user_id)

        # Save initial chat messages (non-critical)
        try:
            await chat_repository.save_chat_message(
                routine_id,
                "user",
                f"Quiero una rutina para {routine_request.goals} con una intensidad de {routine_request.days} días a la semana.",
            )
            await chat_repository.save_chat_message(
                routine_id,
                "assistant",
                "¡He creado una rutina personalizada para ti! Puedes verla en el panel principal.",
            )
        except Exception as e:
            logger.warning("Failed to save initial chat messages: %s", e)

        return {"routine_id": routine_id, "routine": routine.model_dump()}

    except ValueError as e:
        logger.warning("Validation error creating routine: %s", e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(e)},
        )
    except Exception as e:
        logger.error("Failed to create routine: %s", e, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Error interno al generar la rutina"},
        )


@router.post("/modify_routine/{routine_id}")
@router.post("/routine/modify/{routine_id}")
async def modify_routine(
    routine_id: int,
    request: Request,
    generator: RoutineGenerator = Depends(get_routine_generator),
):
    """HTTP fallback for modifying routines (when WebSocket is unavailable)."""
    try:
        data = await request.json()
        message = data.get("message", "")

        if not message:
            return JSONResponse(status_code=400, content={"error": "No se proporcionó mensaje"})

        current_routine = await routine_repository.get_routine(routine_id)
        if not current_routine:
            return JSONResponse(status_code=404, content={"error": "Rutina no encontrada"})

        await chat_repository.save_chat_message(routine_id, "user", message)

        modified_routine = await generator.modify_routine(current_routine, message)
        explanation = await generator.explain_routine_changes(current_routine, modified_routine, message)

        await routine_repository.save_routine(modified_routine, routine_id=routine_id)
        await chat_repository.save_chat_message(routine_id, "assistant", explanation)

        return JSONResponse({"explanation": explanation, "routine": modified_routine.model_dump()})

    except Exception as e:
        logger.error("Failed to modify routine: %s", e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno al modificar la rutina"},
        )


# --- Non-API routes that use Form data ---

delete_router = APIRouter(tags=["Routines"])


@delete_router.post("/delete_routine")
async def delete_routine(routine_id: int = Form(...)):
    """Delete a routine and redirect to the routines list."""
    success = await routine_repository.delete_routine(routine_id)
    if not success:
        raise HTTPException(status_code=500, detail="Error al eliminar la rutina")

    return RedirectResponse(url="/routines?success=true&action=delete", status_code=303)

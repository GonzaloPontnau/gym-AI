"""
HTML page routes (template rendering).
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.repositories import routine_repository, chat_repository

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Landing page with the initial chat interface."""
    return templates.TemplateResponse("chat_initial.html", {"request": request})


@router.get("/routines", response_class=HTMLResponse)
async def list_routines(request: Request, user_id: int = 1):
    """List all routines for a user."""
    routines = await routine_repository.get_user_routines(user_id)
    return templates.TemplateResponse(
        "routines_list.html",
        {"request": request, "routines": routines},
    )


@router.get("/dashboard/{routine_id}", response_class=HTMLResponse)
async def dashboard(request: Request, routine_id: int):
    """Dashboard with routine details and chat sidebar."""
    routine = await routine_repository.get_routine(routine_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")

    chat_history = await chat_repository.get_chat_history(routine_id)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "routine": routine,
            "chat_history": chat_history,
            "routine_id": routine_id,
            "routine_duration": len(routine.days),
        },
    )

import os
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Importar servicios
from app.services.routine_service import RoutineGenerator
from app.services.gemini_service import GeminiRoutineGenerator
from app.services.image_analysis_service import GeminiImageAnalyzer
from app.db.database import init_db, save_routine, get_routine, save_chat_message, get_chat_history, get_user_routines, delete_routine_from_db
from app.websocket.manager import ConnectionManager
from app.websocket.routes import WebSocketRoutes
from app.models.models import RoutineRequest

# Crear la app FastAPI
app = FastAPI(title="GymAI - Gestor Inteligente de Rutinas")

# Configurar middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar plantillas
templates = Jinja2Templates(directory="templates")

# Configurar archivos estáticos solo en desarrollo
# En Vercel, esto será manejado por vercel_app.py
if os.environ.get("VERCEL_ENV") is None:  
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Cargar variables de entorno
load_dotenv()

# Determinar qué generador de rutinas usar
routine_generator = GeminiRoutineGenerator() if os.getenv("GEMINI_API_KEY") else RoutineGenerator()
# Inicializar el analizador de imágenes
image_analyzer = GeminiImageAnalyzer()

# Gestor de conexiones WebSocket
manager = ConnectionManager()

# Inicializar rutas WebSocket
ws_routes = WebSocketRoutes(manager, routine_generator, image_analyzer)

# Configurar eventos de inicio
@app.on_event("startup")
async def startup_event():
    """Inicializar la base de datos"""
    await init_db()

# Rutas de la aplicación
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página inicial con chat para crear rutina"""
    return templates.TemplateResponse("chat_initial.html", {"request": request})

@app.get("/routines", response_class=HTMLResponse)
async def list_routines(request: Request, user_id: int = 1):
    """Listar todas las rutinas del usuario"""
    routines = await get_user_routines(user_id)
    return templates.TemplateResponse(
        "routines_list.html", 
        {"request": request, "routines": routines}
    )

@app.post("/api/create_routine")
async def create_routine(request: Request):
    """Endpoint para crear una rutina inicial"""
    data = await request.json()
    
    routine_request = RoutineRequest(
        goals=data.get("goals", ""),
        equipment=data.get("equipment", ""),
        days=data.get("days", 3),
        user_id=data.get("user_id", 1)
    )
    
    routine = await routine_generator.create_initial_routine(routine_request)
    routine_id = await save_routine(routine, user_id=routine_request.user_id)
    
    # Guardar mensajes iniciales
    await save_chat_message(routine_id, "user", f"Quiero una rutina para {routine_request.goals} con una intensidad de {routine_request.days} días a la semana.")
    await save_chat_message(routine_id, "assistant", "¡He creado una rutina personalizada para ti! Puedes verla en el panel principal.")
    
    return {"routine_id": routine_id, "routine": routine.model_dump()}

@app.get("/dashboard/{routine_id}", response_class=HTMLResponse)
async def dashboard(request: Request, routine_id: int):
    """Dashboard principal con rutina y chat lateral"""
    routine = await get_routine(routine_id)
    
    if not routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    
    chat_history = await get_chat_history(routine_id)
    
    routine_duration = len(routine.days)
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "routine": routine,
            "chat_history": chat_history,
            "routine_id": routine_id,
            "routine_duration": routine_duration
        }
    )

@app.websocket("/ws/chat/{routine_id}")
async def websocket_endpoint(websocket: WebSocket, routine_id: int):
    """Endpoint WebSocket para el chat en tiempo real"""
    await ws_routes.handle_websocket(websocket, routine_id)

# Ruta para eliminar una rutina
@app.post("/delete_routine")
async def delete_routine(routine_id: int = Form(...)):
    """Elimina una rutina y redirige a la lista de rutinas"""
    success = await delete_routine_from_db(routine_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Error al eliminar la rutina")
    
    # Redirigir con parámetros de éxito
    return RedirectResponse(url="/routines?success=true&action=delete", status_code=303)
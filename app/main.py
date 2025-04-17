import os
import asyncio
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno primero
load_dotenv()

# Intentar obtener el bucle de eventos actual o crear uno nuevo
try:
    loop = asyncio.get_event_loop()
    print(f"Usando bucle de eventos existente en main: {loop}")
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print(f"Creado nuevo bucle de eventos en main: {loop}")

# Importar servicios y módulos
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

# Configurar archivos estáticos - CORREGIDO para consistencia con vercel_app.py
if os.environ.get("VERCEL_ENV") is None:  
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ Archivos estáticos montados desde directorio 'static' en /static")

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
    # Solo inicializar si no estamos en Vercel (donde lo hace vercel_app.py)
    if not os.environ.get("VERCEL_ENV"):
        print("⏳ Inicializando base de datos (evento startup)...")
        try:
            await init_db()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error al inicializar la base de datos: {str(e)}")
            print("⚠️ La aplicación seguirá ejecutándose, pero podrían ocurrir errores")
            import traceback
            print(traceback.format_exc())

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
    """Endpoint para crear una rutina inicial con manejo de errores mejorado"""
    try:
        data = await request.json()
        print(f"Datos recibidos para crear rutina: {data}")
        routine_request = RoutineRequest(
            goals=data.get("goals", ""),
            equipment=data.get("equipment", ""),
            days=data.get("days", 3),
            user_id=data.get("user_id", 1)
        )

        # Detectar si estamos en Vercel (entorno serverless)
        is_vercel = os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV") or os.environ.get("VERCEL_REGION")
        if is_vercel:
            print("Detectado entorno Vercel: usando generador de respaldo rápido (sin IA)")
            backup_generator = RoutineGenerator()
            routine = await backup_generator.create_initial_routine(routine_request)
        else:
            # Verificar si Gemini API está configurada
            if not os.getenv("GEMINI_API_KEY"):
                print("ADVERTENCIA: GEMINI_API_KEY no configurada, usando generador de respaldo")
                backup_generator = RoutineGenerator()
                routine = await backup_generator.create_initial_routine(routine_request)
            else:
                try:
                    routine = await routine_generator.create_initial_routine(routine_request)
                except Exception as gemini_error:
                    print(f"Error con Gemini API: {str(gemini_error)}")
                    backup_generator = RoutineGenerator()
                    routine = await backup_generator.create_initial_routine(routine_request)

        print(f"Rutina generada con éxito: {routine.routine_name}")
        try:
            routine_id = await save_routine(routine, user_id=routine_request.user_id)
            print(f"Rutina guardada con ID: {routine_id}")
        except Exception as db_error:
            print(f"Error al guardar rutina en base de datos: {str(db_error)}")
            return {"error": f"Error al guardar rutina: {str(db_error)}"}
        try:
            await save_chat_message(routine_id, "user", f"Quiero una rutina para {routine_request.goals} con una intensidad de {routine_request.days} días a la semana.")
            await save_chat_message(routine_id, "assistant", "¡He creado una rutina personalizada para ti! Puedes verla en el panel principal.")
        except Exception as chat_error:
            print(f"Error al guardar mensajes de chat: {str(chat_error)}")
        return {"routine_id": routine_id, "routine": routine.model_dump()}
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error al crear rutina: {str(e)}")
        print(f"Detalles del error: {error_details}")
        return {"error": str(e), "details": "Hubo un problema al crear la rutina"}

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
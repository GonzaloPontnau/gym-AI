import os
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Importar servicios
from app.services.routine_service import RoutineGenerator
from app.services.gemini_service import GeminiRoutineGenerator
from app.db.database import init_db, save_routine, get_routine, save_chat_message, get_chat_history, get_user_routines
from app.websocket.manager import ConnectionManager
from app.models.models import RoutineRequest

# Crear la app FastAPI
app = FastAPI(title="GymAI - Gestor Inteligente de Rutinas")

# Configurar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar plantillas y archivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cargar variables de entorno
load_dotenv()

# Determinar qué generador de rutinas usar
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print("API key de Gemini detectada. Usando GeminiRoutineGenerator.")
    routine_generator = GeminiRoutineGenerator()
else:
    print("No se encontró API key de Gemini. Usando generador local.")
    routine_generator = RoutineGenerator()

# Crear instancia del gestor de conexiones WebSocket
manager = ConnectionManager()

# Configurar eventos de inicio
@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    # Inicializar la base de datos
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
        {
            "request": request, 
            "routines": routines
        }
    )

@app.post("/api/create_routine")
async def create_routine(request: Request):
    """Endpoint para crear una rutina inicial"""
    data = await request.json()
    
    # Crear el objeto de solicitud
    routine_request = RoutineRequest(
        goals=data.get("goals", ""),
        equipment=data.get("equipment", ""),
        days=data.get("days", 3),
        user_id=data.get("user_id", 1)
    )
    
    # Generar la rutina usando el servicio configurado
    routine = await routine_generator.create_initial_routine(routine_request)
    
    # Guardar la rutina en la base de datos
    routine_id = await save_routine(routine, user_id=routine_request.user_id)
    
    # Guardar mensajes iniciales
    await save_chat_message(routine_id, "user", f"Quiero una rutina para {routine_request.goals} con {routine_request.equipment} para {routine_request.days} días a la semana.")
    await save_chat_message(routine_id, "assistant", f"¡He creado una rutina de {routine.routine_name} personalizada para ti! Puedes ver los detalles en el panel principal.")
    
    return {"routine_id": routine_id, "routine": routine.model_dump()}

@app.get("/dashboard/{routine_id}", response_class=HTMLResponse)
async def dashboard(request: Request, routine_id: int):
    """Dashboard principal con rutina y chat lateral"""
    routine = await get_routine(routine_id)
    
    if not routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    
    chat_history = await get_chat_history(routine_id)
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "routine": routine,
            "chat_history": chat_history,
            "routine_id": routine_id
        }
    )

@app.websocket("/ws/chat/{routine_id}")
async def websocket_endpoint(websocket: WebSocket, routine_id: int):
    """Endpoint WebSocket para el chat en tiempo real"""
    await manager.connect(websocket, routine_id)
    try:
        while True:
            # Recibir mensaje del usuario
            data = await websocket.receive_text()
            
            # Obtener la rutina actual
            current_routine = await get_routine(routine_id)
            
            if not current_routine:
                await websocket.send_json({"error": "Rutina no encontrada"})
                continue
            
            # Guardar mensaje del usuario
            await save_chat_message(routine_id, "user", data)
            
            # Procesar con el generador de rutinas
            modified_routine = await routine_generator.modify_routine(current_routine, data)
            
            # Generar explicación de cambios
            explanation = await routine_generator.explain_routine_changes(current_routine, modified_routine, data)
            
            # Actualizar la rutina en la BD
            await save_routine(modified_routine, routine_id=routine_id)
            
            # Guardar mensaje de respuesta del asistente
            await save_chat_message(routine_id, "assistant", explanation)
            
            # Enviar actualizaciones al cliente
            await manager.broadcast(routine_id, {
                "type": "routine_update",
                "routine": modified_routine.model_dump(),
                "explanation": explanation
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, routine_id)
    except Exception as e:
        print(f"Error en la conexión WebSocket: {str(e)}")
        manager.disconnect(websocket, routine_id)

# Ruta para eliminar una rutina
@app.post("/delete_routine")
async def delete_routine(request: Request, routine_id: int = Form(...)):
    """
    Elimina una rutina de la base de datos y redirige a la lista de rutinas
    """
    print(f"Intentando eliminar rutina con ID: {routine_id}")
    
    # Obtener el servicio de rutinas
    routine_service = RoutineGenerator()
    
    # Intentar eliminar la rutina
    success = await routine_service.delete_routine(routine_id)
    
    print(f"Resultado de la eliminación: {'éxito' if success else 'fallido'}")
    
    if not success:
        # Si falla, mostrar mensaje de error
        raise HTTPException(status_code=500, detail="Error al eliminar la rutina")
    
    # Si todo va bien, redirigir a la lista de rutinas
    return RedirectResponse(url="/routines", status_code=303)
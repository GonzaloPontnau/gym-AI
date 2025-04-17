"""
Punto de entrada minimalista para Vercel con soporte explícito para API
"""
import os
import sys
import json
import random
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

# Configuración básica de logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vercel_app")

# Asegurar que el directorio raíz esté en el PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
    logger.info(f"Añadido {root_dir} al PYTHONPATH")

# Crear la aplicación
app = FastAPI(title="GymAI - Asistente de entrenamiento")
templates = Jinja2Templates(directory="templates")

# Importar el módulo de modo mínimo para operaciones básicas
try:
    from app.minimal_mode import create_demo_routine, get_all_routines, get_routine_by_id
    from app.sqlite_helper import save_routine_sync, save_chat_message_sync
    logger.info("✅ Módulos de operaciones básicas importados correctamente")
except Exception as e:
    logger.error(f"❌ Error al importar módulos: {e}")
    # Implementar funciones mínimas aquí dentro si falla la importación
    
    # Rutina de ejemplo si fallan todas las importaciones
    def create_demo_routine():
        return {
            "routine_name": "Rutina de emergencia",
            "user_id": 1,
            "days": [
                {
                    "day_name": "Lunes",
                    "focus": "Cuerpo completo",
                    "exercises": [
                        {"name": "Flexiones", "sets": 3, "reps": "10", "rest": "60 seg", "equipment": "Peso corporal"},
                        {"name": "Sentadillas", "sets": 3, "reps": "15", "rest": "60 seg", "equipment": "Peso corporal"}
                    ]
                }
            ]
        }

# Montar archivos estáticos
for static_dir in ["/tmp/staticfiles", "staticfiles", "static"]:
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"✅ Archivos estáticos montados desde: {static_dir}")
        break
else:
    logger.warning("❌ No se encontró ningún directorio de archivos estáticos")

# Mapeo de IDs de rutina a datos de rutinas (para persistencia en memoria)
in_memory_routines = {}
in_memory_chat_messages = {}

# Página principal
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página inicial con formulario para crear rutina"""
    return templates.TemplateResponse("chat_initial.html", {"request": request})

# API para crear rutina - RUTA CRÍTICA
@app.post("/api/create_routine")
async def create_routine_api(request: Request):
    """Endpoint para crear una rutina inicial - VERSIÓN SIMPLIFICADA"""
    try:
        # Obtener datos del cuerpo de la solicitud
        data = await request.json()
        logger.info(f"Datos recibidos: {data}")
        
        # Extraer parámetros básicos
        goals = data.get("goals", "Rutina básica")
        days = data.get("days", 3)
        user_id = data.get("user_id", 1)
        
        # Crear una rutina de ejemplo básica
        routine = create_demo_routine()
        routine["routine_name"] = f"Rutina {goals[:20]}... ({days} días)"
        
        # Añadir días según lo solicitado (máximo 7)
        day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        focus_options = ["Pecho/Tríceps", "Espalda/Bíceps", "Piernas", "Hombros/Abdomen", "Cuerpo completo"]
        exercise_options = [
            {"name": "Flexiones", "equipment": "Peso corporal"},
            {"name": "Sentadillas", "equipment": "Peso corporal"},
            {"name": "Plancha", "equipment": "Peso corporal"},
            {"name": "Zancadas", "equipment": "Peso corporal"},
            {"name": "Dominadas", "equipment": "Barra"}
        ]
        
        # Crear días de rutina
        routine["days"] = []
        for i in range(min(days, 7)):
            exercises = []
            for _ in range(3):  # 3 ejercicios por día
                exercise = random.choice(exercise_options)
                exercises.append({
                    "name": exercise["name"],
                    "sets": 3,
                    "reps": "10-12",
                    "rest": "60 seg",
                    "equipment": exercise["equipment"]
                })
                
            routine["days"].append({
                "day_name": day_names[i],
                "focus": random.choice(focus_options),
                "exercises": exercises
            })
        
        # Guardar la rutina (en memoria para esta implementación simple)
        routine_id = len(in_memory_routines) + 1
        in_memory_routines[routine_id] = routine
        
        # Intentar guardar en SQLite si está disponible
        try:
            from app.sqlite_helper import save_routine_sync
            routine_id = save_routine_sync(routine, user_id)
            logger.info(f"✅ Rutina guardada en SQLite con ID: {routine_id}")
        except Exception as sqlite_err:
            logger.error(f"❌ Error al guardar en SQLite: {sqlite_err}")
        
        # Registro simulado en la consola
        logger.info(f"✅ Rutina creada con ID: {routine_id}")
        
        # Devolver respuesta
        return JSONResponse({
            "routine_id": routine_id,
            "routine": routine
        })
            
    except Exception as e:
        logger.error(f"❌ Error al crear rutina: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Error al crear rutina: {str(e)}"}
        )

# Ver rutina específica
@app.get("/dashboard/{routine_id}", response_class=HTMLResponse)
async def dashboard(request: Request, routine_id: int):
    """Vista de dashboard para una rutina específica"""
    # Intentar obtener la rutina de SQLite primero
    routine = None
    try:
        from app.sqlite_helper import get_routine_sync
        routine = get_routine_sync(routine_id)
    except Exception:
        pass
    
    # Si no está en SQLite, buscar en memoria
    if not routine and routine_id in in_memory_routines:
        routine = in_memory_routines[routine_id]
    
    # Si aún no se encuentra, crear una demo
    if not routine:
        routine = create_demo_routine()
        routine["id"] = routine_id
    
    # Mensajes de chat (vacíos si no hay)
    chat_history = []
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "routine": routine,
            "chat_history": chat_history,
            "routine_id": routine_id,
            "routine_duration": len(routine.get("days", []))
        }
    )

# Listar rutinas
@app.get("/routines", response_class=HTMLResponse)
async def list_routines(request: Request, user_id: int = 1):
    """Listar todas las rutinas"""
    # Intentar obtener rutinas de SQLite
    routines = []
    try:
        from app.sqlite_helper import get_user_routines_sync
        routines = get_user_routines_sync(user_id)
    except Exception:
        pass
    
    # Si no hay rutinas en SQLite, usar las de memoria
    if not routines:
        routines = [
            {"id": rid, "routine_name": r["routine_name"], 
             "updated_at": datetime.now().isoformat()}
            for rid, r in in_memory_routines.items()
        ]
    
    # Si aún no hay rutinas, crear una demo
    if not routines:
        routine = create_demo_routine()
        routine_id = 1
        in_memory_routines[routine_id] = routine
        routines = [{"id": routine_id, "routine_name": routine["routine_name"], 
                     "updated_at": datetime.now().isoformat()}]
    
    return templates.TemplateResponse(
        "routines_list.html", 
        {"request": request, "routines": routines}
    )

# Eliminar rutina
@app.post("/delete_routine")
async def delete_routine(routine_id: int = Form(...)):
    """Elimina una rutina"""
    # Intentar eliminar de SQLite
    success = False
    try:
        from app.sqlite_helper import delete_routine_sync
        success = delete_routine_sync(routine_id)
    except Exception:
        pass
    
    # También eliminar de memoria
    if routine_id in in_memory_routines:
        del in_memory_routines[routine_id]
        success = True
    
    # Redirigir con parámetros de éxito
    return RedirectResponse(url="/routines?success=true&action=delete", status_code=303)

# Verificación de salud
@app.get("/health")
async def health_check():
    """Endpoint para verificar si la aplicación está funcionando"""
    return {"status": "online", "server_time": datetime.now().isoformat()}

"""
Punto de entrada minimalista para Vercel con soporte explícito para API
"""
import os
import sys
import json
import random
from datetime import datetime
from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

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

# Configurar middleware CORS (necesario para WebSockets)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# Importar el módulo de modo mínimo para operaciones básicas
try:
    from app.sqlite_helper import (
        save_routine_sync, 
        save_chat_message_sync, 
        get_chat_history_sync, 
        get_routine_sync,
        get_user_routines_sync,
        delete_routine_sync
    )
    logger.info("✅ Módulos de operaciones básicas importados correctamente")
except Exception as e:
    logger.error(f"❌ Error al importar módulos: {e}")
    # No implementar funciones de respaldo - se manejarán excepciones específicamente

# Importar servicios de Gemini si está disponible
try:
    from app.services.gemini_service import GeminiRoutineGenerator
    from app.services.image_analysis_service import GeminiImageAnalyzer
    from app.websocket.manager import ConnectionManager
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    if has_gemini:
        routine_generator = GeminiRoutineGenerator()
        image_analyzer = GeminiImageAnalyzer()
        logger.info("✅ Servicios de Gemini inicializados correctamente")
    else:
        logger.warning("⚠️ GEMINI_API_KEY no configurada, chat avanzado no disponible")
        routine_generator = None
        image_analyzer = None
    
    # Inicializar gestor de conexiones WebSocket
    ws_manager = ConnectionManager()
    logger.info("✅ Gestor de WebSockets inicializado")
except Exception as e:
    logger.error(f"❌ Error al inicializar servicios de Gemini: {e}")
    has_gemini = False
    routine_generator = None
    image_analyzer = None
    ws_manager = None

# Montar archivos estáticos
for static_dir in ["/tmp/staticfiles", "staticfiles", "static"]:
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"✅ Archivos estáticos montados desde: {static_dir}")
        break
else:
    logger.warning("❌ No se encontró ningún directorio de archivos estáticos")

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
        
        # Crear una rutina con datos básicos de usuario
        routine = {
            "routine_name": f"Rutina {goals[:20]}... ({days} días)",
            "user_id": user_id,
            "days": []
        }
        
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
        
        # Guardar en SQLite
        try:
            routine_id = save_routine_sync(routine, user_id)
            logger.info(f"✅ Rutina guardada en SQLite con ID: {routine_id}")
            
            # Guardar mensajes iniciales del chat
            try:
                save_chat_message_sync(routine_id, "user", f"Quiero una rutina para {goals} con {days} días a la semana.")
                save_chat_message_sync(routine_id, "assistant", "¡He creado una rutina personalizada para ti! Puedes verla en el panel principal.")
                logger.info(f"✅ Mensajes de chat iniciales guardados")
            except Exception as chat_err:
                logger.error(f"❌ Error al guardar mensajes de chat: {chat_err}")
                
            # Devolver respuesta
            return JSONResponse({
                "routine_id": routine_id,
                "routine": routine
            })
                
        except Exception as sqlite_err:
            logger.error(f"❌ Error al guardar en SQLite: {sqlite_err}")
            # Fallar explícitamente - no usar rutina demo
            return JSONResponse(
                status_code=500,
                content={"error": "No se pudo guardar la rutina en la base de datos. Por favor, inténtalo de nuevo."}
            )
            
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
    # Intentar obtener la rutina de SQLite
    try:
        routine = get_routine_sync(routine_id)
        if not routine:
            # Si no se encuentra la rutina, devolver 404
            raise HTTPException(status_code=404, detail="Rutina no encontrada")
        
        # Intentar obtener mensajes de chat
        chat_history = []
        try:
            chat_history = get_chat_history_sync(routine_id)
            logger.info(f"✅ Obtenidos {len(chat_history)} mensajes de chat")
        except Exception as chat_err:
            logger.error(f"❌ Error al obtener historial de chat: {chat_err}")
        
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
    
    except HTTPException:
        # Re-lanzar la excepción HTTP
        raise
    except Exception as e:
        logger.error(f"Error al obtener rutina de SQLite: {e}")
        raise HTTPException(status_code=500, detail="Error al cargar la rutina")

# Listar rutinas
@app.get("/routines", response_class=HTMLResponse)
async def list_routines(request: Request, user_id: int = 1):
    """Listar todas las rutinas"""
    # Intentar obtener rutinas de SQLite
    try:
        routines = get_user_routines_sync(user_id)
        
        # Si no hay rutinas, mostrar mensaje informativo
        return templates.TemplateResponse(
            "routines_list.html", 
            {"request": request, "routines": routines}
        )
    except Exception as e:
        logger.error(f"Error al obtener rutinas: {e}")
        # Mostrar página sin rutinas, en lugar de fallar
        return templates.TemplateResponse(
            "routines_list.html", 
            {"request": request, "routines": []}
        )

# Eliminar rutina
@app.post("/delete_routine")
async def delete_routine(routine_id: int = Form(...)):
    """Elimina una rutina"""
    try:
        # Intentar eliminar de SQLite
        success = delete_routine_sync(routine_id)
        
        if not success:
            # Si no se pudo eliminar, mostrar error
            raise HTTPException(status_code=404, detail="Rutina no encontrada o no se pudo eliminar")
        
        # Redirigir con parámetros de éxito
        return RedirectResponse(url="/routines?success=true&action=delete", status_code=303)
    
    except HTTPException:
        # Re-lanzar la excepción HTTP
        raise
    except Exception as e:
        logger.error(f"Error al eliminar rutina: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar la rutina")

# Endpoint WebSocket para el chat (NUEVO)
@app.websocket("/ws/chat/{routine_id}")
async def websocket_endpoint(websocket: WebSocket, routine_id: int):
    """Endpoint WebSocket para el chat en tiempo real"""
    if not ws_manager:
        # Si no hay gestor de WebSockets, rechazar conexión
        return
    
    # Aceptar conexión
    await ws_manager.connect(websocket, routine_id)
    
    try:
        while True:
            # Recibir mensaje
            data = await websocket.receive()
            
            # Procesar mensaje según su tipo
            if "text" in data:
                await handle_ws_text_message(websocket, routine_id, data["text"])
            elif "bytes" in data:
                await websocket.send_json({"error": "No se soportan mensajes binarios directamente"})
            
    except WebSocketDisconnect:
        # Desconectar cliente
        ws_manager.disconnect(websocket, routine_id)
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        try:
            await websocket.send_json({"error": f"Error en el servidor: {str(e)}"})
        except:
            pass
        if ws_manager:
            ws_manager.disconnect(websocket, routine_id)

# Manejar mensajes de texto del WebSocket
async def handle_ws_text_message(websocket: WebSocket, routine_id: int, message: str):
    """Procesa un mensaje de texto recibido por WebSocket"""
    # Verificar si es un comando especial (como análisis de imagen)
    try:
        import json
        data = json.loads(message)
        if isinstance(data, dict) and data.get("type") == "analyze_image":
            # Procesar análisis de imagen si Gemini está disponible
            if image_analyzer:
                try:
                    image_data = data.get("image_data", "")
                    exercise_name = data.get("exercise_name", "")
                    
                    if data.get("action") == "analyze_form":
                        analysis = await image_analyzer.analyze_exercise_image(image_data, exercise_name)
                    else:
                        analysis = await image_analyzer.suggest_exercise_variations(image_data)
                    
                    # Guardar análisis como mensaje
                    save_chat_message_sync(routine_id, "assistant", analysis)
                    
                    # Enviar respuesta
                    await ws_manager.broadcast(routine_id, {
                        "type": "image_analysis",
                        "analysis": analysis
                    })
                    return
                except Exception as img_err:
                    logger.error(f"Error al analizar imagen: {img_err}")
                    await websocket.send_json({"error": f"Error al analizar imagen: {str(img_err)}"})
                    return
            else:
                await websocket.send_json({"error": "Análisis de imágenes no disponible (Gemini no configurado)"})
                return
    except json.JSONDecodeError:
        # No es JSON, tratar como mensaje de texto normal
        pass
    
    # Procesar mensaje de texto normal
    try:
        # Obtener la rutina actual
        current_routine = get_routine_sync(routine_id)
        
        if not current_routine:
            await websocket.send_json({"error": "Rutina no encontrada"})
            return
        
        # Guardar mensaje del usuario
        save_chat_message_sync(routine_id, "user", message)
        
        # Si Gemini está disponible, usar para modificar rutina
        if routine_generator:
            try:
                from app.models.models import Routine
                # Convertir a objeto Routine para el generador
                routine_obj = Routine.model_validate(current_routine)
                
                # Modificar rutina
                modified_routine = await routine_generator.modify_routine(routine_obj, message)
                explanation = await routine_generator.explain_routine_changes(routine_obj, modified_routine, message)
                
                # Guardar rutina modificada
                routine_dict = modified_routine.model_dump()
                save_routine_sync(routine_dict, routine_id=routine_id)
                
                # Guardar explicación como mensaje
                save_chat_message_sync(routine_id, "assistant", explanation)
                
                # Enviar actualización
                await ws_manager.broadcast(routine_id, {
                    "type": "routine_update",
                    "routine": routine_dict,
                    "explanation": explanation
                })
                return
            except Exception as modify_err:
                logger.error(f"Error al modificar rutina: {modify_err}")
        
        # Si llegamos aquí, Gemini no está disponible o falló
        # Dar respuesta genérica
        generic_response = "Lo siento, no puedo modificar la rutina en este momento. La API de Gemini no está configurada correctamente."
        save_chat_message_sync(routine_id, "assistant", generic_response)
        await ws_manager.broadcast(routine_id, {
            "type": "routine_update",
            "routine": current_routine,
            "explanation": generic_response
        })
        
    except Exception as e:
        logger.error(f"Error al procesar mensaje: {e}")
        await websocket.send_json({"error": f"Error al procesar mensaje: {str(e)}"})

# Verificación de salud
@app.get("/health")
async def health_check():
    """Endpoint para verificar si la aplicación está funcionando"""
    status = {
        "status": "online", 
        "server_time": datetime.now().isoformat(),
        "gemini_available": has_gemini,
        "websocket_available": ws_manager is not None
    }
    return status

from fastapi import WebSocket, WebSocketDisconnect
from app.models.models import Routine
from app.websocket.manager import ConnectionManager
from app.services.gemini_service import GeminiRoutineGenerator
from app.services.image_analysis_service import GeminiImageAnalyzer
from app.db.database import save_routine, get_routine, save_chat_message

class WebSocketRoutes:
    """Clase para manejar las rutas de WebSocket"""
    
    def __init__(self, manager: ConnectionManager, routine_generator, image_analyzer):
        self.manager = manager
        self.routine_generator = routine_generator
        self.image_analyzer = image_analyzer
    
    async def handle_websocket(self, websocket: WebSocket, routine_id: int):
        """Maneja una conexión WebSocket para un chat de rutina"""
        await self.manager.connect(websocket, routine_id)
        try:
            while True:
                # Recibir el mensaje
                data = await websocket.receive()
                
                # Verificar si el mensaje es de texto o binario
                if "text" in data:
                    await self.handle_text_message(websocket, routine_id, data["text"])
                elif "bytes" in data:
                    await self.handle_binary_message(websocket, routine_id, data["bytes"])
                else:
                    # Enviar un mensaje de error si el formato no es reconocido
                    await websocket.send_json({"error": "Formato de mensaje no reconocido"})
                    
        except WebSocketDisconnect:
            self.manager.disconnect(websocket, routine_id)
        except Exception as e:
            print(f"Error en WebSocket (routine_id={routine_id}): {str(e)}")
            try:
                await websocket.send_json({"error": f"Error en el servidor: {str(e)}"})
            except:
                pass
            self.manager.disconnect(websocket, routine_id)
    
    async def handle_text_message(self, websocket: WebSocket, routine_id: int, message: str):
        """Maneja un mensaje de texto recibido por WebSocket"""
        try:
            import json
            
            # Intentar parsear como JSON primero
            try:
                data = json.loads(message)
                
                # Manejar mensajes de tipo ping (keepalive)
                if isinstance(data, dict) and data.get("type") == "ping":
                    # Simplemente responder con un pong para mantener la conexión viva
                    await websocket.send_json({"type": "pong"})
                    return
                
                # Si es un mensaje JSON, procesar según su tipo
                if isinstance(data, dict) and data.get("type") == "analyze_image":
                    await self.handle_image_analysis(websocket, routine_id, data)
                    return
            except json.JSONDecodeError:
                # No es JSON, tratar como mensaje de texto normal
                pass
            
            # Obtener la rutina actual
            current_routine = await get_routine(routine_id)
            if not current_routine:
                await websocket.send_json({"error": "Rutina no encontrada"})
                return
            
            # Guardar mensaje del usuario
            await save_chat_message(routine_id, "user", message)
            
            # Procesar con el generador de rutinas
            modified_routine = await self.routine_generator.modify_routine(current_routine, message)
            explanation = await self.routine_generator.explain_routine_changes(current_routine, modified_routine, message)
            
            # Actualizar la rutina en la BD
            await save_routine(modified_routine, routine_id=routine_id)
            await save_chat_message(routine_id, "assistant", explanation)
            
            # Enviar actualizaciones al cliente
            await self.manager.broadcast(routine_id, {
                "type": "routine_update",
                "routine": modified_routine.model_dump(),
                "explanation": explanation
            })
        except Exception as e:
            print(f"Error al procesar mensaje de texto: {str(e)}")
            await websocket.send_json({"error": f"No se pudo procesar el mensaje: {str(e)}"})
    
    async def handle_binary_message(self, websocket: WebSocket, routine_id: int, data: bytes):
        """Maneja un mensaje binario (posiblemente una imagen) recibido por WebSocket"""
        await websocket.send_json({"error": "Los mensajes binarios directos no están soportados. Utiliza el formato JSON para enviar imágenes."})
    
    async def handle_image_analysis(self, websocket: WebSocket, routine_id: int, data: dict):
        """Maneja una solicitud de análisis de imagen"""
        try:
            # Extraer datos de la solicitud
            image_data = data.get("image_data")
            exercise_name = data.get("exercise_name")
            action = data.get("action", "analyze_form")
            
            if not image_data:
                await websocket.send_json({"error": "Datos de imagen no proporcionados"})
                return
            
            # Realizar el análisis según la acción solicitada
            if action == "analyze_form":
                analysis = await self.image_analyzer.analyze_exercise_image(image_data, exercise_name)
            else:
                analysis = await self.image_analyzer.suggest_exercise_variations(image_data)
            
            # Guardar y enviar el análisis
            await save_chat_message(routine_id, "assistant", analysis)
            await self.manager.broadcast(routine_id, {
                "type": "image_analysis",
                "analysis": analysis
            })
        except Exception as e:
            print(f"Error al analizar imagen: {str(e)}")
            await websocket.send_json({"error": f"Error al analizar imagen: {str(e)}"})

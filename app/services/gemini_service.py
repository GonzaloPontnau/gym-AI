import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from app.models.models import Exercise, Day, Routine, RoutineRequest

# Cargar variables de entorno
load_dotenv()

# Configurar la API de Gemini con la clave API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Definir el modelo a utilizar (gemini-1.5-flash)
model = genai.GenerativeModel('gemini-1.5-flash')

class GeminiRoutineGenerator:
    """Servicio para generar rutinas de entrenamiento utilizando la API de Gemini"""
    
    def _build_initial_prompt(self, request: RoutineRequest) -> str:
        """Construye el prompt inicial para crear una rutina basada en los requisitos del usuario"""
        return f"""
        Actúa como un entrenador personal profesional y crea una rutina de entrenamiento detallada con estas características:
        
        Objetivos: {request.goals}
        Días de entrenamiento: {request.days} días a la semana
        
        La rutina debe seguir ESTRICTAMENTE este formato JSON:
        
        {{
            "routine_name": "Nombre descriptivo de la rutina",
            "days": [
                {{
                    "day_name": "Lunes",
                    "focus": "Parte del cuerpo que se trabaja ese día",
                    "exercises": [
                        {{
                            "name": "Nombre del ejercicio",
                            "sets": 3,
                            "reps": "8-12",
                            "rest": "60-90 seg",
                            "equipment": "Equipamiento necesario"
                        }}
                    ]
                }}
            ]
        }}
        
        IMPORTANTE: 
        1. Devuelve SOLO el JSON válido, sin texto explicativo antes o después.
        2. Asegúrate de que el JSON sea válido y esté completo.
        3. Incluye exactamente {request.days} días en la rutina.
        4. Cada ejercicio debe tener todos los campos requeridos.
        """
    
    def _build_modification_prompt(self, current_routine: Routine, user_request: str) -> str:
        """Construye el prompt para modificar una rutina existente según la solicitud del usuario"""
        # Convertir la rutina actual a formato JSON para incluirla en el prompt
        routine_json = current_routine.model_dump_json()
        
        return f"""
        Actúa como un entrenador personal profesional. El usuario tiene la siguiente rutina de entrenamiento (en formato JSON):
        
        ```json
        {routine_json}
        ```
        
        El usuario ha solicitado el siguiente cambio: "{user_request}"
        
        Por favor, modifica la rutina según esta solicitud y devuelve la rutina completa actualizada en formato JSON.
        Retorna SOLO el JSON completo entre marcadores de código, sin texto adicional:
        
        ```json
        {{
            // Aquí va la rutina actualizada
        }}
        ```
        
        Mantén el mismo formato y estructura de la rutina original, solo cambia lo necesario según la solicitud.
        """
    
    def _build_explanation_prompt(self, old_routine: Routine, new_routine: Routine, user_request: str) -> str:
        """Construye el prompt para generar una explicación de los cambios realizados"""
        return f"""
        Actúa como un entrenador personal profesional. 
        
        He realizado cambios a una rutina de entrenamiento basados en la siguiente solicitud del usuario:
        "{user_request}"
        
        Por favor, genera una explicación clara y concisa de los cambios que se han hecho a la rutina.
        Menciona qué ejercicios se han añadido, eliminado o modificado, y el razonamiento detrás de estos cambios.
        
        La explicación debe ser profesional, motivadora y fácil de entender.
        
        No incluyas código JSON ni formato técnico. Solo texto natural explicando los cambios.
        """
    
    def _extract_json_from_text(self, text: str) -> dict:
        """Extrae el contenido JSON de una respuesta de texto"""
        try:
            # Primero intentar buscar bloques de código JSON
            json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
            json_matches = re.findall(json_pattern, text)
            
            if json_matches:
                # Si encontramos un bloque de código JSON, usamos el primer bloque
                json_text = json_matches[0].strip()
                return json.loads(json_text)
            
            # Si no hay bloques de código, intentar parsear el texto completo
            return json.loads(text.strip())
            
        except Exception as e:
            print(f"Error al extraer JSON: {str(e)}")
            print(f"Texto recibido: {text}")
            # Si no se puede parsear, devolver un diccionario vacío
            return {}
    
    async def create_initial_routine(self, request: RoutineRequest) -> Routine:
        """Genera una rutina inicial utilizando la API de Gemini"""
        # Construir el prompt
        prompt = self._build_initial_prompt(request)
        
        try:
            # Generar la respuesta con Gemini
            response = model.generate_content(prompt)
            
            # Extraer y parsear el JSON de la respuesta
            routine_dict = self._extract_json_from_text(response.text)
            
            # Verificar si se obtuvo un diccionario vacío
            if not routine_dict:
                raise ValueError("No se pudo extraer JSON válido de la respuesta")
                
            # Asegurarse de que se incluya el ID de usuario
            routine_dict["user_id"] = request.user_id
            
            # Crear la rutina utilizando Pydantic
            routine = Routine.model_validate(routine_dict)
            return routine
            
        except Exception as e:
            print(f"Error al generar rutina con Gemini: {str(e)}")
            # En caso de error, usar el generador de respaldo
            from app.services.routine_service import RoutineGenerator
            backup_generator = RoutineGenerator()
            return await backup_generator.create_initial_routine(request)
    
    async def modify_routine(self, current_routine: Routine, user_request: str) -> Routine:
        """Modifica una rutina existente según la solicitud del usuario utilizando la API de Gemini"""
        # Construir el prompt
        prompt = self._build_modification_prompt(current_routine, user_request)
        
        try:
            # Generar la respuesta con Gemini
            response = model.generate_content(prompt)
            
            # Extraer y parsear el JSON de la respuesta
            routine_dict = self._extract_json_from_text(response.text)
            
            # Verificar si se obtuvo un diccionario vacío
            if not routine_dict:
                raise ValueError("No se pudo extraer JSON válido de la respuesta")
            
            # Asegurarse de que se mantenga el ID y user_id
            routine_dict["id"] = current_routine.id
            routine_dict["user_id"] = current_routine.user_id
            
            # Crear la rutina utilizando Pydantic
            routine = Routine.model_validate(routine_dict)
            return routine
            
        except Exception as e:
            print(f"Error al modificar rutina con Gemini: {str(e)}")
            # En caso de error, usar el generador de respaldo
            from app.services.routine_service import RoutineGenerator
            backup_generator = RoutineGenerator()
            return await backup_generator.modify_routine(current_routine, user_request)
    
    async def explain_routine_changes(self, old_routine: Routine, new_routine: Routine, user_request: str) -> str:
        """Genera una explicación de los cambios realizados a la rutina utilizando la API de Gemini"""
        # Construir el prompt
        prompt = self._build_explanation_prompt(old_routine, new_routine, user_request)
        
        try:
            # Generar la respuesta con Gemini
            response = model.generate_content(prompt)
            
            # Retornar el texto de la explicación
            return response.text.strip()
            
        except Exception as e:
            print(f"Error al obtener explicación de Gemini: {str(e)}")
            # En caso de error, usar el generador de respaldo
            from app.services.routine_service import RoutineGenerator
            backup_generator = RoutineGenerator()
            return await backup_generator.explain_routine_changes(old_routine, new_routine, user_request)
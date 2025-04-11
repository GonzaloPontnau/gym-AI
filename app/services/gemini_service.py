import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from app.models.models import Routine, RoutineRequest

# Cargar variables de entorno
load_dotenv()

# Configurar la API de Gemini con la clave API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Definir el modelo a utilizar
model = genai.GenerativeModel('gemini-1.5-flash')

class GeminiRoutineGenerator:
    """Servicio para generar rutinas de entrenamiento utilizando la API de Gemini"""
    
    def _build_initial_prompt(self, request: RoutineRequest) -> str:
        """Construye el prompt inicial para crear una rutina"""
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
        1. Devuelve SOLO el JSON válido, sin texto explicativo.
        2. Incluye exactamente {request.days} días en la rutina.
        """
    
    def _build_modification_prompt(self, current_routine: Routine, user_request: str) -> str:
        """Construye el prompt para modificar una rutina existente"""
        routine_json = current_routine.model_dump_json()
        
        return f"""
        Actúa como un entrenador personal. El usuario tiene la siguiente rutina de entrenamiento:
        
        ```json
        {routine_json}
        ```
        
        El usuario ha solicitado: "{user_request}"
        
        Modifica la rutina según esta solicitud y devuelve SOLO el JSON actualizado.
        """
    
    def _extract_json_from_text(self, text: str) -> dict:
        """Extrae el contenido JSON de una respuesta de texto"""
        try:
            # Buscar bloques de código JSON
            json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
            json_matches = re.findall(json_pattern, text)
            
            if json_matches:
                return json.loads(json_matches[0].strip())
            
            # Si no hay bloques de código, parsear el texto completo
            return json.loads(text.strip())
            
        except Exception as e:
            print(f"Error al extraer JSON: {str(e)}")
            return {}
    
    async def create_initial_routine(self, request: RoutineRequest) -> Routine:
        """Genera una rutina inicial utilizando la API de Gemini"""
        prompt = self._build_initial_prompt(request)
        
        try:
            response = model.generate_content(prompt)
            routine_dict = self._extract_json_from_text(response.text)
            
            if not routine_dict:
                raise ValueError("No se pudo extraer JSON válido")
                
            routine_dict["user_id"] = request.user_id
            routine = Routine.model_validate(routine_dict)
            return routine
            
        except Exception as e:
            print(f"Error al generar rutina con Gemini: {str(e)}")
            # Usar generador de respaldo
            from app.services.routine_service import RoutineGenerator
            backup_generator = RoutineGenerator()
            return await backup_generator.create_initial_routine(request)
    
    async def modify_routine(self, current_routine: Routine, user_request: str) -> Routine:
        """Modifica una rutina existente según la solicitud del usuario"""
        prompt = self._build_modification_prompt(current_routine, user_request)
        
        try:
            response = model.generate_content(prompt)
            routine_dict = self._extract_json_from_text(response.text)
            
            if not routine_dict:
                raise ValueError("No se pudo extraer JSON válido")
            
            # Mantener el ID y user_id originales
            routine_dict["id"] = current_routine.id
            routine_dict["user_id"] = current_routine.user_id
            
            routine = Routine.model_validate(routine_dict)
            return routine
            
        except Exception as e:
            print(f"Error al modificar rutina: {str(e)}")
            from app.services.routine_service import RoutineGenerator
            backup_generator = RoutineGenerator()
            return await backup_generator.modify_routine(current_routine, user_request)
    
    async def explain_routine_changes(self, old_routine: Routine, new_routine: Routine, user_request: str) -> str:
        """Genera una explicación de los cambios realizados a la rutina"""
        prompt = f"""
        El usuario solicitó: "{user_request}"
        
        Explica brevemente los cambios realizados a la rutina de forma profesional y motivadora.
        No incluyas código JSON, solo texto explicando los cambios principales.
        """
        
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error al obtener explicación: {str(e)}")
            from app.services.routine_service import RoutineGenerator
            backup_generator = RoutineGenerator()
            return await backup_generator.explain_routine_changes(old_routine, new_routine, user_request)
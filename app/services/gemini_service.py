import os
import json
import re
import traceback
from dotenv import load_dotenv
from app.models.models import Routine, RoutineRequest

# Cargar variables de entorno
load_dotenv()

# Variable para seguimiento de si Gemini está configurado
GEMINI_CONFIGURED = False

# Intentar configurar Gemini solo si la API key está disponible
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        # Definir el modelo a utilizar
        model = genai.GenerativeModel('gemini-1.5-flash')
        GEMINI_CONFIGURED = True
        print("✅ API de Gemini configurada correctamente")
    except Exception as e:
        print(f"❌ Error al configurar Gemini API: {str(e)}")
else:
    print("⚠️ GEMINI_API_KEY no encontrada, servicio de IA no estará disponible")

class GeminiRoutineGenerator:
    """Servicio para generar rutinas de entrenamiento utilizando la API de Gemini"""
    
    def _build_initial_prompt(self, request: RoutineRequest) -> str:
        """Construye el prompt inicial para crear una rutina"""
        return f"""
        Actúa como un entrenador personal profesional y crea una rutina de entrenamiento detallada con estas características:
        
        Objetivos: {request.goals}
        Días de entrenamiento: {request.days} días a la semana
        Nivel de experiencia: {request.experience_level if hasattr(request, 'experience_level') else 'No especificado'}
        Equipo disponible: {request.available_equipment if hasattr(request, 'available_equipment') else 'No especificado'}
        Tiempo por sesión: {request.time_per_session if hasattr(request, 'time_per_session') else 'No especificado'}
        Condiciones de salud: {request.health_conditions if hasattr(request, 'health_conditions') else 'Ninguna'}
        
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
            clean_text = text.strip()
            return json.loads(clean_text)
            
        except Exception as e:
            print(f"Error al extraer JSON: {str(e)}")
            print(f"Texto recibido: {text[:200]}...")  # Mostrar primeros 200 caracteres
            return {}
    
    async def create_initial_routine(self, request: RoutineRequest) -> Routine:
        """Genera una rutina inicial utilizando la API de Gemini"""
        
        # Verificar si Gemini está configurado
        if not GEMINI_CONFIGURED:
            print("❌ Gemini no está configurado")
            raise ValueError("API de Gemini no está configurada. No se pueden generar rutinas.")
        
        prompt = self._build_initial_prompt(request)
        
        try:
            print("Enviando solicitud a Gemini API...")
            response = model.generate_content(prompt)
            
            print(f"Respuesta recibida de Gemini, extrayendo JSON...")
            print(f"Muestra de respuesta: {response.text[:200]}...")  # Primeros 200 caracteres
            
            routine_dict = self._extract_json_from_text(response.text)
            
            if not routine_dict:
                print("❌ No se pudo extraer JSON válido de la respuesta")
                raise ValueError("No se pudo extraer JSON válido de la respuesta de Gemini")
                
            routine_dict["user_id"] = request.user_id
            
            print(f"Validando rutina con Pydantic...")
            routine = Routine.model_validate(routine_dict)
            print(f"✅ Rutina validada correctamente: {routine.routine_name}")
            return routine
            
        except Exception as e:
            print(f"❌ Error al generar rutina con Gemini: {str(e)}")
            print(traceback.format_exc())
            raise ValueError(f"Error al generar rutina con Gemini: {str(e)}")
    
    async def modify_routine(self, current_routine: Routine, user_request: str) -> Routine:
        """Modifica una rutina existente según la solicitud del usuario"""
        # Verificar si Gemini está configurado
        if not GEMINI_CONFIGURED:
            print("❌ Gemini no está configurado")
            raise ValueError("API de Gemini no está configurada. No se pueden modificar rutinas.")
            
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
            raise ValueError(f"Error al modificar rutina con Gemini: {str(e)}")
    
    async def explain_routine_changes(self, old_routine: Routine, new_routine: Routine, user_request: str) -> str:
        """Genera una explicación de los cambios realizados a la rutina"""
        # Verificar si Gemini está configurado
        if not GEMINI_CONFIGURED:
            print("❌ Gemini no está configurado")
            raise ValueError("API de Gemini no está configurada. No se puede explicar cambios.")
            
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
            raise ValueError(f"Error al generar explicación con Gemini: {str(e)}")
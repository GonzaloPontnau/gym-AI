# Gym-AI - Gestor Inteligente de Rutinas con IA

## 1. Visión General

### 1.1 Concepto
GymAI es una aplicación web para la creación y gestión de rutinas de entrenamiento personalizadas mediante inteligencia artificial. Su flujo único de dos fases (conversación inicial seguida de dashboard interactivo) permite a los usuarios crear y modificar rutinas de forma intuitiva a través de lenguaje natural.

### 1.2 Propuesta de Valor
- **Personalización mediante IA**: Creación de rutinas adaptadas a objetivos, nivel y equipamiento disponible
- **Interfaz conversacional**: Interacción natural mediante chat para crear y modificar rutinas
- **Dashboard visual**: Visualización clara de la rutina con modificación en tiempo real
- **Persistencia contextual**: Conservación del historial de conversación para referencias y ajustes futuros

## 2. Stack Tecnológico
| Capa | Tecnologías |
|------|-------------|
| **Backend** | Python (FastAPI), SQLAlchemy ORM, Pydantic, JWT, WebSockets |
| **Frontend** | Jinja2 (plantillas HTML), HTMX, JavaScript, CSS (Tailwind o Bootstrap) |
| **IA/ML** | Google Gemini API (gemini-2.0-flash), Prompt Engineering |
| **Base de Datos** | PostgreSQL |

## 3. Funcionalidades Principales

1. **Creación Inicial (Chat)**
   - Pantalla de chat minimalista
   - IA guía al usuario con preguntas estructuradas:
     - "¿Cuáles son tus objetivos? (aumentar masa, definición, etc.)"
     - "¿Qué equipamiento tienes disponible?"
     - "¿Cuántos días puedes entrenar a la semana?"
   - Construcción progresiva de la rutina durante la conversación
   - Botón "Finalizar y ver rutina" tras confirmación

2. **Dashboard Principal**
   - Visualización semanal de la rutina (3 dias)
   - Cada día muestra ejercicios, series, repeticiones
   - Chat lateral persistente para modificaciones
   - Posibilidad de guardar versiones de la rutina
   - Opción para imprimir/exportar PDF

3. **Chat Lateral para Modificaciones**
   - Historial de conversación mantenido
   - Capacidad para solicitar cambios específicos:
     - "Reemplaza press de banca por flexiones el lunes"
     - "Agrega más ejercicios para piernas el viernes"
     - "Quiero enfocarme más en cardio esta semana"
   - Visualización de los cambios en tiempo real en el dashboard

## 5. Interfaces de Usuario

### 5.1 Pantalla de Chat Inicial
- Diseño minimalista centrado en la conversación
- Indicadores visuales del progreso de creación
- Ejemplos de preguntas sugeridas
- Visualización previa simplificada de la rutina en construcción

### 5.2 Dashboard Principal
- Vista semanal con días organizados horizontalmente
- Tarjetas por ejercicio con información detallada
- Códigos de color según tipo de ejercicio (cardio, fuerza, etc.)
- Panel lateral de chat persistente (30% del ancho)
- Barra superior con acciones (guardar, exportar, compartir)


## 4. AI Features

### 4.1 Tipos de Prompts
- **Prompt de Creación**: Genera rutina completa basada en información inicial
- **Prompt de Modificación**: Modifica aspectos específicos preservando el resto
- **Prompt Explicativo**: Proporciona explicación sobre ejercicios o decisiones
- **Prompt de Sugerencias**: Recomienda mejoras basadas en progresos/feedback

### 4.2 Estructura de Datos de Respuesta
- Rutina completa en formato JSON
- Explicaciones textuales para el usuario
- Metadatos para seguimiento de cambios

### 4.3 Estrategias de Prompt Engineering
- Instrucciones claras sobre formato requerido
- Contexto completo de la rutina actual
- Especificación de restricciones (equipamiento, lesiones)
- Manejo de casos extremos y validaciones

## 5. Integración con Gemini API

### 5.1 Instala la biblioteca necesaria

```
pip install -q -U google-genai
```

## 5.2 Configura la API key como variable de entorno

### En Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY="tu_clave_api_aquí"
```

## 5.3 Crea un servicio para gestionar las interacciones con Gemini

```python
# app/services/gemini_service.py
import json
import os
from google import genai

class GeminiService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"
    
    def _extract_json_from_text(self, text):
        """Extrae el JSON de la respuesta de texto de Gemini"""
        try:
            # Intentar encontrar un bloque JSON en la respuesta
            if "```json" in text and "```" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            # Si no hay formato de código, intentar parsear directamente
            return json.loads(text)
        except:
            # Si falla, devolver un diccionario con el texto como mensaje
            return {"message": text}
    
    def create_initial_routine(self, user_goals, equipment, days_per_week):
        """Genera una rutina inicial basada en los objetivos del usuario"""
        prompt = f"""
        Crea una rutina de entrenamiento personalizada con esta información:
        - Objetivos: {user_goals}
        - Equipamiento disponible: {equipment}
        - Días por semana: {days_per_week}
        
        Devuelve SOLO un JSON estructurado con este formato exacto:
        ```json
        {{
          "routine_name": "Nombre descriptivo de la rutina",
          "days": [
            {{
              "day_name": "Lunes",
              "focus": "Enfoque del día (ej: Pecho y tríceps)",
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
        ```
        No incluyas ningún texto adicional, SOLO el JSON entre las marcas de código.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt]
            )
            
            return self._extract_json_from_text(response.text)
        except Exception as e:
            return {"error": str(e)}
    
    def modify_routine(self, current_routine, user_request):
        """Modifica una rutina existente según la solicitud del usuario"""
        routine_json = json.dumps(current_routine, indent=2)
        
        prompt = f"""
        Modifica esta rutina de entrenamiento según la solicitud del usuario.
        
        RUTINA ACTUAL:
        {routine_json}
        
        SOLICITUD DEL USUARIO: "{user_request}"
        
        Devuelve SOLO la rutina completa ya modificada en formato JSON, con la misma estructura exacta.
        No incluyas ningún texto explicativo, SOLO el JSON entre marcas de código.
        ```json
        (aquí debe ir el JSON modificado)
        ```
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt]
            )
            
            return self._extract_json_from_text(response.text)
        except Exception as e:
            return {"error": str(e)}
    
    def explain_routine_changes(self, old_routine, new_routine, user_request):
        """Explica los cambios realizados a la rutina"""
        old_json = json.dumps(old_routine, indent=2)
        new_json = json.dumps(new_routine, indent=2)
        
        prompt = f"""
        Explica brevemente los cambios realizados a la rutina según esta solicitud: "{user_request}"
        
        RUTINA ANTERIOR:
        {old_json}
        
        RUTINA NUEVA:
        {new_json}
        
        Proporciona una explicación concisa de los cambios principales y por qué son beneficiosos.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt]
            )
            
            return response.text
        except Exception as e:
            return f"Error al explicar cambios: {str(e)}"
```

## 5.4 Integra el servicio en tu aplicación FastAPI

```python
# app/main.py
import os
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.services.gemini_service import GeminiService
from app.db.models import save_routine, get_routine, save_chat_message, get_chat_history
from app.websocket.manager import ConnectionManager

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Verificar API key al inicio
if not os.environ.get("GEMINI_API_KEY"):
    print("⚠️ ADVERTENCIA: GEMINI_API_KEY no encontrada en variables de entorno")
    print("Es necesario definir esta variable antes de ejecutar la aplicación")

manager = ConnectionManager()
gemini_service = GeminiService()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página inicial con chat para crear rutina"""
    return templates.TemplateResponse("chat_initial.html", {"request": request})

@app.post("/api/create_routine")
async def create_routine(request: Request):
    """Endpoint para crear una rutina inicial"""
    data = await request.json()
    user_goals = data.get("goals", "")
    equipment = data.get("equipment", "")
    days_per_week = data.get("days", 3)
    
    # Llamar a Gemini API para generar la rutina
    routine = gemini_service.create_initial_routine(user_goals, equipment, days_per_week)
    
    # Guardar la rutina en la base de datos
    routine_id = await save_routine(routine, user_id=data.get("user_id", 1))
    
    return {"routine_id": routine_id, "routine": routine}

@app.get("/dashboard/{routine_id}", response_class=HTMLResponse)
async def dashboard(request: Request, routine_id: int):
    """Dashboard principal con rutina y chat lateral"""
    routine = await get_routine(routine_id)
    chat_history = await get_chat_history(routine_id)
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "routine": routine,
            "chat_history": chat_history
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
            
            # Guardar mensaje del usuario
            await save_chat_message(routine_id, "user", data)
            
            # Procesar con Gemini API
            modified_routine = gemini_service.modify_routine(current_routine, data)
            
            # Generar explicación de cambios
            explanation = gemini_service.explain_routine_changes(current_routine, modified_routine, data)
            
            # Actualizar la rutina en la BD
            await save_routine(modified_routine, routine_id=routine_id)
            
            # Guardar mensaje de respuesta del asistente
            await save_chat_message(routine_id, "assistant", explanation)
            
            # Enviar actualizaciones al cliente
            await manager.broadcast(routine_id, {
                "type": "routine_update",
                "routine": modified_routine,
                "explanation": explanation
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, routine_id)
```

## 5.5 Crea un Gestor de Conexiones WebSocket

```python
# app/websocket/manager.py
from fastapi import WebSocket
from typing import Dict, List, Any
import json

class ConnectionManager:
    """Gestiona las conexiones WebSocket"""
    
    def __init__(self):
        # Mapeo de routine_id -> lista de conexiones websocket
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, routine_id: int):
        """Conecta un nuevo cliente"""
        await websocket.accept()
        if routine_id not in self.active_connections:
            self.active_connections[routine_id] = []
        self.active_connections[routine_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, routine_id: int):
        """Desconecta un cliente"""
        if routine_id in self.active_connections:
            self.active_connections[routine_id].remove(websocket)
    
    async def broadcast(self, routine_id: int, message: Any):
        """Envía un mensaje a todos los clientes conectados a una rutina específica"""
        if routine_id in self.active_connections:
            for connection in self.active_connections[routine_id]:
                await connection.send_json(message)
```

## 5.6 Verifica la API de Gemini con un test simple

```python
# test_gemini.py
import os
from google import genai

def test_gemini_connection():
    """Prueba simple para verificar la conexión con Gemini API"""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY no encontrada en variables de entorno")
        return False
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=["Describe un ejercicio de gimnasio en una frase corta"]
        )
        print("✅ Conexión exitosa con Gemini API")
        print(f"Respuesta de prueba: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Error al conectarse a Gemini API: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_connection()
```
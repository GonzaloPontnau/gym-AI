from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Exercise(BaseModel):
    """Modelo para un ejercicio"""
    name: str
    sets: int
    reps: str
    rest: str
    equipment: str

class Day(BaseModel):
    """Modelo para un día de entrenamiento"""
    day_name: str
    focus: str
    exercises: List[Exercise]

class Routine(BaseModel):
    """Modelo para una rutina completa"""
    id: Optional[int] = None
    routine_name: str
    user_id: Optional[int] = None
    days: List[Day]

class ChatMessage(BaseModel):
    """Modelo para un mensaje de chat"""
    id: Optional[int] = None
    routine_id: int
    sender: str  # "user" o "assistant"
    content: str
    timestamp: Optional[str] = None
    
class RoutineRequest(BaseModel):
    """Modelo para petición de creación/modificación de rutina"""
    goals: str
    equipment: str
    days: int
    user_id: Optional[int] = 1

class WebSocketMessage(BaseModel):
    """Modelo para mensajes WebSocket"""
    type: str
    data: Dict[str, Any]

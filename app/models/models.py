from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Exercise(BaseModel):
    """Modelo para representar un ejercicio en una rutina"""
    name: str
    sets: int
    reps: str
    rest: str
    equipment: str

class Day(BaseModel):
    """Modelo para representar un día de entrenamiento en una rutina"""
    day_name: str
    focus: str
    exercises: List[Exercise]

class Routine(BaseModel):
    """Modelo para representar una rutina de entrenamiento completa"""
    id: Optional[int] = None
    user_id: int = 1
    routine_name: str
    days: List[Day]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ChatMessage(BaseModel):
    """Modelo para representar un mensaje en el chat"""
    routine_id: int
    sender: str  # "user" o "assistant"
    content: str
    timestamp: Optional[datetime] = None
    
class RoutineRequest(BaseModel):
    """Modelo para solicitar la creación de una rutina"""
    goals: str
    equipment: str = ""
    days: int
    user_id: int = 1

import random
from typing import List, Dict, Any
from datetime import datetime
from app.models.models import Exercise, Day, Routine, RoutineRequest

class RoutineGenerator:
    """Servicio para generar rutinas de entrenamiento"""
    
    def __init__(self):
        # Ya no mantenemos una lista de ejercicios hardcodeados
        # Los días de la semana son útiles para format
        self.days_of_week = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    async def create_initial_routine(self, request: RoutineRequest) -> Routine:
        """
        Este método debe ser sobreescrito por una implementación que use IA
        No hay implementación de respaldo
        """
        raise NotImplementedError("Este método debe ser implementado por una clase derivada que use IA")
    
    async def modify_routine(self, current_routine: Routine, user_request: str) -> Routine:
        """
        Este método debe ser sobreescrito por una implementación que use IA
        No hay implementación de respaldo
        """
        raise NotImplementedError("Este método debe ser implementado por una clase derivada que use IA")
    
    async def explain_routine_changes(self, old_routine: Routine, new_routine: Routine, user_request: str) -> str:
        """
        Este método debe ser sobreescrito por una implementación que use IA
        No hay implementación de respaldo
        """
        raise NotImplementedError("Este método debe ser implementado por una clase derivada que use IA")

    async def delete_routine(self, routine_id: int) -> bool:
        """Elimina una rutina de la base de datos por su ID"""
        try:
            # Esta implementación sigue siendo válida ya que delega a la base de datos
            from app.db.database import delete_routine_from_db
            return await delete_routine_from_db(routine_id)
        except Exception as e:
            print(f"Error al eliminar rutina: {str(e)}")
            return False
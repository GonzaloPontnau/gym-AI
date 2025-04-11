import random
from typing import List, Dict, Any
from datetime import datetime
from app.models.models import Exercise, Day, Routine, RoutineRequest

class RoutineGenerator:
    """Servicio para generar rutinas de entrenamiento como respaldo"""
    
    def __init__(self):
        # Mapeo de días de la semana
        self.days_of_week = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        # Ejercicios básicos simplificados
        self.basic_exercises = [
            {"name": "Flexiones", "equipment": "peso corporal"},
            {"name": "Sentadillas", "equipment": "peso corporal"},
            {"name": "Dominadas", "equipment": "barra"},
            {"name": "Plancha", "equipment": "peso corporal"},
            {"name": "Burpees", "equipment": "peso corporal"}
        ]
    
    async def create_initial_routine(self, request: RoutineRequest) -> Routine:
        """Genera una rutina básica de respaldo"""
        days_count = min(request.days, 7)
        routine_name = f"Rutina de entrenamiento - {days_count} días"
        
        days = []
        for i in range(days_count):
            # Crear 3-4 ejercicios por día
            exercises = []
            selected_exercises = random.sample(self.basic_exercises, min(4, len(self.basic_exercises)))
            
            for ex in selected_exercises:
                exercise = Exercise(
                    name=ex["name"],
                    sets=3,
                    reps="10-12",
                    rest="60 seg",
                    equipment=ex["equipment"]
                )
                exercises.append(exercise)
            
            day = Day(
                day_name=self.days_of_week[i],
                focus="Entrenamiento general",
                exercises=exercises
            )
            days.append(day)
        
        return Routine(
            routine_name=routine_name,
            user_id=request.user_id,
            days=days
        )
    
    async def modify_routine(self, current_routine: Routine, user_request: str) -> Routine:
        """Modifica una rutina existente de manera simple (respaldo)"""
        modified_routine = current_routine.model_copy(deep=True)
        
        # Añadir un ejercicio adicional a cada día como respaldo
        for day in modified_routine.days:
            day_exercise_names = [e.name for e in day.exercises]
            available_exercises = [e for e in self.basic_exercises if e["name"] not in day_exercise_names]
            
            if available_exercises:
                new_exercise_data = random.choice(available_exercises)
                exercise = Exercise(
                    name=new_exercise_data["name"],
                    sets=3,
                    reps="10-12",
                    rest="60 seg",
                    equipment=new_exercise_data["equipment"]
                )
                day.exercises.append(exercise)
        
        return modified_routine
    
    async def explain_routine_changes(self, old_routine: Routine, new_routine: Routine, user_request: str) -> str:
        """Genera una explicación simple de los cambios realizados a la rutina"""
        explanation = "He modificado tu rutina según tu solicitud:\n\n"
        
        # Comparar días y ejercicios
        for old_day, new_day in zip(old_routine.days, new_routine.days):
            old_exercises = set(e.name for e in old_day.exercises)
            new_exercises = set(e.name for e in new_day.exercises)
            
            added = new_exercises - old_exercises
            removed = old_exercises - new_exercises
            
            if added:
                explanation += f"- {old_day.day_name}: Añadí {', '.join(added)}\n"
            
            if removed:
                explanation += f"- {old_day.day_name}: Eliminé {', '.join(removed)}\n"
        
        # Si no hay cambios detectados
        if explanation == "He modificado tu rutina según tu solicitud:\n\n":
            explanation += "No se detectaron cambios en la rutina. Intenta ser más específico con tu solicitud."
            
        return explanation

    async def delete_routine(self, routine_id: int) -> bool:
        """Elimina una rutina de la base de datos por su ID"""
        try:
            # Implementación simplificada usando el acceso a base de datos
            from app.db.database import delete_routine_from_db
            return await delete_routine_from_db(routine_id)
        except Exception as e:
            print(f"Error al eliminar rutina: {str(e)}")
            return False
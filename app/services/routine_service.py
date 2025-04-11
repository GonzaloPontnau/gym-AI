import json
import random
import os
from typing import List, Dict, Any
from datetime import datetime
from app.models.models import Exercise, Day, Routine, RoutineRequest

class RoutineGenerator:
    """Servicio para generar rutinas de entrenamiento como respaldo"""
    
    def __init__(self):
        # Mapeo de días de la semana
        self.days_of_week = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        # Ejercicios básicos para usar como respaldo
        self.basic_exercises = [
            {"name": "Flexiones", "equipment": "peso corporal"},
            {"name": "Sentadillas", "equipment": "peso corporal"},
            {"name": "Dominadas", "equipment": "barra de dominadas"},
            {"name": "Plancha", "equipment": "peso corporal"},
            {"name": "Zancadas", "equipment": "peso corporal"},
            {"name": "Fondos", "equipment": "peso corporal"},
            {"name": "Jumping jacks", "equipment": "ninguno"},
            {"name": "Mountain climbers", "equipment": "peso corporal"},
            {"name": "Burpees", "equipment": "peso corporal"},
            {"name": "Abdominales", "equipment": "peso corporal"}
        ]
    
    async def create_initial_routine(self, request: RoutineRequest) -> Routine:
        """Genera una rutina básica de respaldo"""
        days_count = min(request.days, 7)  # Máximo 7 días
        
        # Crear el nombre de la rutina
        routine_name = f"Rutina de entrenamiento - {days_count} días"
        
        # Generar los días de entrenamiento
        days = []
        for i in range(days_count):
            # Crear ejercicios aleatorios como respaldo
            exercises = []
            selected_exercises = random.sample(self.basic_exercises, min(5, len(self.basic_exercises)))
            
            for ex in selected_exercises:
                exercise = Exercise(
                    name=ex["name"],
                    sets=3,
                    reps="10-15",
                    rest="60 seg",
                    equipment=ex["equipment"]
                )
                exercises.append(exercise)
            
            # Crear el día con todos sus ejercicios
            day = Day(
                day_name=self.days_of_week[i],
                focus="Entrenamiento general",
                exercises=exercises
            )
            days.append(day)
        
        # Crear y devolver la rutina completa
        return Routine(
            routine_name=routine_name,
            user_id=request.user_id,
            days=days
        )
    
    async def modify_routine(self, current_routine: Routine, user_request: str) -> Routine:
        """Modifica una rutina existente de manera simple (respaldo)"""
        # Hacer una copia de la rutina actual para modificarla
        modified_routine = current_routine.model_copy(deep=True)
        
        # Como respaldo, simplemente añadir un ejercicio adicional a cada día
        for day in modified_routine.days:
            # Elegir un ejercicio que no esté ya en el día
            day_exercise_names = [e.name for e in day.exercises]
            available_exercises = [e for e in self.basic_exercises if e["name"] not in day_exercise_names]
            
            if available_exercises:
                new_exercise_data = random.choice(available_exercises)
                exercise = Exercise(
                    name=new_exercise_data["name"],
                    sets=3,
                    reps="10-15",
                    rest="60 seg",
                    equipment=new_exercise_data["equipment"]
                )
                day.exercises.append(exercise)
        
        return modified_routine
    
    async def explain_routine_changes(self, old_routine: Routine, new_routine: Routine, user_request: str) -> str:
        """Genera una explicación simple de los cambios realizados a la rutina"""
        explanation = "He modificado tu rutina según tu solicitud:\n\n"
        
        # Comparar días
        for old_day, new_day in zip(old_routine.days, new_routine.days):
            # Verificar si hubo cambios en los ejercicios
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
            explanation += "No se detectaron cambios significativos en la rutina. Por favor, sé más específico con tu solicitud."
            
        return explanation

    async def delete_routine(self, routine_id: int) -> bool:
        """
        Elimina una rutina de la base de datos por su ID
        
        Args:
            routine_id: ID de la rutina a eliminar
        
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario
        """
        try:
            # Implementación según el tipo de almacenamiento utilizado:
            
            # Opción 1: Si usas SQLAlchemy con FastAPI
            from app.database import get_db
            from sqlalchemy.orm import Session
            from app.models.db_models import RoutineDB  # Asumiendo que este es tu modelo de base de datos
            
            db = next(get_db())
            routine = db.query(RoutineDB).filter(RoutineDB.id == routine_id).first()
            if routine:
                db.delete(routine)
                db.commit()
                return True
            return False
            
            # Opción 2: Si usas MongoDB
            # from app.database import get_mongo_client
            # 
            # db = get_mongo_client().get_database("gym_ai")
            # result = db.routines.delete_one({"_id": routine_id})
            # return result.deleted_count > 0
            
            # Opción 3: Si usas almacenamiento JSON
            # data_file = "app/data/routines.json"
            # if os.path.exists(data_file):
            #     with open(data_file, "r") as f:
            #         routines = json.load(f)
            #     
            #     # Filtrar la rutina a eliminar
            #     routines = [r for r in routines if r.get("id") != routine_id]
            #     
            #     # Guardar el archivo actualizado
            #     with open(data_file, "w") as f:
            #         json.dump(routines, f, indent=2)
            #     
            #     return True
            # return False
            
        except Exception as e:
            print(f"Error al eliminar rutina: {str(e)}")
            return False
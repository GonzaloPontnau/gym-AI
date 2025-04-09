import json
import random
from typing import List, Dict, Any
from datetime import datetime
from app.models.models import Exercise, Day, Routine, RoutineRequest

class RoutineGenerator:
    """Servicio para generar rutinas de entrenamiento sin API externa"""
    
    def __init__(self):
        # Catálogo de ejercicios por grupo muscular
        self.exercise_catalog = {
            "pecho": [
                {"name": "Press de banca", "equipment": "barra y banco"},
                {"name": "Flexiones", "equipment": "peso corporal"},
                {"name": "Press con mancuernas", "equipment": "mancuernas"},
                {"name": "Aperturas con mancuernas", "equipment": "mancuernas"},
                {"name": "Fondos en paralelas", "equipment": "paralelas"}
            ],
            "espalda": [
                {"name": "Dominadas", "equipment": "barra de dominadas"},
                {"name": "Remo con barra", "equipment": "barra"},
                {"name": "Remo con mancuerna", "equipment": "mancuerna"},
                {"name": "Pulldown en polea", "equipment": "máquina de poleas"},
                {"name": "Peso muerto", "equipment": "barra"}
            ],
            "hombros": [
                {"name": "Press militar", "equipment": "barra o mancuernas"},
                {"name": "Elevaciones laterales", "equipment": "mancuernas"},
                {"name": "Elevaciones frontales", "equipment": "mancuernas"},
                {"name": "Pájaros", "equipment": "mancuernas"},
                {"name": "Face pull", "equipment": "polea"}
            ],
            "piernas": [
                {"name": "Sentadillas", "equipment": "barra o peso corporal"},
                {"name": "Prensa", "equipment": "máquina"},
                {"name": "Extensiones de cuádriceps", "equipment": "máquina"},
                {"name": "Curl de isquiotibiales", "equipment": "máquina"},
                {"name": "Zancadas", "equipment": "mancuernas o peso corporal"}
            ],
            "brazos": [
                {"name": "Curl con barra", "equipment": "barra"},
                {"name": "Curl con mancuernas", "equipment": "mancuernas"},
                {"name": "Press francés", "equipment": "barra o mancuerna"},
                {"name": "Extensiones de tríceps en polea", "equipment": "polea"},
                {"name": "Fondos para tríceps", "equipment": "banco o paralelas"}
            ],
            "core": [
                {"name": "Crunches", "equipment": "peso corporal"},
                {"name": "Plancha", "equipment": "peso corporal"},
                {"name": "Russian twist", "equipment": "peso corporal o peso libre"},
                {"name": "Elevación de piernas", "equipment": "peso corporal"},
                {"name": "Rueda abdominal", "equipment": "rueda abdominal"}
            ],
            "cardio": [
                {"name": "Carrera continua", "equipment": "ninguno"},
                {"name": "HIIT", "equipment": "ninguno"},
                {"name": "Saltos", "equipment": "ninguno"},
                {"name": "Burpees", "equipment": "ninguno"},
                {"name": "Jump Rope", "equipment": "cuerda"}
            ]
        }
        
        # Tipos de rutinas según objetivo
        self.routine_types = {
            "masa": {
                "sets": 4,
                "reps": "6-8",
                "rest": "90-120 seg",
                "focus_map": ["pecho/tríceps", "espalda/bíceps", "piernas/hombros"]
            },
            "definición": {
                "sets": 3,
                "reps": "12-15",
                "rest": "45-60 seg",
                "focus_map": ["pecho/hombros", "espalda/brazos", "piernas/core"]
            },
            "fuerza": {
                "sets": 5,
                "reps": "3-5",
                "rest": "180-240 seg",
                "focus_map": ["pecho/tríceps", "espalda/bíceps", "piernas"]
            },
            "resistencia": {
                "sets": 3,
                "reps": "15-20",
                "rest": "30-45 seg",
                "focus_map": ["pecho/espalda", "piernas/core", "fullbody"]
            },
            "mantenimiento": {
                "sets": 3,
                "reps": "10-12",
                "rest": "60 seg",
                "focus_map": ["empuje", "tirón", "piernas/core"]
            }
        }
        
        # Mapeo de días de la semana
        self.days_of_week = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        # Mapeo de grupos musculares por tipo de entrenamiento
        self.muscle_group_map = {
            "pecho/tríceps": ["pecho", "brazos"],
            "espalda/bíceps": ["espalda", "brazos"],
            "piernas/hombros": ["piernas", "hombros"],
            "pecho/hombros": ["pecho", "hombros"],
            "espalda/brazos": ["espalda", "brazos"],
            "piernas/core": ["piernas", "core"],
            "pecho/espalda": ["pecho", "espalda"],
            "fullbody": ["pecho", "espalda", "hombros", "piernas", "core"],
            "empuje": ["pecho", "hombros", "brazos"],
            "tirón": ["espalda", "brazos"]
        }
    
    def _determine_routine_type(self, goals: str) -> str:
        """Determina el tipo de rutina basado en los objetivos del usuario"""
        goals = goals.lower()
        
        if any(keyword in goals for keyword in ["masa", "volumen", "hipertrofia", "crecer", "aumentar", "tamaño"]):
            return "masa"
        elif any(keyword in goals for keyword in ["definición", "definir", "marcar", "tonificar"]):
            return "definición"
        elif any(keyword in goals for keyword in ["fuerza", "fuerte", "potencia"]):
            return "fuerza"
        elif any(keyword in goals for keyword in ["resistencia", "aguante", "cardio", "quemar", "adelgazar"]):
            return "resistencia"
        else:
            return "mantenimiento"
    
    def _filter_by_equipment(self, exercises: List[Dict], available_equipment: str) -> List[Dict]:
        """Filtra ejercicios en base al equipamiento disponible"""
        available_equipment = available_equipment.lower()
        
        # Palabras clave para equipamiento común
        equipment_keywords = {
            "casa": ["peso corporal", "mancuernas", "ninguno"],
            "gym": ["todas", "barra", "máquina", "polea"],
            "mancuernas": ["mancuernas", "peso libre"],
            "barra": ["barra"],
            "máquina": ["máquina", "polea"]
        }
        
        # Determinar qué equipamiento tiene disponible
        has_equipment = []
        for key, terms in equipment_keywords.items():
            if any(term in available_equipment for term in [key]):
                has_equipment.extend(terms)
        
        # Si menciona "todo" o "completo", considera que tiene todo el equipamiento
        if any(term in available_equipment for term in ["todo", "completo", "gym", "gimnasio"]):
            return exercises
        
        # Si es casa o no menciona equipamiento específico, asumir básico
        if not has_equipment or "casa" in available_equipment:
            has_equipment = equipment_keywords["casa"]
        
        # Filtrar ejercicios por equipamiento disponible
        filtered = []
        for exercise in exercises:
            equip = exercise["equipment"].lower()
            if any(term in equip for term in has_equipment) or "peso corporal" in equip or "ninguno" in equip:
                filtered.append(exercise)
                
        # Si no hay ejercicios filtrados, devolver ejercicios con peso corporal
        if not filtered:
            return [e for e in exercises if "peso corporal" in e["equipment"].lower() or "ninguno" in e["equipment"].lower()]
            
        return filtered
    
    async def create_initial_routine(self, request: RoutineRequest) -> Routine:
        """Genera una rutina inicial basada en los objetivos del usuario"""
        routine_type = self._determine_routine_type(request.goals)
        days_count = min(request.days, 7)  # Máximo 7 días
        
        # Configurar la rutina según el tipo
        routine_config = self.routine_types[routine_type]
        
        # Crear el nombre de la rutina
        routine_name = f"Rutina de {routine_type.capitalize()} - {days_count} días"
        
        # Generar los días de entrenamiento
        days = []
        for i in range(days_count):
            # Determinar el enfoque del día usando una rotación cíclica
            focus_index = i % len(routine_config["focus_map"])
            focus = routine_config["focus_map"][focus_index]
            
            # Seleccionar los grupos musculares para este enfoque
            muscle_groups = self.muscle_group_map[focus]
            
            # Crear los ejercicios para este día
            exercises = []
            for group in muscle_groups:
                # Seleccionar 2-3 ejercicios por grupo muscular
                num_exercises = random.randint(2, 3)
                group_exercises = self._filter_by_equipment(self.exercise_catalog[group], request.equipment)
                
                # Si hay suficientes ejercicios, seleccionar aleatoriamente
                selected_exercises = random.sample(group_exercises, min(num_exercises, len(group_exercises)))
                
                # Añadir configuración de series, repeticiones, descanso
                for ex in selected_exercises:
                    exercise = Exercise(
                        name=ex["name"],
                        sets=routine_config["sets"],
                        reps=routine_config["reps"],
                        rest=routine_config["rest"],
                        equipment=ex["equipment"]
                    )
                    exercises.append(exercise)
            
            # Crear el día con todos sus ejercicios
            day = Day(
                day_name=self.days_of_week[i],
                focus=focus.replace("/", " y ").capitalize(),
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
        """Modifica una rutina existente según la solicitud del usuario"""
        # Hacer una copia de la rutina actual para modificarla
        modified_routine = current_routine.model_copy(deep=True)
        
        # Analizar la solicitud del usuario para determinar qué cambios hacer
        request = user_request.lower()
        
        # Caso 1: Cambio de ejercicio específico
        if any(term in request for term in ["reemplaza", "cambia", "sustituye"]):
            # Buscar el día mencionado (lunes, martes, etc.)
            day_mentioned = None
            for day in self.days_of_week:
                if day.lower() in request:
                    day_mentioned = day
                    break
            
            # Buscar los ejercicios mencionados para reemplazar
            exercise_to_replace = None
            for day in modified_routine.days:
                for i, exercise in enumerate(day.exercises):
                    if exercise.name.lower() in request:
                        exercise_to_replace = (day, i, exercise)
                        break
                if exercise_to_replace:
                    break
            
            # Si encontramos un ejercicio para reemplazar
            if exercise_to_replace:
                day, exercise_index, old_exercise = exercise_to_replace
                
                # Determinar grupo muscular del ejercicio
                muscle_group = None
                for group, exercises in self.exercise_catalog.items():
                    if any(e["name"].lower() == old_exercise.name.lower() for e in exercises):
                        muscle_group = group
                        break
                
                if muscle_group:
                    # Filtrar los ejercicios del mismo grupo muscular
                    group_exercises = self._filter_by_equipment(
                        self.exercise_catalog[muscle_group], 
                        "todo"  # Aquí usamos "todo" para tener más opciones
                    )
                    
                    # Elegir un nuevo ejercicio que no sea el actual
                    new_exercises = [e for e in group_exercises if e["name"].lower() != old_exercise.name.lower()]
                    if new_exercises:
                        new_exercise_data = random.choice(new_exercises)
                        # Mantener la configuración de series, repeticiones, etc.
                        day.exercises[exercise_index] = Exercise(
                            name=new_exercise_data["name"],
                            sets=old_exercise.sets,
                            reps=old_exercise.reps,
                            rest=old_exercise.rest,
                            equipment=new_exercise_data["equipment"]
                        )
        
        # Caso 2: Agregar más ejercicios para un grupo muscular
        elif any(term in request for term in ["agregar", "añadir", "más"]):
            # Identificar el grupo muscular mencionado
            target_group = None
            for group in self.exercise_catalog.keys():
                if group in request:
                    target_group = group
                    break
            
            # Identificar el día mencionado
            target_day = None
            for day in modified_routine.days:
                if day.day_name.lower() in request:
                    target_day = day
                    break
            
            # Si tenemos un grupo y un día objetivo, agregar ejercicios
            if target_group and target_day:
                # Obtener ejercicios actuales para evitar duplicaciones
                current_exercises = [e.name.lower() for e in target_day.exercises]
                
                # Filtrar ejercicios disponibles
                group_exercises = self._filter_by_equipment(
                    self.exercise_catalog[target_group], 
                    "todo"  # Aquí usamos "todo" para tener más opciones
                )
                
                # Seleccionar ejercicios no duplicados
                new_exercises = [e for e in group_exercises if e["name"].lower() not in current_exercises]
                
                # Agregar 1-2 nuevos ejercicios
                num_to_add = min(random.randint(1, 2), len(new_exercises))
                if new_exercises and num_to_add > 0:
                    selected = random.sample(new_exercises, num_to_add)
                    
                    # Usar la configuración del primer ejercicio existente como referencia
                    reference = target_day.exercises[0] if target_day.exercises else None
                    
                    # Agregar nuevos ejercicios
                    for ex in selected:
                        target_day.exercises.append(Exercise(
                            name=ex["name"],
                            sets=reference.sets if reference else 3,
                            reps=reference.reps if reference else "10-12",
                            rest=reference.rest if reference else "60 seg",
                            equipment=ex["equipment"]
                        ))
        
        # Caso 3: Cambiar el enfoque de la rutina
        elif any(term in request for term in ["enfoque", "enfocar", "concentrar"]):
            routine_type = None
            for rt in self.routine_types.keys():
                if rt in request:
                    routine_type = rt
                    break
            
            # Si se especificó un nuevo enfoque, actualizar la rutina
            if routine_type:
                routine_config = self.routine_types[routine_type]
                modified_routine.routine_name = f"Rutina de {routine_type.capitalize()} - {len(modified_routine.days)} días"
                
                # Actualizar configuración de ejercicios
                for day in modified_routine.days:
                    for exercise in day.exercises:
                        exercise.sets = routine_config["sets"]
                        exercise.reps = routine_config["reps"]
                        exercise.rest = routine_config["rest"]
        
        return modified_routine
    
    async def explain_routine_changes(self, old_routine: Routine, new_routine: Routine, user_request: str) -> str:
        """Genera una explicación de los cambios realizados a la rutina"""
        explanation = "He modificado tu rutina según tu solicitud:\n\n"
        
        # Comparar nombres de rutina
        if old_routine.routine_name != new_routine.routine_name:
            explanation += f"- Cambié el enfoque de la rutina a {new_routine.routine_name}\n"
        
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
                # Buscar reemplazos
                for ex in removed:
                    old_ex = next((e for e in old_day.exercises if e.name == ex), None)
                    # Verificar si hay un nuevo ejercicio que no estaba antes
                    for new_ex in new_day.exercises:
                        if new_ex.name in added:
                            explanation += f"- {old_day.day_name}: Reemplacé {ex} por {new_ex.name}\n"
                            break
            
            # Verificar cambios en series/repeticiones
            for i, (old_ex, new_ex) in enumerate(zip(old_day.exercises, new_day.exercises)):
                if old_ex.name == new_ex.name and (old_ex.sets != new_ex.sets or old_ex.reps != new_ex.reps):
                    explanation += f"- {old_day.day_name}: Ajusté {old_ex.name} de {old_ex.sets}x{old_ex.reps} a {new_ex.sets}x{new_ex.reps}\n"
        
        # Si no hay cambios detectados
        if explanation == "He modificado tu rutina según tu solicitud:\n\n":
            explanation += "No se detectaron cambios significativos en la rutina. Por favor, sé más específico con tu solicitud."
            
        return explanation
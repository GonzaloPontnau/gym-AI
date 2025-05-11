"""
Pruebas simples para los modelos de la aplicación sin dependencias externas
"""
import sys
import os
import json

# Ajustar path para importar desde directorio raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importar modelos
from app.models.models import Routine, Day, Exercise, RoutineRequest

class TestModels:
    """Pruebas para modelos Pydantic"""
    
    def test_exercise_creation(self):
        """Verificar la creación de un ejercicio"""
        exercise = Exercise(
            name="Press de banca",
            sets=3,
            reps="8-12",
            rest="60-90 seg",
            equipment="Barra y banco"
        )
        
        assert exercise.name == "Press de banca"
        assert exercise.sets == 3
        assert exercise.reps == "8-12"
        assert exercise.rest == "60-90 seg"
        assert exercise.equipment == "Barra y banco"
    
    def test_day_creation(self):
        """Verificar la creación de un día de entrenamiento"""
        day = Day(
            day_name="Lunes",
            focus="Pecho",
            exercises=[
                Exercise(
                    name="Press de banca",
                    sets=3,
                    reps="8-12",
                    rest="60-90 seg",
                    equipment="Barra y banco"
                )
            ]
        )
        
        assert day.day_name == "Lunes"
        assert day.focus == "Pecho"
        assert len(day.exercises) == 1
        assert day.exercises[0].name == "Press de banca"
    
    def test_routine_creation(self):
        """Verificar la creación de una rutina completa"""
        routine = Routine(
            routine_name="Rutina de prueba",
            user_id=1,
            days=[
                Day(
                    day_name="Lunes",
                    focus="Pecho",
                    exercises=[
                        Exercise(
                            name="Press de banca",
                            sets=3,
                            reps="8-12",
                            rest="60-90 seg",
                            equipment="Barra y banco"
                        )
                    ]
                ),
                Day(
                    day_name="Miércoles",
                    focus="Espalda",
                    exercises=[
                        Exercise(
                            name="Dominadas",
                            sets=3,
                            reps="8-12",
                            rest="60-90 seg",
                            equipment="Barra"
                        )
                    ]
                )
            ]
        )
        
        assert routine.routine_name == "Rutina de prueba"
        assert routine.user_id == 1
        assert len(routine.days) == 2
        assert routine.days[0].day_name == "Lunes"
        assert routine.days[1].day_name == "Miércoles"
    
    def test_json_serialization(self):
        """Verificar la serialización a JSON"""
        routine = Routine(
            routine_name="Rutina de serialización",
            user_id=1,
            days=[
                Day(
                    day_name="Lunes",
                    focus="Pecho",
                    exercises=[
                        Exercise(
                            name="Press de banca",
                            sets=3,
                            reps="8-12",
                            rest="60-90 seg",
                            equipment="Barra y banco"
                        )
                    ]
                )
            ]
        )
        
        # Serializar a JSON
        json_data = routine.model_dump_json()
        
        # Deserializar de JSON
        data_dict = json.loads(json_data)
        
        # Verificar datos
        assert data_dict["routine_name"] == "Rutina de serialización"
        assert data_dict["user_id"] == 1
        assert len(data_dict["days"]) == 1
        assert data_dict["days"][0]["day_name"] == "Lunes"
        assert len(data_dict["days"][0]["exercises"]) == 1
        assert data_dict["days"][0]["exercises"][0]["name"] == "Press de banca"
    
    def test_routine_request(self):
        """Verificar modelo de solicitud de rutina"""
        request = RoutineRequest(
            goals="Hipertrofia",
            equipment="Gimnasio completo",
            days=3,
            user_id=1
        )
        
        assert request.goals == "Hipertrofia"
        assert request.equipment == "Gimnasio completo"
        assert request.days == 3
        assert request.user_id == 1 
import pytest
from pydantic import ValidationError
from app.models.models import Routine, Day, Exercise, RoutineRequest

class TestModels:
    """Pruebas para los modelos Pydantic"""
    
    def test_exercise_model_valid(self):
        """Verificar que un ejercicio válido se crea correctamente"""
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
    
    def test_day_model_valid(self):
        """Verificar que un día válido se crea correctamente"""
        day = Day(
            day_name="Lunes",
            focus="Pecho y tríceps",
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
        assert day.focus == "Pecho y tríceps"
        assert len(day.exercises) == 1
        assert day.exercises[0].name == "Press de banca"
    
    def test_routine_model_valid(self, sample_routine):
        """Verificar que una rutina válida se crea correctamente"""
        assert sample_routine.routine_name == "Rutina de prueba"
        assert sample_routine.user_id == 1
        assert len(sample_routine.days) == 2
        assert sample_routine.days[0].day_name == "Lunes"
        assert sample_routine.days[1].day_name == "Miércoles"
    
    def test_routine_request_model_valid(self):
        """Verificar que una solicitud de rutina válida se crea correctamente"""
        routine_request = RoutineRequest(
            goals="Hipertrofia",
            equipment="Gimnasio completo",
            days=4,
            user_id=1
        )
        
        assert routine_request.goals == "Hipertrofia"
        assert routine_request.equipment == "Gimnasio completo"
        assert routine_request.days == 4
        assert routine_request.user_id == 1
    
    def test_routine_request_model_default_values(self):
        """Verificar valores predeterminados en RoutineRequest"""
        routine_request = RoutineRequest(
            goals="Hipertrofia",
            days=4
        )
        
        assert routine_request.goals == "Hipertrofia"
        assert routine_request.equipment == ""  # Valor predeterminado
        assert routine_request.days == 4
        assert routine_request.user_id == 1  # Valor predeterminado 
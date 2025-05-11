import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

class TestAPIEndpoints:
    """Pruebas para los endpoints de la API"""
    
    def test_health_check(self, test_client):
        """Probar el endpoint de verificación de salud"""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "ok"
    
    def test_get_root(self, test_client):
        """Probar la página inicial (chat_initial.html)"""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "html" in response.text.lower()
        assert "gym" in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_create_routine(self, test_client, monkeypatch):
        """Probar la creación de una rutina a través de la API"""
        # Crear un mock para gemini_service.GeminiRoutineGenerator.create_initial_routine
        async def mock_create_initial_routine(*args, **kwargs):
            from app.models.models import Routine, Day, Exercise
            return Routine(
                routine_name="Rutina de prueba API",
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
        
        # Patch para save_routine
        async def mock_save_routine(*args, **kwargs):
            return 1  # ID de la rutina
            
        # Patch para save_chat_message
        async def mock_save_chat_message(*args, **kwargs):
            return 1  # ID del mensaje
        
        # Parchar GEMINI_CONFIGURED para que sea True
        monkeypatch.setattr("app.services.gemini_service.GEMINI_CONFIGURED", True)
        
        # Aplicar los parches
        with patch("app.main.routine_generator.create_initial_routine", mock_create_initial_routine):
            with patch("app.main.save_routine", mock_save_routine):
                with patch("app.main.save_chat_message", mock_save_chat_message):
                    # Datos para la solicitud
                    data = {
                        "goals": "Hipertrofia",
                        "equipment": "Gimnasio completo",
                        "days": 3,
                        "experience_level": "Intermedio",
                        "available_equipment": "Pesas, máquinas",
                        "time_per_session": "60 min",
                        "health_conditions": "",
                        "user_id": 1
                    }
                    
                    # Enviar solicitud
                    response = test_client.post("/api/create_routine", json=data)
                    
                    # Verificar respuesta
                    assert response.status_code == 200
                    assert "routine_id" in response.json()
                    assert response.json()["routine_id"] == 1
                    assert "routine" in response.json()
                    assert response.json()["routine"]["routine_name"] == "Rutina de prueba API"
    
    @pytest.mark.asyncio
    async def test_get_routines_list(self, test_client, monkeypatch):
        """Probar la obtención de la lista de rutinas"""
        # Mock para get_user_routines
        async def mock_get_user_routines(*args, **kwargs):
            return [
                {"id": 1, "routine_name": "Rutina 1", "updated_at": "2023-01-01T00:00:00"},
                {"id": 2, "routine_name": "Rutina 2", "updated_at": "2023-01-02T00:00:00"}
            ]
        
        # Aplicar el parche
        with patch("app.main.get_user_routines", mock_get_user_routines):
            # Obtener lista de rutinas
            response = test_client.get("/routines?user_id=1")
            
            # Verificar respuesta
            assert response.status_code == 200
            assert "html" in response.text.lower()
            assert "Rutina 1" in response.text
            assert "Rutina 2" in response.text
    
    @pytest.mark.asyncio
    async def test_delete_routine(self, test_client, monkeypatch):
        """Probar la eliminación de una rutina"""
        # Mock para delete_routine_from_db
        async def mock_delete_routine_from_db(*args, **kwargs):
            return True
        
        # Aplicar el parche
        with patch("app.main.delete_routine_from_db", mock_delete_routine_from_db):
            # Enviar solicitud de eliminación
            response = test_client.post(
                "/delete_routine", 
                data={"routine_id": 1},
                follow_redirects=False
            )
            
            # Verificar redirección
            assert response.status_code == 303
            assert response.headers["location"] == "/routines?success=true&action=delete" 
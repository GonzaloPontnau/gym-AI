import pytest
import os
import tempfile
import json
from app.sqlite_helper import (
    ensure_db_exists,
    save_routine_sync,
    get_routine_sync,
    save_chat_message_sync,
    get_chat_history_sync,
    get_user_routines_sync,
    delete_routine_sync
)

class TestSQLiteHelper:
    """Pruebas para las funciones de SQLite Helper"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, monkeypatch):
        """Configurar y limpiar después de cada prueba"""
        # Crear un directorio temporal para la base de datos
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_gym.db")
        
        # Redefinir la función ensure_db_exists para usar la BD temporal
        def mock_ensure_db_exists():
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            return self.db_path
        
        # Aplicar el patch
        monkeypatch.setattr("app.sqlite_helper.ensure_db_exists", mock_ensure_db_exists)
        
        yield
        
        # Limpiar
        self.temp_dir.cleanup()
    
    def test_save_and_get_routine(self):
        """Prueba para guardar y recuperar una rutina"""
        # Datos de prueba
        routine_dict = {
            "routine_name": "Rutina de prueba",
            "days": [
                {
                    "day_name": "Lunes",
                    "focus": "Pecho y tríceps",
                    "exercises": [
                        {
                            "name": "Press de banca",
                            "sets": 3,
                            "reps": "8-12",
                            "rest": "60-90 seg",
                            "equipment": "Barra y banco"
                        }
                    ]
                }
            ]
        }
        
        # Guardar rutina
        routine_id = save_routine_sync(routine_dict, user_id=1)
        
        # Verificar que se haya guardado con un ID
        assert routine_id is not None
        assert routine_id > 0
        
        # Recuperar rutina
        retrieved_routine = get_routine_sync(routine_id)
        
        # Verificar que los datos sean correctos
        assert retrieved_routine is not None
        assert retrieved_routine["routine_name"] == "Rutina de prueba"
        assert len(retrieved_routine["days"]) == 1
        assert retrieved_routine["days"][0]["day_name"] == "Lunes"
        assert len(retrieved_routine["days"][0]["exercises"]) == 1
        assert retrieved_routine["days"][0]["exercises"][0]["name"] == "Press de banca"
    
    def test_save_and_get_chat_messages(self):
        """Prueba para guardar y recuperar mensajes de chat"""
        # Datos de prueba
        routine_dict = {"routine_name": "Test Routine", "days": []}
        routine_id = save_routine_sync(routine_dict, user_id=1)
        
        # Guardar mensajes
        message_id1 = save_chat_message_sync(routine_id, "user", "Hola, necesito una rutina")
        message_id2 = save_chat_message_sync(routine_id, "assistant", "Claro, aquí tienes una rutina")
        
        # Verificar IDs
        assert message_id1 is not None
        assert message_id2 is not None
        
        # Recuperar mensajes
        messages = get_chat_history_sync(routine_id)
        
        # Verificar mensajes
        assert len(messages) == 2
        assert messages[0]["sender"] == "user"
        assert messages[0]["content"] == "Hola, necesito una rutina"
        assert messages[1]["sender"] == "assistant"
        assert messages[1]["content"] == "Claro, aquí tienes una rutina"
    
    def test_get_user_routines(self):
        """Prueba para obtener rutinas de un usuario"""
        # Crear algunas rutinas
        save_routine_sync({"routine_name": "Rutina 1", "days": []}, user_id=1)
        save_routine_sync({"routine_name": "Rutina 2", "days": []}, user_id=1)
        save_routine_sync({"routine_name": "Rutina 3", "days": []}, user_id=2)
        
        # Obtener rutinas del usuario 1
        routines = get_user_routines_sync(1)
        
        # Verificar
        assert len(routines) == 2
        assert routines[0]["routine_name"] == "Rutina 2"  # Ordenado por fecha, más reciente primero
        assert routines[1]["routine_name"] == "Rutina 1"
        
        # Obtener rutinas del usuario 2
        routines = get_user_routines_sync(2)
        
        # Verificar
        assert len(routines) == 1
        assert routines[0]["routine_name"] == "Rutina 3"
    
    def test_delete_routine(self):
        """Prueba para eliminar una rutina"""
        # Crear una rutina
        routine_id = save_routine_sync({"routine_name": "Rutina a eliminar", "days": []}, user_id=1)
        
        # Verificar que existe
        routine = get_routine_sync(routine_id)
        assert routine is not None
        
        # Eliminar
        success = delete_routine_sync(routine_id)
        assert success is True
        
        # Verificar que ya no existe
        routine = get_routine_sync(routine_id)
        assert routine is None 
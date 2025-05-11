import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.gemini_service import GeminiRoutineGenerator
from app.models.models import Routine, RoutineRequest

class TestGeminiService:
    """Pruebas para el servicio de Gemini"""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock para el módulo google.generativeai"""
        with patch("app.services.gemini_service.genai") as mock_genai:
            # Configurar el comportamiento del mock
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            # Crear una respuesta simulada de la API
            mock_response = MagicMock()
            mock_response.text = """
            ```json
            {
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
            ```
            """
            
            # Configurar generate_content para devolver la respuesta simulada
            mock_model.generate_content = AsyncMock(return_value=mock_response)
            
            yield mock_genai
    
    @pytest.mark.asyncio
    async def test_create_initial_routine(self, mock_genai):
        """Probar la creación de una rutina inicial"""
        # Configurar GEMINI_CONFIGURED para evitar errores
        with patch("app.services.gemini_service.GEMINI_CONFIGURED", True):
            # Crear instancia del generador de rutinas
            generator = GeminiRoutineGenerator()
            
            # Crear solicitud de rutina
            request = RoutineRequest(
                goals="Hipertrofia",
                equipment="Gimnasio completo",
                days=3,
                user_id=1
            )
            
            # Generar rutina
            routine = await generator.create_initial_routine(request)
            
            # Verificar llamada al modelo
            mock_genai.GenerativeModel.return_value.generate_content.assert_called_once()
            
            # Verificar resultado
            assert isinstance(routine, Routine)
            assert routine.routine_name == "Rutina de prueba"
            assert len(routine.days) == 1
            assert routine.days[0].day_name == "Lunes"
            assert routine.user_id == 1
    
    @pytest.mark.asyncio
    async def test_modify_routine(self, mock_genai):
        """Probar la modificación de una rutina existente"""
        # Configurar GEMINI_CONFIGURED para evitar errores
        with patch("app.services.gemini_service.GEMINI_CONFIGURED", True):
            # Crear instancia del generador de rutinas
            generator = GeminiRoutineGenerator()
            
            # Crear rutina original
            original_routine = Routine(
                id=1,
                user_id=1,
                routine_name="Rutina original",
                days=[]
            )
            
            # Modificar rutina
            modified_routine = await generator.modify_routine(
                original_routine, 
                "Quiero agregar más ejercicios para pecho"
            )
            
            # Verificar llamada al modelo
            mock_genai.GenerativeModel.return_value.generate_content.assert_called_once()
            
            # Verificar resultado
            assert isinstance(modified_routine, Routine)
            assert modified_routine.routine_name == "Rutina de prueba"  # Del mock
            assert modified_routine.id == 1  # Debe mantener el ID original
            assert modified_routine.user_id == 1  # Debe mantener el user_id original
    
    @pytest.mark.asyncio
    async def test_extract_json_from_text(self, mock_genai):
        """Probar la extracción de JSON desde una respuesta de texto"""
        # Configurar GEMINI_CONFIGURED para evitar errores
        with patch("app.services.gemini_service.GEMINI_CONFIGURED", True):
            # Crear instancia del generador de rutinas
            generator = GeminiRoutineGenerator()
            
            # Probar con formato JSON en bloque de código
            text_with_json_block = """
            Aquí tienes la rutina:
            
            ```json
            {
                "routine_name": "Rutina de fuerza",
                "days": []
            }
            ```
            
            Espero que te sea útil.
            """
            
            result = generator._extract_json_from_text(text_with_json_block)
            assert result["routine_name"] == "Rutina de fuerza"
            
            # Probar con JSON simple sin bloques
            simple_json = '{"routine_name": "Rutina simple", "days": []}'
            result = generator._extract_json_from_text(simple_json)
            assert result["routine_name"] == "Rutina simple"
            
            # Probar con JSON inválido
            with pytest.raises(Exception):
                generator._extract_json_from_text("Esto no es JSON") 
import pytest
from unittest.mock import patch, MagicMock
from app.services.gemini_service import GeminiRoutineGenerator
from app.schemas.routines import RoutineRequest
from app.models.models import Routine


class TestGeminiService:
    """Pruebas para el servicio de Gemini"""

    @pytest.fixture
    def generator(self):
        """Create a GeminiRoutineGenerator with mocked Gemini model."""
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

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)

        gen = GeminiRoutineGenerator()
        gen._configured = True
        gen._model = mock_model
        return gen

    @pytest.mark.asyncio
    async def test_create_initial_routine(self, generator):
        """Probar la creación de una rutina inicial"""
        request = RoutineRequest(
            goals="Hipertrofia",
            equipment="Gimnasio completo",
            days=3,
            user_id=1
        )

        routine = await generator.create_initial_routine(request)

        generator._model.generate_content.assert_called_once()

        assert isinstance(routine, Routine)
        assert routine.routine_name == "Rutina de prueba"
        assert len(routine.days) == 1
        assert routine.days[0].day_name == "Lunes"
        assert routine.user_id == 1

    @pytest.mark.asyncio
    async def test_modify_routine(self, generator):
        """Probar la modificación de una rutina existente"""
        original_routine = Routine(
            id=1,
            user_id=1,
            routine_name="Rutina original",
            days=[]
        )

        modified_routine = await generator.modify_routine(
            original_routine,
            "Quiero agregar más ejercicios para pecho"
        )

        generator._model.generate_content.assert_called_once()

        assert isinstance(modified_routine, Routine)
        assert modified_routine.routine_name == "Rutina de prueba"  # Del mock
        assert modified_routine.id == 1  # Debe mantener el ID original
        assert modified_routine.user_id == 1  # Debe mantener el user_id original

    @pytest.mark.asyncio
    async def test_extract_json_from_text(self, generator):
        """Probar la extracción de JSON desde una respuesta de texto"""
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

        # Probar con JSON inválido — ahora retorna {} en vez de lanzar excepción
        result = generator._extract_json_from_text("Esto no es JSON")
        assert result == {}

    @pytest.mark.asyncio
    async def test_create_routine_without_configuration(self):
        """Probar que falla si Gemini no está configurado"""
        generator = GeminiRoutineGenerator()
        # _configured es False por defecto sin API key

        request = RoutineRequest(
            goals="Hipertrofia",
            equipment="Gimnasio completo",
            days=3,
            user_id=1
        )

        with pytest.raises(ValueError, match="not configured"):
            await generator.create_initial_routine(request)

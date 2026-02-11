import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai_service import RoutineGenerator
from app.schemas.routines import RoutineRequest
from app.models.models import Routine


class TestAIService:
    """Pruebas para el servicio de IA (Groq)"""

    @pytest.fixture
    def generator(self):
        """Create a RoutineGenerator with mocked Groq client."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""{
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
                    }"""
                )
            )
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        gen = RoutineGenerator()
        gen._configured = True
        gen._client = mock_client
        gen._model = "llama-3.3-70b-versatile"
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

        generator._client.chat.completions.create.assert_called_once()

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

        generator._client.chat.completions.create.assert_called_once()

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

        # Probar con JSON inválido — retorna {}
        result = generator._extract_json_from_text("Esto no es JSON")
        assert result == {}

    @pytest.mark.asyncio
    async def test_create_routine_without_configuration(self):
        """Probar que falla si la API no está configurada"""
        generator = RoutineGenerator()
        generator._configured = False
        generator._client = None

        request = RoutineRequest(
            goals="Hipertrofia",
            equipment="Gimnasio completo",
            days=3,
            user_id=1
        )

        with pytest.raises(ValueError, match="not configured"):
            await generator.create_initial_routine(request)

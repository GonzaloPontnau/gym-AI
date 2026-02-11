import pytest
from unittest.mock import MagicMock
import base64
import io
from PIL import Image

from app.services.image_analysis_service import GeminiImageAnalyzer


class TestImageAnalysisService:
    """Pruebas para el servicio de análisis de imágenes"""

    @pytest.fixture
    def analyzer(self):
        """Create a GeminiImageAnalyzer with mocked Gemini model."""
        mock_response = MagicMock()
        mock_response.text = """
        La imagen muestra a una persona realizando una sentadilla con buena forma.

        Análisis de postura:
        - Espalda recta
        - Rodillas alineadas con los pies
        - Profundidad adecuada

        Recomendaciones:
        - Mantener esta técnica
        - Asegurar que los talones permanezcan en el suelo
        """

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)

        analyzer = GeminiImageAnalyzer()
        analyzer._configured = True
        analyzer._model = mock_model
        return analyzer

    @pytest.fixture
    def sample_image_base64(self):
        """Generar una imagen de prueba en base64 con formato data URI"""
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        base64_encoded = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_encoded}"

    @pytest.mark.asyncio
    async def test_analyze_exercise_image(self, analyzer, sample_image_base64):
        """Probar el análisis de imagen de ejercicio"""
        result = await analyzer.analyze_exercise_image(
            sample_image_base64,
            "sentadilla",
        )

        analyzer._model.generate_content.assert_called_once()

        assert "buena forma" in result.lower()
        assert "espalda recta" in result.lower()
        assert "recomendaciones" in result.lower()

    @pytest.mark.asyncio
    async def test_analyze_exercise_image_with_invalid_image(self, analyzer):
        """Probar el análisis con imagen inválida — retorna mensaje de error"""
        result = await analyzer.analyze_exercise_image(
            "invalid_base64",
            "sentadilla",
        )

        assert isinstance(result, str)
        assert "no se pudo" in result.lower() or "no es válido" in result.lower()

    @pytest.mark.asyncio
    async def test_analyze_without_gemini_configured(self):
        """Probar comportamiento cuando Gemini no está configurado — retorna mensaje de error"""
        analyzer = GeminiImageAnalyzer()
        # _configured es False por defecto sin API key

        result = await analyzer.analyze_exercise_image(
            "base64_irrelevante",
            "sentadilla",
        )

        assert isinstance(result, str)
        assert "deshabilitada" in result.lower()

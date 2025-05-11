import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import base64
import io
from PIL import Image
import sys
import os

# Ajustar path para importar desde directorio raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importar el servicio
from app.services.image_analysis_service import GeminiImageAnalyzer

class TestImageAnalysisService:
    """Pruebas para el servicio de análisis de imágenes"""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock para el módulo google.generativeai"""
        with patch("app.services.image_analysis_service.genai") as mock_genai:
            # Configurar el comportamiento del mock
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            # Crear una respuesta simulada de la API
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
            
            # Configurar generate_content para devolver la respuesta simulada
            mock_model.generate_content = AsyncMock(return_value=mock_response)
            
            yield mock_genai
    
    @pytest.fixture
    def sample_image_base64(self):
        """Generar una imagen de prueba en base64"""
        # Crear una imagen vacía
        img = Image.new('RGB', (100, 100), color='red')
        
        # Convertir a bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Convertir a base64
        base64_encoded = base64.b64encode(img_byte_arr).decode('utf-8')
        
        return base64_encoded
    
    @pytest.mark.asyncio
    async def test_analyze_exercise_image(self, mock_genai, sample_image_base64):
        """Probar el análisis de imagen de ejercicio"""
        # Configurar GEMINI_CONFIGURED para evitar errores
        with patch("app.services.image_analysis_service.GEMINI_CONFIGURED", True):
            # Crear instancia del analizador
            analyzer = GeminiImageAnalyzer()
            
            # Analizar imagen
            result = await analyzer.analyze_exercise_image(
                sample_image_base64,
                "sentadilla",
                "Verificar si la postura es correcta"
            )
            
            # Verificar llamada al modelo
            mock_genai.GenerativeModel.return_value.generate_content.assert_called_once()
            
            # Verificar resultado
            assert "buena forma" in result.lower()
            assert "espalda recta" in result.lower()
            assert "recomendaciones" in result.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_exercise_image_with_invalid_image(self, mock_genai):
        """Probar el análisis con imagen inválida"""
        # Configurar GEMINI_CONFIGURED para evitar errores
        with patch("app.services.image_analysis_service.GEMINI_CONFIGURED", True):
            # Crear instancia del analizador
            analyzer = GeminiImageAnalyzer()
            
            # Intentar analizar con imagen inválida
            with pytest.raises(ValueError, match="Error al decodificar imagen"):
                await analyzer.analyze_exercise_image(
                    "invalid_base64",
                    "sentadilla",
                    "Verificar si la postura es correcta"
                )
    
    @pytest.mark.asyncio
    async def test_analyze_without_gemini_configured(self):
        """Probar comportamiento cuando Gemini no está configurado"""
        # Configurar GEMINI_CONFIGURED como False
        with patch("app.services.image_analysis_service.GEMINI_CONFIGURED", False):
            # Crear instancia del analizador
            analyzer = GeminiImageAnalyzer()
            
            # Intentar analizar imagen
            with pytest.raises(ValueError, match="API de Gemini no está configurada"):
                await analyzer.analyze_exercise_image(
                    "base64_irrelevante",
                    "sentadilla",
                    "Verificar si la postura es correcta"
                ) 
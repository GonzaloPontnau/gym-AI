"""
Service for analyzing exercise images using the Gemini API.
Shares Gemini configuration with gemini_service via centralized config.
"""

import base64
from io import BytesIO
import asyncio

import google.generativeai as genai

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("services.image_analysis")

# Lazy PIL import
PIL_AVAILABLE = False
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    logger.warning("Pillow not installed — image analysis disabled")


class GeminiImageAnalyzer:
    """Analyzes exercise images and suggests variations via Gemini AI."""

    def __init__(self):
        settings = get_settings()
        self._configured = settings.gemini_configured
        self._max_image_size = settings.max_image_size_bytes

        if self._configured:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
                logger.info("Image analyzer configured with model %s", settings.GEMINI_MODEL)
            except Exception as e:
                logger.error("Failed to configure image analyzer: %s", e)
                self._configured = False
        else:
            self._model = None

    # --- Image Validation ---

    def _validate_and_open_image(self, image_data):
        """
        Validate and open image data from various formats.

        Returns:
            PIL.Image or error string.
        """
        if not PIL_AVAILABLE:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada (Pillow no instalado)."

        if not self._configured:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada (API de Gemini no configurada)."

        try:
            if isinstance(image_data, str) and image_data.startswith("data:image"):
                image_bytes = base64.b64decode(image_data.split(",")[1])
            elif isinstance(image_data, bytes):
                image_bytes = image_data
            else:
                image_bytes = bytes(image_data)

            if len(image_bytes) > self._max_image_size:
                return f"La imagen es demasiado grande. Máximo: {self._max_image_size // (1024*1024)}MB."

            image = Image.open(BytesIO(image_bytes))
            image.verify()
            # Reopen after verify() since it closes the file
            return Image.open(BytesIO(image_bytes))

        except Exception as e:
            logger.error("Image validation failed: %s", e)
            return "No se pudo procesar la imagen. El formato no es válido o está corrupta."

    # --- Public API ---

    async def analyze_exercise_image(self, image_data, exercise_name: str = None) -> str:
        """
        Analyze an exercise image and provide posture/technique feedback.
        """
        result = self._validate_and_open_image(image_data)
        if isinstance(result, str):
            return result  # Error message
        image = result

        if exercise_name:
            prompt = f"""
            Analiza esta imagen donde la persona está realizando el ejercicio: {exercise_name}.

            Por favor, proporciona:
            1. Una evaluación de su postura y técnica
            2. Puntos específicos de mejora
            3. Consejos para mejorar la forma del ejercicio
            4. Posibles riesgos de lesión basados en la técnica mostrada

            Responde en español de forma clara y concisa.
            """
        else:
            prompt = """
            Analiza esta imagen de una persona haciendo ejercicio.

            Por favor:
            1. Identifica qué ejercicio está realizando
            2. Evalúa su postura y técnica
            3. Proporciona consejos específicos para mejorar
            4. Menciona los beneficios del ejercicio y músculos trabajados

            Responde en español de forma clara y concisa.
            """

        try:
            response = await asyncio.to_thread(self._model.generate_content, [prompt, image])
            return response.text.strip()
        except Exception as e:
            logger.error("Image analysis failed: %s", e)
            return "No se pudo analizar la imagen. Por favor, inténtalo de nuevo."

    async def suggest_exercise_variations(self, image_data, difficulty_level: str = None) -> str:
        """
        Analyze an exercise image and suggest variations.
        """
        result = self._validate_and_open_image(image_data)
        if isinstance(result, str):
            return result
        image = result

        if difficulty_level:
            prompt = f"""
            Observa esta imagen de ejercicio y sugiere 3-4 variaciones {difficulty_level} del mismo.

            Para cada variación, incluye:
            - Nombre del ejercicio
            - Breve descripción de cómo realizarlo
            - Músculos principales trabajados
            - Nivel de dificultad comparado con el ejercicio original

            Responde en español de forma clara y concisa.
            """
        else:
            prompt = """
            Observa esta imagen de ejercicio y sugiere 4-5 variaciones alternativas que trabajen los mismos grupos musculares.

            Para cada variación, incluye:
            - Nombre del ejercicio
            - Breve descripción de cómo realizarlo
            - Equipo necesario (si aplica)
            - Si es más fácil o más difícil que el ejercicio mostrado

            Responde en español de forma clara y concisa.
            """

        try:
            response = await asyncio.to_thread(self._model.generate_content, [prompt, image])
            return response.text.strip()
        except Exception as e:
            logger.error("Exercise variation suggestion failed: %s", e)
            return "No se pudieron generar variaciones. Por favor, inténtalo de nuevo."

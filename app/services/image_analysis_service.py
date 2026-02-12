"""
Service for analyzing exercise images using the Groq API with Llama Vision models.
Shares Groq configuration with ai_service via centralized config.
"""

import base64
from io import BytesIO

from typing import Optional

from groq import AsyncGroq

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


class ImageAnalyzer:
    """Analyzes exercise images and suggests variations via Groq AI (Llama Vision)."""

    def __init__(self):
        settings = get_settings()
        self._configured = settings.ai_configured
        self._max_image_size = settings.max_image_size_bytes

        if self._configured:
            try:
                self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                self._model = settings.GROQ_VISION_MODEL
                logger.info("Image analyzer configured with model %s", self._model)
            except Exception as e:
                logger.error("Failed to configure image analyzer: %s", e)
                self._configured = False
                self._client = None
        else:
            self._client = None

    # --- Image Validation ---

    def _validate_and_prepare_image(self, image_data) -> Optional[str]:
        """
        Validate image data and return a base64 data URL ready for the API.

        Returns:
            base64 data URL string or error message string.
        """
        if not PIL_AVAILABLE:
            return None

        if not self._configured:
            return None

        try:
            if isinstance(image_data, str) and image_data.startswith("data:image"):
                # Already a data URL — validate the image bytes
                image_bytes = base64.b64decode(image_data.split(",")[1])
                if len(image_bytes) > self._max_image_size:
                    return None
                # Validate with PIL
                img = Image.open(BytesIO(image_bytes))
                img.verify()
                return image_data  # Return original data URL
            elif isinstance(image_data, bytes):
                image_bytes = image_data
            else:
                image_bytes = bytes(image_data)

            if len(image_bytes) > self._max_image_size:
                return None

            # Validate with PIL
            img = Image.open(BytesIO(image_bytes))
            img.verify()

            # Convert to base64 data URL
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            return f"data:image/jpeg;base64,{b64}"

        except Exception as e:
            logger.error("Image validation failed: %s", e)
            return None

    # --- Public API ---

    async def analyze_exercise_image(self, image_data, exercise_name: str = None) -> str:
        """Analyze an exercise image and provide posture/technique feedback."""
        if not PIL_AVAILABLE:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada (Pillow no instalado)."

        if not self._configured:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada (API de IA no configurada)."

        image_url = self._validate_and_prepare_image(image_data)
        if image_url is None:
            return "No se pudo procesar la imagen. El formato no es válido, está corrupta o es demasiado grande."

        if exercise_name:
            prompt = f"""Analiza esta imagen donde la persona está realizando el ejercicio: {exercise_name}.

Por favor, proporciona:
1. Una evaluación de su postura y técnica
2. Puntos específicos de mejora
3. Consejos para mejorar la forma del ejercicio
4. Posibles riesgos de lesión basados en la técnica mostrada

Responde en español de forma clara y concisa."""
        else:
            prompt = """Analiza esta imagen de una persona haciendo ejercicio.

Por favor:
1. Identifica qué ejercicio está realizando
2. Evalúa su postura y técnica
3. Proporciona consejos específicos para mejorar
4. Menciona los beneficios del ejercicio y músculos trabajados

Responde en español de forma clara y concisa."""

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error("Image analysis failed: %s", e, exc_info=True)
            return f"No se pudo analizar la imagen: {e}"

    async def suggest_exercise_variations(self, image_data, difficulty_level: str = None) -> str:
        """Analyze an exercise image and suggest variations."""
        if not PIL_AVAILABLE:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada (Pillow no instalado)."

        if not self._configured:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada (API de IA no configurada)."

        image_url = self._validate_and_prepare_image(image_data)
        if image_url is None:
            return "No se pudo procesar la imagen. El formato no es válido, está corrupta o es demasiado grande."

        if difficulty_level:
            prompt = f"""Observa esta imagen de ejercicio y sugiere 3-4 variaciones {difficulty_level} del mismo.

Para cada variación, incluye:
- Nombre del ejercicio
- Breve descripción de cómo realizarlo
- Músculos principales trabajados
- Nivel de dificultad comparado con el ejercicio original

Responde en español de forma clara y concisa."""
        else:
            prompt = """Observa esta imagen de ejercicio y sugiere 4-5 variaciones alternativas que trabajen los mismos grupos musculares.

Para cada variación, incluye:
- Nombre del ejercicio
- Breve descripción de cómo realizarlo
- Equipo necesario (si aplica)
- Si es más fácil o más difícil que el ejercicio mostrado

Responde en español de forma clara y concisa."""

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error("Exercise variation suggestion failed: %s", e, exc_info=True)
            return f"No se pudieron generar variaciones: {e}"

"""
Service for generating and modifying workout routines using the Groq API
with Llama models. Follows dependency injection — receives configuration, not global state.
"""

import json
import re

from groq import AsyncGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.models import Routine
from app.schemas.routines import RoutineRequest

logger = get_logger("services.ai")


class RoutineGenerator:
    """Generates and modifies workout routines via Groq AI (Llama models)."""

    def __init__(self):
        settings = get_settings()
        self._configured = settings.ai_configured

        if self._configured:
            try:
                self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                self._model = settings.GROQ_MODEL
                logger.info("Groq API configured with model %s", self._model)
            except Exception as e:
                logger.error("Failed to configure Groq API: %s", e)
                self._configured = False
                self._client = None
        else:
            self._client = None
            logger.warning("GROQ_API_KEY not set — AI service unavailable")

    @property
    def is_configured(self) -> bool:
        return self._configured

    # --- Prompt Builders ---

    @staticmethod
    def _build_initial_prompt(request: RoutineRequest) -> str:
        return f"""Actúa como un entrenador personal profesional y crea una rutina de entrenamiento detallada con estas características:

Objetivos: {request.goals}
Días de entrenamiento: {request.days} días a la semana
Nivel de experiencia: {request.experience_level or 'No especificado'}
Equipo disponible: {request.available_equipment or 'No especificado'}
Tiempo por sesión: {request.time_per_session or 'No especificado'}
Condiciones de salud: {request.health_conditions or 'Ninguna'}

La rutina debe seguir ESTRICTAMENTE este formato JSON:

{{
    "routine_name": "Nombre descriptivo de la rutina",
    "days": [
        {{
            "day_name": "Lunes",
            "focus": "Parte del cuerpo que se trabaja ese día",
            "exercises": [
                {{
                    "name": "Nombre del ejercicio",
                    "sets": 3,
                    "reps": "8-12",
                    "rest": "60-90 seg",
                    "equipment": "Equipamiento necesario"
                }}
            ]
        }}
    ]
}}

IMPORTANTE:
1. Devuelve SOLO el JSON válido, sin texto explicativo.
2. Incluye exactamente {request.days} días en la rutina.
3. Cada día debe tener entre 4 y 6 ejercicios.
4. Los nombres de los días deben ser en español (Lunes, Martes, etc.)."""

    @staticmethod
    def _build_modification_prompt(current_routine: Routine, user_request: str) -> str:
        routine_json = current_routine.model_dump_json()
        return f"""Actúa como un entrenador personal. El usuario tiene la siguiente rutina de entrenamiento:

```json
{routine_json}
```

El usuario ha solicitado: "{user_request}"

Modifica la rutina según esta solicitud y devuelve SOLO el JSON actualizado con el mismo formato.
No incluyas campos como "id", "user_id", "created_at" o "updated_at" en la respuesta."""

    # --- JSON Extraction ---

    @staticmethod
    def _extract_json_from_text(text: str) -> dict:
        """Extract JSON content from a potentially wrapped text response."""
        try:
            # First try direct JSON parse
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        try:
            # Try extracting from markdown code blocks
            json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
            json_matches = re.findall(json_pattern, text)
            if json_matches:
                return json.loads(json_matches[0].strip())
        except Exception as e:
            logger.error("JSON extraction from code block failed: %s", e)

        # Last resort: find first { to last }
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except Exception as e:
            logger.error("JSON extraction failed: %s — text: %s", e, text[:200])
            return {}

    # --- Public API ---

    def _ensure_configured(self):
        if not self._configured:
            raise ValueError("Groq API is not configured. Cannot process AI requests.")

    async def create_initial_routine(self, request: RoutineRequest) -> Routine:
        """Generate an initial routine from a user request."""
        self._ensure_configured()
        prompt = self._build_initial_prompt(request)

        try:
            logger.info("Sending initial routine request to Groq (%s)...", self._model)
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un entrenador personal profesional. Responde ÚNICAMENTE con JSON válido, sin texto adicional."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            raw_text = response.choices[0].message.content
            routine_dict = self._extract_json_from_text(raw_text)
            if not routine_dict:
                raise ValueError("Could not extract valid JSON from AI response")

            routine_dict["user_id"] = request.user_id
            routine = Routine.model_validate(routine_dict)
            logger.info("Routine generated: %s", routine.routine_name)
            return routine

        except Exception as e:
            logger.error("Failed to create routine: %s", e, exc_info=True)
            raise ValueError(f"Error generating routine: {e}")

    async def modify_routine(self, current_routine: Routine, user_request: str) -> Routine:
        """Modify an existing routine based on user instructions."""
        self._ensure_configured()
        prompt = self._build_modification_prompt(current_routine, user_request)

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un entrenador personal profesional. Responde ÚNICAMENTE con JSON válido, sin texto adicional."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            raw_text = response.choices[0].message.content
            routine_dict = self._extract_json_from_text(raw_text)

            if not routine_dict:
                raise ValueError("Could not extract valid JSON")

            routine_dict["id"] = current_routine.id
            routine_dict["user_id"] = current_routine.user_id
            return Routine.model_validate(routine_dict)

        except Exception as e:
            logger.error("Failed to modify routine: %s", e)
            raise ValueError(f"Error modifying routine: {e}")

    async def explain_routine_changes(
        self, old_routine: Routine, new_routine: Routine, user_request: str
    ) -> str:
        """Generate a natural-language explanation of the changes made."""
        self._ensure_configured()

        prompt = f"""El usuario solicitó: "{user_request}"

Explica brevemente los cambios realizados a la rutina de forma profesional y motivadora.
No incluyas código JSON, solo texto explicando los cambios principales."""

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un entrenador personal profesional y motivador. Responde en español de forma clara y concisa."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error("Failed to generate explanation: %s", e)
            raise ValueError(f"Error generating explanation: {e}")

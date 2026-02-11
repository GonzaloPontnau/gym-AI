"""
FastAPI dependency injection providers.
Central place for all Depends() callables.
"""

from functools import lru_cache

from app.services.gemini_service import GeminiRoutineGenerator
from app.services.image_analysis_service import GeminiImageAnalyzer


@lru_cache
def get_routine_generator() -> GeminiRoutineGenerator:
    """Singleton routine generator."""
    return GeminiRoutineGenerator()


@lru_cache
def get_image_analyzer() -> GeminiImageAnalyzer:
    """Singleton image analyzer."""
    return GeminiImageAnalyzer()

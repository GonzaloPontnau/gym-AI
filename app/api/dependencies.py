"""
FastAPI dependency injection providers.
Central place for all Depends() callables.
"""

from functools import lru_cache

from app.services.ai_service import RoutineGenerator
from app.services.image_analysis_service import ImageAnalyzer


@lru_cache
def get_routine_generator() -> RoutineGenerator:
    """Singleton routine generator."""
    return RoutineGenerator()


@lru_cache
def get_image_analyzer() -> ImageAnalyzer:
    """Singleton image analyzer."""
    return ImageAnalyzer()

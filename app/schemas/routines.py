"""
API request/response schemas for routine endpoints.
Separated from domain models to follow clean architecture.
"""

from typing import Optional

from pydantic import BaseModel, Field


class RoutineRequest(BaseModel):
    """Schema for creating a new routine via the API."""

    goals: str
    equipment: str = ""
    days: Optional[int] = Field(default=None, ge=1, le=7)
    experience_level: str = ""
    available_equipment: str = ""
    time_per_session: str = ""
    health_conditions: str = ""
    user_id: int = 1


class ModifyRoutineRequest(BaseModel):
    """Schema for modifying an existing routine via the HTTP fallback API."""

    message: str

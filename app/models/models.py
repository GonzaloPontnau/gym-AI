"""
Domain models for GymAI.
These represent the core business entities, independent of API or DB concerns.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Exercise(BaseModel):
    """A single exercise within a training day."""

    name: str
    sets: int
    reps: str
    rest: str
    equipment: str


class Day(BaseModel):
    """A training day consisting of a focus area and exercises."""

    day_name: str
    focus: str
    exercises: List[Exercise]


class Routine(BaseModel):
    """A complete workout routine spanning multiple training days."""

    id: Optional[int] = None
    user_id: int = 1
    routine_name: str
    days: List[Day]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    """A single message in a routine's chat history."""

    routine_id: int
    sender: str  # "user" | "assistant"
    content: str
    timestamp: Optional[datetime] = None

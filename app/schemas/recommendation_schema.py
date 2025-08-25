# app/schemas/recommendation_schema.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    budget_level: Optional[int] = Field(None, ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)

class Context(BaseModel):
    lat: float
    lng: float
    category: str
    radius_m: int = 1500
    when: str = "now"
    party: str = "solo"
    intent: str = "casual"
    open_now: bool = True

class RecommendRequest(BaseModel):
    user_profile: UserProfile
    context: Context

class RecItem(BaseModel):
    id: str
    name: str
    address: str = ""
    reason: str
    eta_min: int
    expected_stay_min: int
    crowd: str
    link: Optional[str] = ""

class MissionItem(BaseModel):
    title: str
    steps: List[str]
    reward_hint: Optional[str] = ""

class RecommendationPayload(BaseModel):
    summary: str
    recommendations: List[RecItem]
    missions: List[MissionItem]
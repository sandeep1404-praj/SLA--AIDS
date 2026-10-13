from pydantic import BaseModel
from typing import Optional, List
from datetime import date


PLATFORM_OPTIONS = ["linkedin", "x", "instagram", "facebook", "short_video"]
TONE_OPTIONS = ["professional", "conversational", "educational", "informative", "persuasive", "storytelling", "inspirational", "humorous"]
OBJECTIVE_OPTIONS = ["education", "brand_awareness", "audience_engagement", "lead_generation", "thought_leadership", "community_building"]


class CalendarGenerateRequest(BaseModel):
    article_id: str
    title: str
    target_audience: str
    industry: str
    content_objective: str
    tone: str
    start_date: str  # ISO date string YYYY-MM-DD
    platforms: List[str]

    class Config:
        str_strip_whitespace = True


class CalendarUpdate(BaseModel):
    title: Optional[str] = None
    tone: Optional[str] = None
    content_objective: Optional[str] = None


class CalendarResponse(BaseModel):
    id: str
    user_id: str
    article_id: str
    title: str
    start_date: str
    duration_days: int
    selected_platforms: List[str]
    target_audience: str
    tone: str
    content_objective: str
    generation_status: str
    weekly_plan: Optional[List[dict]]
    created_at: str
    updated_at: str

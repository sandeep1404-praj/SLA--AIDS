from pydantic import BaseModel
from typing import Optional, List


class Theme(BaseModel):
    theme: str
    description: str
    supporting_points: List[str] = []


class ArticleAnalysis(BaseModel):
    main_thesis: str
    summary: str
    themes: List[Theme] = []
    facts: List[str] = []
    statistics: List[str] = []
    quotations: List[str] = []
    practical_takeaways: List[str] = []
    examples: List[str] = []
    limitations: List[str] = []
    potential_ctas: List[str] = []


class DayPlan(BaseModel):
    day_number: int
    theme: str
    objective: str
    content_angle: str
    audience_intent: str
    assigned_points: List[str] = []
    suggested_cta: str
    platforms: List[str] = []


class WeeklyPlan(BaseModel):
    days: List[DayPlan]
    overall_narrative: str


class GeneratedPost(BaseModel):
    platform: str
    day_number: int
    content_angle: str
    title: Optional[str] = None
    post_text: str
    hashtags: List[str] = []
    call_to_action: Optional[str] = None
    visual_suggestion: Optional[str] = None
    assigned_source_themes: List[str] = []
    thread_posts: Optional[List[str]] = None  # for X threads


class VerificationResult(BaseModel):
    supported_claims: List[str] = []
    unsupported_claims: List[str] = []
    warnings: List[str] = []
    overall_grounded: bool = True

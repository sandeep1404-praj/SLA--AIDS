from pydantic import BaseModel
from typing import Optional, List


class PostUpdate(BaseModel):
    post_text: Optional[str] = None
    title: Optional[str] = None
    hashtags: Optional[List[str]] = None
    call_to_action: Optional[str] = None
    visual_suggestion: Optional[str] = None
    status: Optional[str] = None


class PostResponse(BaseModel):
    id: str
    calendar_id: str
    user_id: str
    day_number: int
    platform: str
    title: Optional[str]
    post_text: str
    hashtags: List[str]
    call_to_action: Optional[str]
    visual_suggestion: Optional[str]
    content_angle: Optional[str]
    assigned_source_themes: List[str]
    word_count: int
    character_count: int
    validation_status: str
    validation_warnings: List[str]
    status: str
    created_at: str
    updated_at: str


class PostVersionResponse(BaseModel):
    id: str
    post_id: str
    version_number: int
    change_type: str
    previous_content: dict
    created_at: str

from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class ArticleCreate(BaseModel):
    title: str
    article_text: str
    source_url: Optional[str] = None
    language: str = "English"

    class Config:
        str_strip_whitespace = True


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    source_url: Optional[str] = None
    language: Optional[str] = None


class ArticleResponse(BaseModel):
    id: str
    user_id: str
    title: str
    source_url: Optional[str]
    article_text: str
    language: str
    extracted_analysis: Optional[dict]
    created_at: str
    updated_at: str

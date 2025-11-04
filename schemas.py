"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class SuggestionItem(BaseModel):
    title: str
    source: Literal["youtube", "radio"]
    # For YouTube, store the videoId; for radio, store the stream URL
    id: Optional[str] = None
    stream_url: Optional[str] = None
    thumbnail: Optional[str] = None
    meta: Optional[dict] = None

class Recommendation(BaseModel):
    mood: str = Field(..., description="User mood like happy, sad, chill, focus")
    message: Optional[str] = Field(None, description="Original user message to the assistant")
    suggestions: List[SuggestionItem] = Field(default_factory=list)

# You can add more schemas as needed for playlists, favorites, etc.

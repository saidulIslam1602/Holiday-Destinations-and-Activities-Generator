"""
Data models and schemas for the Holiday Destinations Generator.
All models use Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ThemeType(str, Enum):
    """Available destination themes."""
    SPORTS = "Sports"
    SCIENTIFIC = "Scientific"
    NATURAL_ATTRACTION = "Natural Attraction"
    HISTORICAL_PLACE = "Historical Place"
    ENTERTAINMENT = "Entertainment"


class ActivityType(str, Enum):
    """Types of activities."""
    OUTDOOR = "Outdoor"
    INDOOR = "Indoor"
    CULTURAL = "Cultural"
    ADVENTURE = "Adventure"
    RELAXATION = "Relaxation"
    EDUCATIONAL = "Educational"


class Activity(BaseModel):
    """Model for a single activity."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    activity_type: Optional[ActivityType] = None
    duration_hours: Optional[float] = Field(None, ge=0, le=168)  # Max 1 week
    cost_estimate: Optional[str] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class Destination(BaseModel):
    """Model for a travel destination."""
    id: UUID = Field(default_factory=uuid4)
    place: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    continent: Optional[str] = Field(None, max_length=50)
    coordinates: Optional[Dict[str, float]] = None  # {"lat": float, "lng": float}
    description: Optional[str] = Field(None, max_length=2000)
    best_time_to_visit: Optional[str] = Field(None, max_length=200)
    activities: List[Activity] = Field(default_factory=list)
    theme: ThemeType
    rating: Optional[float] = Field(None, ge=0, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator("coordinates")
    def validate_coordinates(cls, v):
        if v is not None:
            if not isinstance(v, dict) or "lat" not in v or "lng" not in v:
                raise ValueError("Coordinates must be a dict with 'lat' and 'lng' keys")
            if not (-90 <= v["lat"] <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= v["lng"] <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v

    @property
    def full_name(self) -> str:
        """Return the full destination name."""
        return f"{self.place}, {self.country}"

    class Config:
        use_enum_values = True


class GenerationRequest(BaseModel):
    """Request model for destination generation."""
    theme: ThemeType
    count: int = Field(default=5, ge=1, le=20)
    include_activities: bool = Field(default=True)
    user_preferences: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class GenerationResponse(BaseModel):
    """Response model for destination generation."""
    request_id: UUID = Field(default_factory=uuid4)
    destinations: List[Destination]
    theme: ThemeType
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_time_seconds: Optional[float] = None
    
    class Config:
        use_enum_values = True


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default_factory=dict)


class CacheInfo(BaseModel):
    """Cache information model."""
    cache_key: str
    hit: bool
    ttl_seconds: Optional[int] = None
    size_bytes: Optional[int] = None 